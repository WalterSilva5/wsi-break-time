use std::io::Cursor;

use rodio::{Decoder, OutputStream, Sink};

const NOTIFICATION_WAV: &[u8] = include_bytes!("../assets/notification.wav");

pub fn show_notification(title: &str, body: &str) {
    let t = title.to_string();
    let b = body.to_string();
    std::thread::spawn(move || {
        let _ = notify_rust::Notification::new()
            .summary(&t)
            .body(&b)
            .appname("Wsi Break Time")
            .show();
    });
}

pub fn play_sound(volume: f64) {
    if volume <= 0.0 {
        return;
    }
    let vol = volume as f32;
    std::thread::spawn(move || {
        if let Ok((_stream, handle)) = OutputStream::try_default() {
            if let Ok(sink) = Sink::try_new(&handle) {
                let cursor = Cursor::new(NOTIFICATION_WAV);
                if let Ok(source) = Decoder::new(cursor) {
                    sink.set_volume(vol);
                    sink.append(source);
                    sink.sleep_until_end();
                }
            }
        }
    });
}

/// Combina notificação visual + som.
pub fn notify(title: &str, body: &str, volume: f64) {
    show_notification(title, body);
    play_sound(volume);
}
