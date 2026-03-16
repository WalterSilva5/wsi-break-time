use std::sync::{Arc, Mutex};
use std::time::Duration;

use crossbeam_channel::{Receiver, Sender};
use tray_icon::menu::MenuEvent;

use crate::event::{AppCommand, AppEvent};
use crate::notifications;
use crate::settings::{AppSettings, SettingsManager};
use crate::todo::manager::TodoManager;
use crate::tray::{self, AppTray};

#[derive(PartialEq)]
enum WindowMode {
    Hidden,
    Overlay,
    Settings,
}

pub struct App {
    event_rx: Receiver<AppEvent>,
    cmd_tx: Sender<AppCommand>,
    settings_manager: SettingsManager,
    settings: Arc<Mutex<AppSettings>>,
    todo_manager: Arc<Mutex<TodoManager>>,

    tray: AppTray,

    // Estado
    mode: WindowMode,
    is_running: bool,
    is_paused: bool,
    is_on_break: bool,
    break_message: String,
    break_seconds_remaining: i32,
    seconds_until_break: i64,
    breaks_taken: i32,

    // Pomodoro
    pomodoro_active: bool,
    pomodoro_waiting: bool,
    pomodoro_status: String,
    pomodoro_seconds: i32,

    // Settings UI state
    settings_draft: AppSettings,
    settings_tab: usize,
    new_message: String,
    selected_message: Option<usize>,

    // Verificação TODO
    verification_dialog: Option<VerificationDialog>,

    // Flag para inicialização
    initialized: bool,
}

struct VerificationDialog {
    todo_id: String,
    title: String,
    code: String,
    entered: String,
    error: bool,
}

impl App {
    pub fn new(
        event_rx: Receiver<AppEvent>,
        cmd_tx: Sender<AppCommand>,
        settings_manager: SettingsManager,
        settings: Arc<Mutex<AppSettings>>,
        todo_manager: Arc<Mutex<TodoManager>>,
        tray: AppTray,
    ) -> Self {
        let s = settings.lock().unwrap().clone();
        Self {
            event_rx,
            cmd_tx,
            settings_manager,
            settings,
            todo_manager,
            tray,
            mode: WindowMode::Hidden,
            is_running: false,
            is_paused: false,
            is_on_break: false,
            break_message: String::new(),
            break_seconds_remaining: 0,
            seconds_until_break: 0,
            breaks_taken: 0,
            pomodoro_active: false,
            pomodoro_waiting: false,
            pomodoro_status: String::new(),
            pomodoro_seconds: 0,
            settings_draft: s,
            settings_tab: 0,
            new_message: String::new(),
            selected_message: None,
            verification_dialog: None,
            initialized: false,
        }
    }

    fn process_events(&mut self) {
        while let Ok(event) = self.event_rx.try_recv() {
            let volume = self.settings.lock().unwrap().notification_volume;
            match event {
                AppEvent::Tick(secs) => {
                    self.seconds_until_break = secs;
                    let m = secs / 60;
                    let s = secs % 60;
                    self.tray
                        .ids
                        .status
                        .set_text(format!("Próxima pausa em {:02}:{:02}", m, s));
                }
                AppEvent::BreakStarted(msg) => {
                    self.is_on_break = true;
                    self.break_message = msg;
                    self.break_seconds_remaining =
                        self.settings.lock().unwrap().break_duration;
                    self.mode = WindowMode::Overlay;
                    notifications::notify("Pausa para os olhos", &self.break_message, volume);
                    self.tray
                        .ids
                        .status
                        .set_text("Em pausa...");
                }
                AppEvent::BreakTick(secs) => {
                    self.break_seconds_remaining = secs;
                }
                AppEvent::BreakEnded => {
                    self.is_on_break = false;
                    if self.mode == WindowMode::Overlay {
                        self.mode = WindowMode::Hidden;
                    }
                    self.tray.ids.status.set_text("Timer ativo");
                }
                AppEvent::PreNotification(secs) => {
                    notifications::notify(
                        "Pausa em breve",
                        &format!("Sua pausa começará em {} segundos.", secs),
                        volume,
                    );
                }
                AppEvent::WaterReminder => {
                    notifications::notify(
                        "Hora de hidratar!",
                        "Beba um copo de água para manter-se hidratado.",
                        volume,
                    );
                }
                AppEvent::PomodoroTick(secs) => {
                    self.pomodoro_seconds = secs;
                }
                AppEvent::PomodoroStateChanged(status) => {
                    self.pomodoro_status = status.clone();
                    self.pomodoro_active = !status.contains("inativo");
                    self.pomodoro_waiting = status.contains("Aguardando");
                }
                AppEvent::PomodoroConfirmationNeeded(msg) => {
                    self.pomodoro_waiting = true;
                    notifications::notify("Pomodoro - Ação Necessária", &msg, volume);
                }
                AppEvent::PomodoroReminder => {
                    notifications::show_notification(
                        "Pomodoro Aguardando",
                        "Abra o app para continuar ou encerrar o Pomodoro.",
                    );
                }
                AppEvent::TodoDue(title, time) => {
                    let body = if time.is_empty() {
                        title.clone()
                    } else {
                        format!("{} - {}", title, time)
                    };
                    notifications::notify("TODO Pendente", &body, volume);
                }
                AppEvent::TodoVerificationRequired(todo_id, title, code) => {
                    self.verification_dialog = Some(VerificationDialog {
                        todo_id,
                        title,
                        code,
                        entered: String::new(),
                        error: false,
                    });
                    if self.mode == WindowMode::Hidden {
                        self.mode = WindowMode::Settings;
                    }
                }
            }

            // Atualiza estado do tray
            tray::update_tray_state(
                &mut self.tray,
                self.is_paused,
                self.is_on_break,
                self.pomodoro_active,
                self.pomodoro_waiting,
            );
        }
    }

    fn process_menu_events(&mut self) {
        while let Ok(event) = MenuEvent::receiver().try_recv() {
            let id = event.id().clone();

            if id == self.tray.ids.pause_resume.id().clone() {
                if self.is_paused {
                    self.is_paused = false;
                    let _ = self.cmd_tx.send(AppCommand::Resume);
                } else {
                    self.is_paused = true;
                    let _ = self.cmd_tx.send(AppCommand::Pause);
                }
                tray::update_tray_state(
                    &mut self.tray,
                    self.is_paused,
                    self.is_on_break,
                    self.pomodoro_active,
                    self.pomodoro_waiting,
                );
            } else if id == self.tray.ids.take_break.id().clone() {
                let _ = self.cmd_tx.send(AppCommand::TakeBreakNow);
            } else if id == self.tray.ids.skip_break.id().clone() {
                let _ = self.cmd_tx.send(AppCommand::SkipBreak);
            } else if id == self.tray.ids.settings.id().clone() {
                self.settings_draft = self.settings.lock().unwrap().clone();
                self.mode = WindowMode::Settings;
            } else if id == self.tray.ids.quit.id().clone() {
                std::process::exit(0);
            } else if id == self.tray.ids.pomodoro_start.id().clone() {
                let _ = self.cmd_tx.send(AppCommand::StartPomodoro);
            } else if id == self.tray.ids.pomodoro_confirm.id().clone() {
                let _ = self.cmd_tx.send(AppCommand::ConfirmPomodoroCycle);
            } else if id == self.tray.ids.pomodoro_end.id().clone() {
                let _ = self.cmd_tx.send(AppCommand::StopPomodoro);
            }
        }
    }

    fn render_overlay(&mut self, ctx: &egui::Context) {
        let s = self.settings.lock().unwrap().clone();
        egui::CentralPanel::default()
            .frame(egui::Frame::default().fill(egui::Color32::from_rgba_premultiplied(0, 0, 0, 230)))
            .show(ctx, |ui| {
                ui.vertical_centered(|ui| {
                    ui.add_space(ui.available_height() / 4.0);

                    ui.label(
                        egui::RichText::new("Pausa para os olhos")
                            .size(36.0)
                            .color(egui::Color32::WHITE),
                    );
                    ui.add_space(20.0);

                    ui.label(
                        egui::RichText::new(&self.break_message)
                            .size(18.0)
                            .color(egui::Color32::from_rgb(176, 176, 176)),
                    );
                    ui.add_space(30.0);

                    let color = if self.break_seconds_remaining <= 5 {
                        egui::Color32::from_rgb(255, 152, 0) // Laranja
                    } else {
                        egui::Color32::from_rgb(76, 175, 80) // Verde
                    };
                    ui.label(
                        egui::RichText::new(format!("{}", self.break_seconds_remaining))
                            .size(72.0)
                            .strong()
                            .color(color),
                    );

                    ui.label(
                        egui::RichText::new("segundos restantes")
                            .size(14.0)
                            .color(egui::Color32::from_rgb(128, 128, 128)),
                    );
                    ui.add_space(15.0);

                    // Progress bar
                    let progress = if s.break_duration > 0 {
                        self.break_seconds_remaining as f32 / s.break_duration as f32
                    } else {
                        0.0
                    };
                    let bar = egui::ProgressBar::new(progress)
                        .fill(egui::Color32::from_rgb(76, 175, 80));
                    ui.add_sized([300.0, 8.0], bar);
                    ui.add_space(30.0);

                    // Botões
                    ui.horizontal(|ui| {
                        ui.add_space((ui.available_width() - 280.0) / 2.0);
                        if s.allow_skip {
                            if ui
                                .add(egui::Button::new(
                                    egui::RichText::new("Pular").color(egui::Color32::WHITE),
                                )
                                .fill(egui::Color32::from_rgb(66, 66, 66))
                                .min_size(egui::vec2(120.0, 40.0)))
                                .clicked()
                            {
                                let _ = self.cmd_tx.send(AppCommand::SkipBreak);
                            }
                        }
                        if s.allow_skip && s.allow_postpone {
                            ui.add_space(16.0);
                        }
                        if s.allow_postpone {
                            let label = format!("Adiar {} min", s.postpone_minutes);
                            if ui
                                .add(egui::Button::new(
                                    egui::RichText::new(label).color(egui::Color32::WHITE),
                                )
                                .fill(egui::Color32::from_rgb(21, 101, 192))
                                .min_size(egui::vec2(140.0, 40.0)))
                                .clicked()
                            {
                                let _ = self.cmd_tx.send(AppCommand::PostponeBreak(
                                    s.postpone_minutes,
                                ));
                            }
                        }
                    });
                });
            });
    }

    fn render_settings(&mut self, ctx: &egui::Context) {
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading("Configurações - Wsi Break Time");
            ui.add_space(8.0);

            // Tabs
            ui.horizontal(|ui| {
                for (i, label) in ["Pausas", "Mensagens", "Geral", "TODOs", "Pomodoro"]
                    .iter()
                    .enumerate()
                {
                    if ui.selectable_label(self.settings_tab == i, *label).clicked() {
                        self.settings_tab = i;
                    }
                }
            });
            ui.separator();

            egui::ScrollArea::vertical().show(ui, |ui| {
                match self.settings_tab {
                    0 => self.render_pausas_tab(ui),
                    1 => self.render_mensagens_tab(ui),
                    2 => self.render_geral_tab(ui),
                    3 => self.render_todos_tab(ui),
                    4 => self.render_pomodoro_tab(ui),
                    _ => {}
                }
            });

            ui.add_space(8.0);
            ui.separator();
            ui.horizontal(|ui| {
                if ui.button("Salvar").clicked() {
                    self.apply_settings();
                    self.mode = WindowMode::Hidden;
                }
                if ui.button("Cancelar").clicked() {
                    self.mode = WindowMode::Hidden;
                }
            });
        });

        // Diálogo de verificação TODO
        if self.verification_dialog.is_some() {
            self.render_verification_dialog(ctx);
        }
    }

    fn render_pausas_tab(&mut self, ui: &mut egui::Ui) {
        ui.label(egui::RichText::new("Intervalo").strong());
        ui.horizontal(|ui| {
            ui.label("Pausa a cada:");
            ui.add(egui::Slider::new(&mut self.settings_draft.break_interval, 1..=120).suffix(" min"));
        });
        ui.horizontal(|ui| {
            ui.label("Duração da pausa:");
            ui.add(egui::Slider::new(&mut self.settings_draft.break_duration, 5..=300).suffix(" s"));
        });

        ui.add_space(8.0);
        ui.label(egui::RichText::new("Notificações").strong());
        ui.checkbox(&mut self.settings_draft.show_pre_notification, "Notificar antes da pausa");
        if self.settings_draft.show_pre_notification {
            ui.horizontal(|ui| {
                ui.label("Antecedência:");
                ui.add(egui::Slider::new(&mut self.settings_draft.pre_notification_seconds, 5..=120).suffix(" s"));
            });
        }

        ui.add_space(8.0);
        ui.label(egui::RichText::new("Controles").strong());
        ui.checkbox(&mut self.settings_draft.allow_skip, "Permitir pular pausas");
        ui.checkbox(&mut self.settings_draft.allow_postpone, "Permitir adiar pausas");
        if self.settings_draft.allow_postpone {
            ui.horizontal(|ui| {
                ui.label("Tempo de adiamento:");
                ui.add(egui::Slider::new(&mut self.settings_draft.postpone_minutes, 1..=30).suffix(" min"));
            });
        }
    }

    fn render_mensagens_tab(&mut self, ui: &mut egui::Ui) {
        ui.label(egui::RichText::new("Mensagens de pausa").strong());

        let mut to_remove = None;
        for (i, msg) in self.settings_draft.break_messages.iter().enumerate() {
            ui.horizontal(|ui| {
                let selected = self.selected_message == Some(i);
                if ui.selectable_label(selected, msg.as_str()).clicked() {
                    self.selected_message = Some(i);
                    self.new_message = msg.clone();
                }
                if self.settings_draft.break_messages.len() > 1 {
                    if ui.small_button("✕").clicked() {
                        to_remove = Some(i);
                    }
                }
            });
        }
        if let Some(i) = to_remove {
            self.settings_draft.break_messages.remove(i);
            if self.selected_message == Some(i) {
                self.selected_message = None;
                self.new_message.clear();
            }
        }

        ui.add_space(8.0);
        ui.text_edit_multiline(&mut self.new_message);
        ui.horizontal(|ui| {
            if ui.button("Adicionar").clicked() && !self.new_message.trim().is_empty() {
                self.settings_draft
                    .break_messages
                    .push(self.new_message.trim().to_string());
                self.new_message.clear();
            }
            if let Some(idx) = self.selected_message {
                if ui.button("Atualizar").clicked() && !self.new_message.trim().is_empty() {
                    self.settings_draft.break_messages[idx] =
                        self.new_message.trim().to_string();
                    self.new_message.clear();
                    self.selected_message = None;
                }
            }
        });
    }

    fn render_geral_tab(&mut self, ui: &mut egui::Ui) {
        ui.label(egui::RichText::new("Extras").strong());
        ui.horizontal(|ui| {
            ui.label("Lembrete de água:");
            ui.add(egui::Slider::new(&mut self.settings_draft.water_reminder_interval, 0..=120).suffix(" min"));
        });
        if self.settings_draft.water_reminder_interval == 0 {
            ui.label(egui::RichText::new("Desativado").color(egui::Color32::GRAY));
        }

        ui.add_space(8.0);
        ui.label(egui::RichText::new("Som").strong());
        ui.horizontal(|ui| {
            let vol = &mut self.settings_draft.notification_volume;
            let icon = if *vol <= 0.0 {
                "🔇"
            } else if *vol < 0.5 {
                "🔉"
            } else {
                "🔊"
            };
            ui.label(icon);
            ui.label("Volume:");
            let mut vol_f32 = *vol as f32;
            if ui.add(egui::Slider::new(&mut vol_f32, 0.0..=1.0).show_value(false)).changed() {
                *vol = vol_f32 as f64;
            }
            let pct = (*vol * 100.0).round() as i32;
            ui.label(if pct == 0 { "Mudo".to_string() } else { format!("{}%", pct) });
        });

        ui.add_space(8.0);
        ui.checkbox(&mut self.settings_draft.start_minimized, "Iniciar minimizado");
    }

    fn render_todos_tab(&mut self, ui: &mut egui::Ui) {
        ui.label(egui::RichText::new("TODOs").strong());

        let todos = self.todo_manager.lock().unwrap().todos.clone();
        for todo in &todos {
            let status_icon = if todo.status == crate::todo::model::TodoStatus::Completed {
                "✓"
            } else {
                "○"
            };
            let recurring = if todo.is_recurring { " (R)" } else { "" };
            let time = todo.scheduled_time.as_deref().unwrap_or("");
            ui.horizontal(|ui| {
                ui.label(format!("[{}]{} {} {}", status_icon, recurring, todo.title, time));
                if todo.status == crate::todo::model::TodoStatus::Pending {
                    if ui.small_button("Completar").clicked() {
                        let _ = self.cmd_tx.send(AppCommand::RequestTodoCompletion(
                            todo.id.clone(),
                        ));
                    }
                }
            });
        }

        if todos.is_empty() {
            ui.label(egui::RichText::new("Nenhum TODO").color(egui::Color32::GRAY));
        }
    }

    fn render_pomodoro_tab(&mut self, ui: &mut egui::Ui) {
        ui.label(egui::RichText::new("Durações").strong());
        ui.horizontal(|ui| {
            ui.label("Trabalho:");
            ui.add(egui::Slider::new(&mut self.settings_draft.pomodoro_work_duration, 1..=120).suffix(" min"));
        });
        ui.horizontal(|ui| {
            ui.label("Pausa curta:");
            ui.add(egui::Slider::new(&mut self.settings_draft.pomodoro_short_break, 1..=60).suffix(" min"));
        });
        ui.horizontal(|ui| {
            ui.label("Pausa longa:");
            ui.add(egui::Slider::new(&mut self.settings_draft.pomodoro_long_break, 1..=120).suffix(" min"));
        });
        ui.horizontal(|ui| {
            ui.label("Ciclos antes da pausa longa:");
            ui.add(egui::Slider::new(&mut self.settings_draft.pomodoro_cycles_before_long, 2..=10));
        });

        ui.add_space(16.0);
        ui.label(egui::RichText::new("Como funciona").strong());
        ui.label(
            "O Pomodoro é uma técnica de produtividade que alterna períodos de \
            trabalho focado com pausas curtas. Após um número de ciclos, \
            uma pausa longa é feita.\n\n\
            1. Inicie o Pomodoro pelo menu do tray\n\
            2. Trabalhe durante o período configurado\n\
            3. Ao final, confirme para iniciar a pausa ou encerrar\n\
            4. Se não confirmar, lembretes serão exibidos a cada 30 segundos",
        );
    }

    fn render_verification_dialog(&mut self, ctx: &egui::Context) {
        let mut close = false;
        let mut verify = false;

        if let Some(ref mut dialog) = self.verification_dialog {
            egui::Window::new("Verificação de TODO")
                .collapsible(false)
                .resizable(false)
                .anchor(egui::Align2::CENTER_CENTER, [0.0, 0.0])
                .show(ctx, |ui| {
                    ui.label(format!("TODO: {}", dialog.title));
                    ui.add_space(8.0);
                    ui.label("Digite o código para confirmar:");
                    ui.add_space(4.0);
                    ui.label(
                        egui::RichText::new(&dialog.code)
                            .size(24.0)
                            .strong()
                            .monospace(),
                    );
                    ui.add_space(8.0);
                    ui.text_edit_singleline(&mut dialog.entered);
                    if dialog.error {
                        ui.colored_label(egui::Color32::RED, "Código incorreto!");
                    }
                    ui.add_space(8.0);
                    ui.horizontal(|ui| {
                        if ui
                            .add_enabled(dialog.entered.len() == 8, egui::Button::new("Confirmar"))
                            .clicked()
                        {
                            verify = true;
                        }
                        if ui.button("Cancelar").clicked() {
                            close = true;
                        }
                    });
                });
        }

        if verify {
            if let Some(ref dialog) = self.verification_dialog {
                let _ = self.cmd_tx.send(AppCommand::VerifyTodoCompletion(
                    dialog.todo_id.clone(),
                    dialog.entered.clone(),
                ));
                // Verificação simples no lado do UI
                let mut tm = self.todo_manager.lock().unwrap();
                if tm.verify_and_complete(&dialog.todo_id, &dialog.entered) {
                    close = true;
                } else if let Some(ref mut d) = self.verification_dialog {
                    d.error = true;
                    d.entered.clear();
                }
            }
        }

        if close {
            self.verification_dialog = None;
        }
    }

    fn apply_settings(&mut self) {
        {
            let mut s = self.settings.lock().unwrap();
            *s = self.settings_draft.clone();
        }
        self.settings_manager.settings = self.settings_draft.clone();
        self.settings_manager.save();
        let _ = self.cmd_tx.send(AppCommand::SettingsChanged);
    }
}

impl eframe::App for App {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // Inicializa na primeira execução
        if !self.initialized {
            self.initialized = true;
            self.is_running = true;
            let _ = self.cmd_tx.send(AppCommand::Start);
            notifications::show_notification(
                "Wsi Break Time",
                "Proteção para seus olhos ativa!",
            );
            self.tray.ids.status.set_text("Timer ativo");
        }

        // Processa eventos
        self.process_events();
        self.process_menu_events();

        // Atualiza viewport conforme modo
        match self.mode {
            WindowMode::Hidden => {
                ctx.send_viewport_cmd(egui::ViewportCommand::Minimized(true));
            }
            WindowMode::Overlay => {
                ctx.send_viewport_cmd(egui::ViewportCommand::Minimized(false));
                ctx.send_viewport_cmd(egui::ViewportCommand::Fullscreen(true));
                ctx.send_viewport_cmd(egui::ViewportCommand::WindowLevel(
                    egui::WindowLevel::AlwaysOnTop,
                ));
                ctx.send_viewport_cmd(egui::ViewportCommand::Decorations(false));
                self.render_overlay(ctx);
            }
            WindowMode::Settings => {
                ctx.send_viewport_cmd(egui::ViewportCommand::Minimized(false));
                ctx.send_viewport_cmd(egui::ViewportCommand::Fullscreen(false));
                ctx.send_viewport_cmd(egui::ViewportCommand::WindowLevel(
                    egui::WindowLevel::Normal,
                ));
                ctx.send_viewport_cmd(egui::ViewportCommand::Decorations(true));
                ctx.send_viewport_cmd(egui::ViewportCommand::Focus);
                self.render_settings(ctx);
            }
        }

        // Repaint periódico para processar eventos mesmo quando hidden
        ctx.request_repaint_after(Duration::from_millis(500));
    }
}
