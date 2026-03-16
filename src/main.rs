#![windows_subsystem = "windows"]

mod app;
mod event;
mod notifications;
mod pomodoro;
mod settings;
mod timer;
mod todo;
mod tray;

use std::sync::{Arc, Mutex};

use crate::settings::SettingsManager;
use crate::todo::manager::TodoManager;
use crate::tray::create_tray;

fn main() -> eframe::Result {
    // Carrega configurações
    let settings_manager = SettingsManager::new();
    let settings = Arc::new(Mutex::new(settings_manager.settings.clone()));
    let todo_manager = Arc::new(Mutex::new(TodoManager::new(
        settings_manager.settings.todos.clone(),
    )));

    // Canais de comunicação
    let (event_tx, event_rx) = crossbeam_channel::unbounded();
    let (cmd_tx, cmd_rx) = crossbeam_channel::unbounded();

    // Inicia thread do timer
    let timer_settings = Arc::clone(&settings);
    let timer_todos = Arc::clone(&todo_manager);
    timer::spawn_timer_thread(event_tx, cmd_rx, timer_settings, timer_todos);

    // Cria tray icon (deve ser no main thread)
    let tray = create_tray();

    // Configura eframe
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_visible(false)
            .with_inner_size([500.0, 600.0])
            .with_title("Wsi Break Time"),
        ..Default::default()
    };

    eframe::run_native(
        "Wsi Break Time",
        options,
        Box::new(move |cc| {
            // Thread que mantém o event loop ativo mesmo com janela oculta
            let ctx = cc.egui_ctx.clone();
            std::thread::spawn(move || loop {
                std::thread::sleep(std::time::Duration::from_millis(250));
                ctx.request_repaint();
            });

            Ok(Box::new(app::App::new(
                event_rx,
                cmd_tx,
                settings_manager,
                settings,
                todo_manager,
                tray,
            )))
        }),
    )
}
