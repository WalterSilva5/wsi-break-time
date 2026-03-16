use std::collections::{HashMap, HashSet};

use chrono::Local;
use rand::Rng;

use super::model::{TodoItem, TodoStatus};

pub struct TodoManager {
    pub todos: Vec<TodoItem>,
    notified_todos: HashSet<String>,
    pending_verification: HashMap<String, String>, // todo_id -> code
}

impl TodoManager {
    pub fn new(todos: Vec<TodoItem>) -> Self {
        Self {
            todos,
            notified_todos: HashSet::new(),
            pending_verification: HashMap::new(),
        }
    }

    pub fn pending_todos(&self) -> Vec<&TodoItem> {
        self.todos
            .iter()
            .filter(|t| t.status == TodoStatus::Pending)
            .collect()
    }

    /// Verifica TODOs pendentes e retorna notificações a enviar.
    /// Retorna: Vec<(title, time_str)>
    pub fn check_todos(&mut self) -> Vec<(String, String)> {
        let mut notifications = Vec::new();

        // Reset recurring TODOs at midnight
        for todo in &mut self.todos {
            if todo.needs_reset() {
                todo.reset_for_new_day();
            }
        }

        // Check due TODOs
        for todo in &self.todos {
            if todo.is_due() && !self.notified_todos.contains(&todo.id) {
                let time_str = todo
                    .scheduled_time
                    .clone()
                    .unwrap_or_default();
                notifications.push((todo.title.clone(), time_str));
                self.notified_todos.insert(todo.id.clone());
            }
        }

        notifications
    }

    /// Reseta notificações no início de novo dia.
    pub fn reset_daily(&mut self) {
        self.notified_todos.clear();
        for todo in &mut self.todos {
            if todo.needs_reset() {
                todo.reset_for_new_day();
            }
        }
    }

    /// Gera código de verificação para TODO recorrente.
    /// Retorna None se não precisa verificação (não recorrente).
    pub fn request_completion(&mut self, todo_id: &str) -> Option<String> {
        let todo = self.todos.iter().find(|t| t.id == todo_id)?;
        if !todo.is_recurring {
            // Completa direto
            if let Some(t) = self.todos.iter_mut().find(|t| t.id == todo_id) {
                t.mark_completed();
            }
            return None;
        }
        let code = generate_code();
        self.pending_verification
            .insert(todo_id.to_string(), code.clone());
        Some(code)
    }

    /// Verifica código e completa o TODO se correto.
    pub fn verify_and_complete(&mut self, todo_id: &str, entered_code: &str) -> bool {
        if let Some(expected) = self.pending_verification.get(todo_id) {
            if expected.eq_ignore_ascii_case(entered_code) {
                self.pending_verification.remove(todo_id);
                if let Some(todo) = self.todos.iter_mut().find(|t| t.id == todo_id) {
                    todo.mark_completed();
                }
                return true;
            }
        }
        false
    }

    pub fn add_todo(&mut self, todo: TodoItem) {
        self.todos.push(todo);
    }

    pub fn remove_todo(&mut self, todo_id: &str) {
        self.todos.retain(|t| t.id != todo_id);
    }

    pub fn last_check_date(&self) -> String {
        Local::now().format("%Y-%m-%d").to_string()
    }
}

fn generate_code() -> String {
    const CHARS: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    let mut rng = rand::thread_rng();
    (0..8)
        .map(|_| CHARS[rng.gen_range(0..CHARS.len())] as char)
        .collect()
}
