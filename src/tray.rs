use tray_icon::menu::{Menu, MenuEvent, MenuItem, PredefinedMenuItem, Submenu};
use tray_icon::{Icon, TrayIcon, TrayIconBuilder};

pub struct TrayMenuIds {
    pub status: MenuItem,
    pub pause_resume: MenuItem,
    pub take_break: MenuItem,
    pub skip_break: MenuItem,
    pub pomodoro_start: MenuItem,
    pub pomodoro_confirm: MenuItem,
    pub pomodoro_end: MenuItem,
    pub settings: MenuItem,
    pub quit: MenuItem,
    pub todo_submenu: Submenu,
}

pub struct AppTray {
    pub tray: TrayIcon,
    pub menu: Menu,
    pub ids: TrayMenuIds,
}

pub fn create_tray() -> AppTray {
    let menu = Menu::new();

    let status = MenuItem::new("Wsi Break Time", false, None);
    let pause_resume = MenuItem::new("Pausar", true, None);
    let take_break = MenuItem::new("Pausa agora", true, None);
    let skip_break = MenuItem::new("Pular pausa", true, None);
    let todo_submenu = Submenu::new("TODOs", true);
    let pomodoro_start = MenuItem::new("Iniciar Pomodoro", true, None);
    let pomodoro_confirm = MenuItem::new("Confirmar ciclo", true, None);
    let pomodoro_end = MenuItem::new("Encerrar Pomodoro", true, None);
    let settings = MenuItem::new("Configurações", true, None);
    let quit = MenuItem::new("Sair", true, None);

    // Itens inicialmente ocultos
    skip_break.set_enabled(false);
    pomodoro_confirm.set_enabled(false);
    pomodoro_end.set_enabled(false);

    let _ = menu.append(&status);
    let _ = menu.append(&PredefinedMenuItem::separator());
    let _ = menu.append(&pause_resume);
    let _ = menu.append(&take_break);
    let _ = menu.append(&skip_break);
    let _ = menu.append(&PredefinedMenuItem::separator());
    let _ = menu.append(&todo_submenu);
    let _ = menu.append(&PredefinedMenuItem::separator());
    let _ = menu.append(&pomodoro_start);
    let _ = menu.append(&pomodoro_confirm);
    let _ = menu.append(&pomodoro_end);
    let _ = menu.append(&PredefinedMenuItem::separator());
    let _ = menu.append(&settings);
    let _ = menu.append(&quit);

    let icon = create_icon([76, 175, 80]); // Verde

    let tray = TrayIconBuilder::new()
        .with_menu(Box::new(menu.clone()))
        .with_tooltip("Wsi Break Time")
        .with_icon(icon)
        .build()
        .expect("Falha ao criar tray icon");

    let ids = TrayMenuIds {
        status,
        pause_resume,
        take_break,
        skip_break,
        pomodoro_start,
        pomodoro_confirm,
        pomodoro_end,
        settings,
        quit,
        todo_submenu,
    };

    AppTray { tray, menu, ids }
}

pub fn create_icon(color: [u8; 3]) -> Icon {
    let size = 32u32;
    let mut rgba = vec![0u8; (size * size * 4) as usize];
    let center = size as f32 / 2.0;
    let radius = center - 1.0;

    for y in 0..size {
        for x in 0..size {
            let idx = ((y * size + x) * 4) as usize;
            let dx = x as f32 - center;
            let dy = y as f32 - center;
            if dx * dx + dy * dy <= radius * radius {
                rgba[idx] = color[0];
                rgba[idx + 1] = color[1];
                rgba[idx + 2] = color[2];
                rgba[idx + 3] = 255;
            }
        }
    }

    Icon::from_rgba(rgba, size, size).expect("Falha ao criar ícone")
}

pub fn update_tray_state(tray: &mut AppTray, is_paused: bool, is_on_break: bool, pomodoro_active: bool, pomodoro_waiting: bool) {
    // Atualiza cor do ícone
    let color = if pomodoro_waiting {
        [255, 152, 0] // Laranja
    } else if pomodoro_active {
        [233, 30, 99] // Rosa
    } else if is_on_break {
        [33, 150, 243] // Azul
    } else if is_paused {
        [255, 193, 7] // Amarelo
    } else {
        [76, 175, 80] // Verde
    };
    let icon = create_icon(color);
    let _ = tray.tray.set_icon(Some(icon));

    // Atualiza texto do botão pausar/retomar
    tray.ids.pause_resume.set_text(if is_paused { "Retomar" } else { "Pausar" });

    // Visibilidade dos itens
    tray.ids.skip_break.set_enabled(is_on_break);
    tray.ids.take_break.set_enabled(!is_on_break && !is_paused);
    tray.ids.pomodoro_start.set_enabled(!pomodoro_active);
    tray.ids.pomodoro_confirm.set_enabled(pomodoro_waiting);
    tray.ids.pomodoro_end.set_enabled(pomodoro_active);
}
