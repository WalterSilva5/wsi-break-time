use chrono::{Local, NaiveTime};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum TodoStatus {
    Pending,
    Completed,
}

impl Default for TodoStatus {
    fn default() -> Self {
        Self::Pending
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TodoItem {
    pub id: String,
    pub title: String,
    #[serde(default)]
    pub description: String,
    #[serde(default)]
    pub is_recurring: bool,
    #[serde(default)]
    pub scheduled_time: Option<String>, // "HH:MM"
    #[serde(default)]
    pub status: TodoStatus,
    #[serde(default)]
    pub completed_at: Option<String>,
    #[serde(default)]
    pub last_reset_date: Option<String>, // "YYYY-MM-DD"
    #[serde(default)]
    pub created_at: String,
}

impl TodoItem {
    pub fn new(title: String) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            title,
            description: String::new(),
            is_recurring: false,
            scheduled_time: None,
            status: TodoStatus::Pending,
            completed_at: None,
            last_reset_date: None,
            created_at: Local::now().to_rfc3339(),
        }
    }

    pub fn is_due(&self) -> bool {
        if self.status != TodoStatus::Pending {
            return false;
        }
        if !self.is_recurring {
            return true;
        }
        if let Some(ref time_str) = self.scheduled_time {
            if let Ok(scheduled) = NaiveTime::parse_from_str(time_str, "%H:%M") {
                return Local::now().time() >= scheduled;
            }
        }
        true
    }

    pub fn needs_reset(&self) -> bool {
        if !self.is_recurring {
            return false;
        }
        let today = Local::now().format("%Y-%m-%d").to_string();
        match &self.last_reset_date {
            Some(date) => date != &today,
            None => true,
        }
    }

    pub fn reset_for_new_day(&mut self) {
        self.status = TodoStatus::Pending;
        self.completed_at = None;
        self.last_reset_date = Some(Local::now().format("%Y-%m-%d").to_string());
    }

    pub fn mark_completed(&mut self) {
        self.status = TodoStatus::Completed;
        self.completed_at = Some(Local::now().to_rfc3339());
    }
}
