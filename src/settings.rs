use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

use crate::todo::model::TodoItem;

fn default_messages() -> Vec<String> {
    vec![
        "Hora de descansar os olhos!\nOlhe para algo a 6 metros de distância.".into(),
        "Levante-se e alongue o corpo!".into(),
        "Respire fundo e relaxe os ombros.".into(),
        "Pisque os olhos várias vezes para hidratá-los.".into(),
        "Olhe pela janela e descanse a visão.".into(),
    ]
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppSettings {
    #[serde(default = "default_20")]
    pub break_interval: i32,
    #[serde(default = "default_20")]
    pub break_duration: i32,
    #[serde(default = "default_messages")]
    pub break_messages: Vec<String>,
    #[serde(default = "default_true")]
    pub start_minimized: bool,
    #[serde(default)]
    pub start_with_windows: bool,
    #[serde(default = "default_true")]
    pub show_pre_notification: bool,
    #[serde(default = "default_30")]
    pub pre_notification_seconds: i32,
    #[serde(default = "default_true")]
    pub allow_skip: bool,
    #[serde(default = "default_true")]
    pub allow_postpone: bool,
    #[serde(default = "default_5")]
    pub postpone_minutes: i32,
    #[serde(default)]
    pub water_reminder_interval: i32,
    #[serde(default = "default_volume")]
    pub notification_volume: f64,
    #[serde(default = "default_25")]
    pub pomodoro_work_duration: i32,
    #[serde(default = "default_5")]
    pub pomodoro_short_break: i32,
    #[serde(default = "default_15")]
    pub pomodoro_long_break: i32,
    #[serde(default = "default_4")]
    pub pomodoro_cycles_before_long: i32,
    #[serde(default)]
    pub todos: Vec<TodoItem>,
}

fn default_true() -> bool { true }
fn default_20() -> i32 { 20 }
fn default_30() -> i32 { 30 }
fn default_25() -> i32 { 25 }
fn default_15() -> i32 { 15 }
fn default_5() -> i32 { 5 }
fn default_4() -> i32 { 4 }
fn default_volume() -> f64 { 0.5 }

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            break_interval: 20,
            break_duration: 20,
            break_messages: default_messages(),
            start_minimized: true,
            start_with_windows: false,
            show_pre_notification: true,
            pre_notification_seconds: 30,
            allow_skip: true,
            allow_postpone: true,
            postpone_minutes: 5,
            water_reminder_interval: 0,
            notification_volume: 0.5,
            pomodoro_work_duration: 25,
            pomodoro_short_break: 5,
            pomodoro_long_break: 15,
            pomodoro_cycles_before_long: 4,
            todos: Vec::new(),
        }
    }
}

pub struct SettingsManager {
    path: PathBuf,
    pub settings: AppSettings,
}

impl SettingsManager {
    pub fn new() -> Self {
        let path = Self::config_path();
        let settings = Self::load_from(&path);
        Self { path, settings }
    }

    fn config_path() -> PathBuf {
        let base = dirs::config_dir()
            .or_else(|| dirs::home_dir().map(|h| h.join("WsiBreakTime")))
            .unwrap_or_else(|| PathBuf::from("."));
        base.join("WsiBreakTime").join("config.json")
    }

    fn load_from(path: &PathBuf) -> AppSettings {
        match fs::read_to_string(path) {
            Ok(data) => serde_json::from_str(&data).unwrap_or_default(),
            Err(_) => AppSettings::default(),
        }
    }

    pub fn save(&self) {
        if let Some(parent) = self.path.parent() {
            let _ = fs::create_dir_all(parent);
        }
        if let Ok(data) = serde_json::to_string_pretty(&self.settings) {
            let _ = fs::write(&self.path, data);
        }
    }

    pub fn reload(&mut self) {
        self.settings = Self::load_from(&self.path);
    }
}
