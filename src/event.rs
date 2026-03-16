/// Eventos enviados do background (timer thread) para o foreground (UI).
#[derive(Debug, Clone)]
pub enum AppEvent {
    /// Countdown tick: segundos restantes até próxima pausa
    Tick(i64),
    /// Pausa iniciou com mensagem
    BreakStarted(String),
    /// Tick durante pausa: segundos restantes
    BreakTick(i32),
    /// Pausa terminou
    BreakEnded,
    /// Pré-notificação: segundos até a pausa
    PreNotification(i32),
    /// Lembrete de água
    WaterReminder,
    /// Pomodoro tick: segundos restantes
    PomodoroTick(i32),
    /// Pomodoro estado mudou
    PomodoroStateChanged(String),
    /// Pomodoro precisa confirmação
    PomodoroConfirmationNeeded(String),
    /// Pomodoro lembrete (30s waiting)
    PomodoroReminder,
    /// TODO pendente
    TodoDue(String, String), // (title, time)
    /// TODO verificação necessária
    TodoVerificationRequired(String, String, String), // (todo_id, title, code)
}

/// Comandos enviados do foreground (UI) para o background (timer thread).
#[derive(Debug, Clone)]
pub enum AppCommand {
    Start,
    Stop,
    Pause,
    Resume,
    SkipBreak,
    PostponeBreak(i32), // minutos
    TakeBreakNow,
    SettingsChanged,
    // Pomodoro
    StartPomodoro,
    StopPomodoro,
    ConfirmPomodoroCycle,
    // TODOs
    RequestTodoCompletion(String), // todo_id
    VerifyTodoCompletion(String, String), // (todo_id, entered_code)
}
