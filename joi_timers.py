import threading
import time
import datetime

def set_timer_in_background(duration_seconds, message_to_user):
    """
    Configura un temporizador que se ejecuta en segundo plano.
    Cuando el tiempo se agota, imprime un mensaje al usuario.
    """
    def timer_function():
        print(f"\n--- ¡Joi ha configurado un temporizador para {duration_seconds} segundos! Esperando... ---")
        time.sleep(duration_seconds)
        print(f"\n--- ¡Ding, dong, Juan! Tu temporizador ha terminado. Joi te recuerda: {message_to_user} ---")
        print("Tú: ", end='', flush=True) # Para que el prompt de "Tú:" reaparezca

    # Inicia el temporizador en un hilo separado para que no bloquee la conversación
    timer_thread = threading.Thread(target=timer_function)
    timer_thread.daemon = True # Esto asegura que el hilo se cerrará si el programa principal se cierra
    timer_thread.start()

def set_reminder_at_time(reminder_time_str, message_to_user):
    """
    Configura un recordatorio para una hora específica del día.
    reminder_time_str debe estar en formato HH:MM (ej. "14:30").
    """
    try:
        # Parsear la hora del recordatorio
        reminder_hour, reminder_minute = map(int, reminder_time_str.split(':'))

        now = datetime.datetime.now()
        # Crear un objeto datetime para la hora del recordatorio HOY
        reminder_datetime = now.replace(hour=reminder_hour, minute=reminder_minute, second=0, microsecond=0)

        # Si la hora del recordatorio ya pasó hoy, programarlo para mañana
        if reminder_datetime <= now:
            reminder_datetime += datetime.timedelta(days=1)

        time_to_wait_seconds = (reminder_datetime - now).total_seconds()

        if time_to_wait_seconds > 0:
            print(f"\n--- ¡Joi ha configurado un recordatorio para las {reminder_time_str}! Esperando... ---")
            def reminder_function():
                time.sleep(time_to_wait_seconds)
                print(f"\n--- ¡Ding, dong, Juan! ¡Es hora! Joi te recuerda: {message_to_user} ---")
                print("Tú: ", end='', flush=True) # Para que el prompt de "Tú:" reaparezca

            reminder_thread = threading.Thread(target=reminder_function)
            reminder_thread.daemon = True
            reminder_thread.start()
            return True
        else:
            print("--- Joi: La hora del recordatorio ya ha pasado. Por favor, especifica una hora futura. ---")
            return False
    except ValueError:
        print("--- Joi: Formato de hora de recordatorio inválido. Usa HH:MM. ---")
        return False
    except Exception as e:
        print(f"--- Joi: Error al configurar recordatorio: {e}. ---")
        return False

# Ejemplo de uso (esto no se ejecutará al importarse, solo si se llama directamente)
if __name__ == "__main__": 
    print("Probando temporizador de 5 segundos...")
    set_timer_in_background(5, "¡Prueba de temporizador!")

    print("\nProbando recordatorio para 1 minuto en el futuro...")
    # Calcula 1 minuto en el futuro para la prueba
    future_time = (datetime.datetime.now() + datetime.timedelta(minutes=1)).strftime("%H:%M")
    set_reminder_at_time(future_time, "¡Prueba de recordatorio en un minuto!")

    # Mantenemos el programa principal vivo para que los hilos se ejecuten
    input("Presiona Enter para salir después de que los temporizadores terminen o quieras detener. ")