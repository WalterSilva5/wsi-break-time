import 'package:flutter_test/flutter_test.dart';
import 'package:wsi_break_time/models/app_settings.dart';
import 'package:wsi_break_time/models/todo_item.dart';
import 'package:wsi_break_time/models/pomodoro_state.dart';

void main() {
  group('AppSettings', () {
    test('default values', () {
      final settings = AppSettings();
      expect(settings.breakInterval, 20);
      expect(settings.breakDuration, 20);
      expect(settings.breakMessages.length, 5);
      expect(settings.pomodoroWorkDuration, 25);
      expect(settings.notificationVolume, 0.5);
    });

    test('JSON round-trip', () {
      final original = AppSettings(
        breakInterval: 30,
        breakDuration: 15,
        notificationVolume: 0.8,
      );
      final json = original.toJson();
      final restored = AppSettings.fromJson(json);
      expect(restored.breakInterval, 30);
      expect(restored.breakDuration, 15);
      expect(restored.notificationVolume, 0.8);
    });

    test('backward compat playSound bool to volume', () {
      final fromTrue = AppSettings.fromJson({'playSound': true});
      expect(fromTrue.notificationVolume, 0.5);

      final fromFalse = AppSettings.fromJson({'playSound': false});
      expect(fromFalse.notificationVolume, 0.0);
    });
  });

  group('TodoItem', () {
    test('non-recurring is always due when pending', () {
      final todo = TodoItem(title: 'Test');
      expect(todo.isDue, true);
    });

    test('mark completed', () {
      final todo = TodoItem(title: 'Test');
      todo.markCompleted();
      expect(todo.status, TodoStatus.completed);
      expect(todo.completedAt, isNotNull);
      expect(todo.isDue, false);
    });

    test('JSON round-trip', () {
      final original = TodoItem(
        title: 'Test',
        description: 'Desc',
        isRecurring: true,
        scheduledTime: '09:00',
      );
      final json = original.toJson();
      final restored = TodoItem.fromJson(json);
      expect(restored.title, 'Test');
      expect(restored.isRecurring, true);
      expect(restored.scheduledTime, '09:00');
    });
  });

  group('PomodoroState', () {
    test('enum values', () {
      expect(PomodoroState.idle.value, 'idle');
      expect(PomodoroState.working.value, 'working');
      expect(PomodoroState.waitingConfirmation.value, 'waiting');
    });
  });
}
