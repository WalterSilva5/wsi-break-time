use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

use chrono::Local;
use crossbeam_channel::{Receiver, Sender};
use rand::Rng;

use crate::event::{AppCommand, AppEvent};
use crate::pomodoro::{PomodoroEvent, PomodoroManager};
use crate::settings::AppSettings;
use crate::todo::manager::TodoManager;

pub fn spawn_timer_thread(
    event_tx: Sender<AppEvent>,
    cmd_rx: Receiver<AppCommand>,
    settings: Arc<Mutex<AppSettings>>,
    todo_manager: Arc<Mutex<TodoManager>>,
) -> thread::JoinHandle<()> {
    thread::spawn(move || {
        timer_loop(event_tx, cmd_rx, settings, todo_manager);
    })
}

fn timer_loop(
    event_tx: Sender<AppEvent>,
    cmd_rx: Receiver<AppCommand>,
    settings: Arc<Mutex<AppSettings>>,
    todo_manager: Arc<Mutex<TodoManager>>,
) {
    let mut is_running = false;
    let mut is_paused = false;
    let mut is_on_break = false;
    let mut break_seconds_remaining: i32 = 0;
    let mut next_break_time: Option<Instant> = None;
    let mut breaks_taken: i32 = 0;
    let mut last_water_time: Option<Instant> = None;
    let mut pre_notified = false;

    let mut pomodoro = PomodoroManager::new();
    let mut last_todo_check = Instant::now();
    let mut last_midnight_check = Local::now().date_naive();

    let mut last_tick = Instant::now();

    loop {
        // Processa comandos (non-blocking)
        while let Ok(cmd) = cmd_rx.try_recv() {
            let s = settings.lock().unwrap().clone();
            match cmd {
                AppCommand::Start => {
                    is_running = true;
                    is_paused = false;
                    is_on_break = false;
                    breaks_taken = 0;
                    schedule_next_break(&mut next_break_time, &s);
                    pre_notified = false;
                    last_water_time = if s.water_reminder_interval > 0 {
                        Some(Instant::now())
                    } else {
                        None
                    };
                }
                AppCommand::Stop => {
                    is_running = false;
                    is_paused = false;
                    is_on_break = false;
                    next_break_time = None;
                }
                AppCommand::Pause => {
                    is_paused = true;
                }
                AppCommand::Resume => {
                    is_paused = false;
                    schedule_next_break(&mut next_break_time, &s);
                    pre_notified = false;
                }
                AppCommand::SkipBreak => {
                    if is_on_break {
                        is_on_break = false;
                        breaks_taken += 1;
                        let _ = event_tx.send(AppEvent::BreakEnded);
                        if is_running {
                            schedule_next_break(&mut next_break_time, &s);
                            pre_notified = false;
                        }
                    }
                }
                AppCommand::PostponeBreak(minutes) => {
                    if is_on_break {
                        is_on_break = false;
                        breaks_taken += 1;
                        let _ = event_tx.send(AppEvent::BreakEnded);
                    }
                    next_break_time =
                        Some(Instant::now() + Duration::from_secs(minutes as u64 * 60));
                    pre_notified = false;
                }
                AppCommand::TakeBreakNow => {
                    if !is_on_break && is_running {
                        next_break_time = Some(Instant::now());
                    }
                }
                AppCommand::SettingsChanged => {
                    let new_s = settings.lock().unwrap().clone();
                    pomodoro.configure(
                        new_s.pomodoro_work_duration,
                        new_s.pomodoro_short_break,
                        new_s.pomodoro_long_break,
                        new_s.pomodoro_cycles_before_long,
                    );
                    if is_running && !is_paused && !is_on_break {
                        schedule_next_break(&mut next_break_time, &new_s);
                        pre_notified = false;
                    }
                    last_water_time = if new_s.water_reminder_interval > 0 {
                        Some(Instant::now())
                    } else {
                        None
                    };
                }
                AppCommand::StartPomodoro => {
                    if !pomodoro.is_active() {
                        is_paused = true;
                        pomodoro.start();
                        let _ = event_tx.send(AppEvent::PomodoroStateChanged(
                            pomodoro.status_text(),
                        ));
                    }
                }
                AppCommand::StopPomodoro => {
                    pomodoro.stop();
                    is_paused = false;
                    let _ = event_tx.send(AppEvent::PomodoroStateChanged(
                        pomodoro.status_text(),
                    ));
                    if is_running {
                        let s = settings.lock().unwrap().clone();
                        schedule_next_break(&mut next_break_time, &s);
                        pre_notified = false;
                    }
                }
                AppCommand::ConfirmPomodoroCycle => {
                    let events = pomodoro.confirm_next_cycle();
                    process_pomodoro_events(&events, &event_tx, &pomodoro);
                }
                AppCommand::RequestTodoCompletion(todo_id) => {
                    let mut tm = todo_manager.lock().unwrap();
                    if let Some(code) = tm.request_completion(&todo_id) {
                        let title = tm
                            .todos
                            .iter()
                            .find(|t| t.id == todo_id)
                            .map(|t| t.title.clone())
                            .unwrap_or_default();
                        let _ = event_tx.send(AppEvent::TodoVerificationRequired(
                            todo_id, title, code,
                        ));
                    }
                }
                AppCommand::VerifyTodoCompletion(todo_id, code) => {
                    let mut tm = todo_manager.lock().unwrap();
                    tm.verify_and_complete(&todo_id, &code);
                }
            }
        }

        // Sleep 100ms entre iterações
        thread::sleep(Duration::from_millis(100));

        // Tick a cada ~1 segundo
        if last_tick.elapsed() < Duration::from_secs(1) {
            continue;
        }
        last_tick = Instant::now();

        let s = settings.lock().unwrap().clone();

        // Pomodoro tick
        if pomodoro.is_active() {
            let events = pomodoro.tick();
            process_pomodoro_events(&events, &event_tx, &pomodoro);
            let _ = event_tx.send(AppEvent::PomodoroTick(pomodoro.seconds_remaining));
        }

        // TODO check a cada 60 segundos
        if last_todo_check.elapsed() >= Duration::from_secs(60) {
            last_todo_check = Instant::now();
            let mut tm = todo_manager.lock().unwrap();
            let notifs = tm.check_todos();
            for (title, time) in notifs {
                let _ = event_tx.send(AppEvent::TodoDue(title, time));
            }
        }

        // Midnight reset check
        let today = Local::now().date_naive();
        if today != last_midnight_check {
            last_midnight_check = today;
            let mut tm = todo_manager.lock().unwrap();
            tm.reset_daily();
        }

        if !is_running || is_paused {
            continue;
        }

        // Durante pausa ativa
        if is_on_break {
            break_seconds_remaining -= 1;
            let _ = event_tx.send(AppEvent::BreakTick(break_seconds_remaining));
            if break_seconds_remaining <= 0 {
                is_on_break = false;
                breaks_taken += 1;
                let _ = event_tx.send(AppEvent::BreakEnded);
                schedule_next_break(&mut next_break_time, &s);
                pre_notified = false;
            }
            continue;
        }

        // Contagem para próxima pausa
        if let Some(nbt) = next_break_time {
            let remaining = nbt.saturating_duration_since(Instant::now());
            let total_seconds = remaining.as_secs() as i64;

            if total_seconds <= 0 {
                // Hora da pausa!
                is_on_break = true;
                break_seconds_remaining = s.break_duration;
                let message = get_random_message(&s);
                let _ = event_tx.send(AppEvent::BreakStarted(message));
            } else {
                let _ = event_tx.send(AppEvent::Tick(total_seconds));

                // Pré-notificação
                if s.show_pre_notification
                    && !pre_notified
                    && total_seconds <= s.pre_notification_seconds as i64
                {
                    pre_notified = true;
                    let _ = event_tx.send(AppEvent::PreNotification(
                        s.pre_notification_seconds,
                    ));
                }
            }
        }

        // Lembrete de água
        if s.water_reminder_interval > 0 {
            if let Some(last) = last_water_time {
                if last.elapsed()
                    >= Duration::from_secs(s.water_reminder_interval as u64 * 60)
                {
                    last_water_time = Some(Instant::now());
                    let _ = event_tx.send(AppEvent::WaterReminder);
                }
            }
        }
    }
}

fn schedule_next_break(next: &mut Option<Instant>, s: &AppSettings) {
    *next = Some(Instant::now() + Duration::from_secs(s.break_interval as u64 * 60));
}

fn get_random_message(s: &AppSettings) -> String {
    if s.break_messages.is_empty() {
        return "Hora de descansar!".into();
    }
    let idx = rand::thread_rng().gen_range(0..s.break_messages.len());
    s.break_messages[idx].clone()
}

fn process_pomodoro_events(
    events: &[PomodoroEvent],
    tx: &Sender<AppEvent>,
    pomodoro: &PomodoroManager,
) {
    for event in events {
        match event {
            PomodoroEvent::StateChanged(_) => {
                let _ = tx.send(AppEvent::PomodoroStateChanged(pomodoro.status_text()));
            }
            PomodoroEvent::ConfirmationNeeded(msg) => {
                let _ = tx.send(AppEvent::PomodoroConfirmationNeeded(msg.clone()));
            }
            PomodoroEvent::Reminder => {
                let _ = tx.send(AppEvent::PomodoroReminder);
            }
            _ => {}
        }
    }
}
