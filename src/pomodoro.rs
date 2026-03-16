use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum PomodoroState {
    Idle,
    Working,
    ShortBreak,
    LongBreak,
    WaitingConfirmation,
}

impl PomodoroState {
    pub fn label(&self) -> &str {
        match self {
            Self::Idle => "Inativo",
            Self::Working => "Trabalho",
            Self::ShortBreak => "Pausa Curta",
            Self::LongBreak => "Pausa Longa",
            Self::WaitingConfirmation => "Aguardando",
        }
    }
}

pub struct PomodoroManager {
    pub state: PomodoroState,
    pub seconds_remaining: i32,
    pub cycles_completed: i32,

    work_duration: i32,     // minutos
    short_break: i32,       // minutos
    long_break: i32,        // minutos
    cycles_before_long: i32,

    reminder_counter: i32,  // conta segundos para reminder de 30s
    was_working: bool,      // para saber se veio de work ou break
}

impl PomodoroManager {
    pub fn new() -> Self {
        Self {
            state: PomodoroState::Idle,
            seconds_remaining: 0,
            cycles_completed: 0,
            work_duration: 25,
            short_break: 5,
            long_break: 15,
            cycles_before_long: 4,
            reminder_counter: 0,
            was_working: false,
        }
    }

    pub fn configure(
        &mut self,
        work: i32,
        short_break: i32,
        long_break: i32,
        cycles_before_long: i32,
    ) {
        self.work_duration = work;
        self.short_break = short_break;
        self.long_break = long_break;
        self.cycles_before_long = cycles_before_long;
    }

    pub fn is_active(&self) -> bool {
        self.state != PomodoroState::Idle
    }

    pub fn start(&mut self) {
        self.state = PomodoroState::Working;
        self.seconds_remaining = self.work_duration * 60;
        self.cycles_completed = 0;
        self.was_working = true;
    }

    pub fn stop(&mut self) {
        self.state = PomodoroState::Idle;
        self.seconds_remaining = 0;
    }

    /// Chamado a cada segundo. Retorna eventos que ocorreram.
    pub fn tick(&mut self) -> Vec<PomodoroEvent> {
        let mut events = Vec::new();

        match self.state {
            PomodoroState::Working | PomodoroState::ShortBreak | PomodoroState::LongBreak => {
                self.seconds_remaining -= 1;
                if self.seconds_remaining <= 0 {
                    match self.state {
                        PomodoroState::Working => {
                            self.cycles_completed += 1;
                            self.was_working = true;
                            self.state = PomodoroState::WaitingConfirmation;
                            self.reminder_counter = 0;
                            let msg = format!(
                                "Ciclo {} completo! Inicie a pausa ou encerre o Pomodoro.",
                                self.cycles_completed
                            );
                            events.push(PomodoroEvent::CycleCompleted(self.cycles_completed));
                            events.push(PomodoroEvent::ConfirmationNeeded(msg));
                        }
                        PomodoroState::ShortBreak | PomodoroState::LongBreak => {
                            self.was_working = false;
                            self.state = PomodoroState::WaitingConfirmation;
                            self.reminder_counter = 0;
                            let msg = format!(
                                "Pausa finalizada! Ciclo {} de {}. Inicie o próximo período ou encerre.",
                                self.cycles_completed, self.cycles_before_long
                            );
                            events.push(PomodoroEvent::BreakEnded);
                            events.push(PomodoroEvent::ConfirmationNeeded(msg));
                        }
                        _ => {}
                    }
                    events.push(PomodoroEvent::StateChanged(self.state));
                }
            }
            PomodoroState::WaitingConfirmation => {
                self.reminder_counter += 1;
                if self.reminder_counter >= 30 {
                    self.reminder_counter = 0;
                    events.push(PomodoroEvent::Reminder);
                }
            }
            PomodoroState::Idle => {}
        }

        events
    }

    /// Confirma o próximo ciclo (chamado pelo usuário).
    pub fn confirm_next_cycle(&mut self) -> Vec<PomodoroEvent> {
        let mut events = Vec::new();
        if self.state != PomodoroState::WaitingConfirmation {
            return events;
        }

        if self.was_working {
            // Decide entre pausa curta ou longa
            let is_long = self.cycles_completed > 0
                && self.cycles_completed % self.cycles_before_long == 0;
            if is_long {
                self.state = PomodoroState::LongBreak;
                self.seconds_remaining = self.long_break * 60;
            } else {
                self.state = PomodoroState::ShortBreak;
                self.seconds_remaining = self.short_break * 60;
            }
            events.push(PomodoroEvent::BreakStarted);
        } else {
            // Volta ao trabalho
            self.state = PomodoroState::Working;
            self.seconds_remaining = self.work_duration * 60;
        }

        events.push(PomodoroEvent::StateChanged(self.state));
        events
    }

    pub fn status_text(&self) -> String {
        match self.state {
            PomodoroState::Idle => "Pomodoro inativo".into(),
            PomodoroState::WaitingConfirmation => {
                format!("Aguardando confirmação (ciclo {})", self.cycles_completed)
            }
            _ => {
                let m = self.seconds_remaining / 60;
                let s = self.seconds_remaining % 60;
                format!("{} - {:02}:{:02}", self.state.label(), m, s)
            }
        }
    }
}

#[derive(Debug, Clone)]
pub enum PomodoroEvent {
    StateChanged(PomodoroState),
    CycleCompleted(i32),
    ConfirmationNeeded(String),
    BreakStarted,
    BreakEnded,
    Reminder,
}
