# main.py
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.clock import Clock # Para actualizar la UI desde otro hilo
from plyer import stt # Speech-to-Text (Reconocimiento de Voz)
from plyer import tts # Text-to-Speech (Sintesis de Voz)
import sys # Importamos sys para redirigir la salida de errores
import io # Importamos io para capturar la salida de errores

# --- Importaciones mínimas para el arranque y la UI ---
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window

# --- Clase para capturar la salida de errores (stderr) ---
class ErrorCapturingStringIO(io.StringIO):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_buffer = ""

    def write(self, s):
        self.error_buffer += s
        super().write(s) # También escribe al buffer original

# Redirigir stderr para capturar errores que ocurren antes de que Kivy inicie completamente
original_stderr = sys.stderr
sys.stderr = ErrorCapturingStringIO()

class JoiApp(App):
    def build(self):
        Window.size = (360, 640)

        # Creamos el layout principal de la aplicación
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Área de texto para mostrar la conversación
        self.chat_display = TextInput(
            text='¡Hola, Juan Eduardo! Estoy listo para escuchar. Toca el botón para hablar.',
            readonly=True,
            font_size=20,
            background_color=[0.9, 0.9, 0.9, 1], # Gris claro
            foreground_color=[0.1, 0.1, 0.1, 1], # Negro
            size_hint_y=0.8, # Ocupa el 80% de la altura
            padding=[10, 10, 10, 10] # Espaciado interno
        )
        self.layout.add_widget(self.chat_display)

        # Etiqueta para mostrar errores (nueva adición)
        self.error_label = Label(
            text="Errores aparecerán aquí...",
            size_hint_y=None,
            height=50, # Altura inicial, se ajustará
            color=[1, 0, 0, 1], # Texto rojo para errores
            markup=True,
            valign='top',
            halign='left',
            text_size=(Window.width * 0.9, None)
        )
        self.error_label.bind(texture_size=self.error_label.setter('size'))
        self.layout.add_widget(self.error_label)


        # Botón para activar el reconocimiento de voz
        self.listen_button = Button(
            text='Toca para Hablar',
            font_size=24,
            size_hint_y=0.2, # Ocupa el 20% de la altura
            background_normal='', # Elimina el fondo predeterminado
            background_color=[0.2, 0.6, 0.8, 1], # Azul vibrante
            color=[1, 1, 1, 1], # Texto blanco
            bold=True,
            border_radius=[10], # Bordes redondeados
            markup=True # Habilita el marcado para texto
        )
        # Asignamos la función on_listen_button_press al evento de presionar el botón
        self.listen_button.bind(on_press=self.on_listen_button_press)
        self.layout.add_widget(self.listen_button)

        # Mostrar errores capturados al inicio si los hay
        self.update_error_display()

        return self.layout

    def update_error_display(self):
        # Esta función actualiza la etiqueta de errores con lo que se ha capturado
        captured_errors = sys.stderr.error_buffer.strip()
        if captured_errors:
            self.error_label.text = f"[color=FF0000]ERRORES:[/color]\n{captured_errors}"
            self.error_label.height = max(50, self.error_label.texture_size[1]) # Ajustar altura
        else:
            self.error_label.text = "No se detectaron errores al iniciar."


    def on_listen_button_press(self, instance):
        # Deshabilitamos el botón para evitar múltiples clics mientras escucha
        self.listen_button.disabled = True
        self.listen_button.text = 'Escuchando...'
        self.chat_display.text = 'Por favor, habla ahora...'
        self.error_label.text = "No se detectaron errores al iniciar." # Limpiar errores anteriores

        # Iniciamos el reconocimiento de voz en un hilo separado para no bloquear la UI
        threading.Thread(target=self._start_speech_recognition).start()

    def _start_speech_recognition(self):
        try:
            # Intentamos iniciar el reconocimiento de voz
            results = stt.listen(language='es-ES', show_partial=False)

            if results and len(results) > 0:
                recognized_text = results[0]
                Clock.schedule_once(lambda dt: self._process_recognized_text(recognized_text), 0)
            else:
                Clock.schedule_once(lambda dt: self._update_chat_display("No se reconoció nada. Intenta de nuevo."), 0)

        except Exception as e:
            error_message = f"Error en el reconocimiento de voz: {e}"
            Clock.schedule_once(lambda dt: self._update_chat_display(error_message), 0)
        finally:
            Clock.schedule_once(lambda dt: self._reset_listen_button(), 0)

    def _process_recognized_text(self, user_input):
        self.chat_display.text = f"Tú: {user_input}\nJoi: Pensando..."
        self.chat_display.cursor = (0, len(self.chat_display.text.splitlines()))

        # En esta versión simplificada, Joi solo responde con un mensaje de prueba
        joi_response_to_user = f"Hola Juan Eduardo, me dijiste: '{user_input}'. ¡Estoy funcionando correctamente!"
        Clock.schedule_once(lambda dt: self._update_chat_display_with_joi_response(user_input, joi_response_to_user), 0)

    def _update_chat_display(self, text):
        self.chat_display.text = f"Tú: {text}\nJoi: (Respuesta de Joi aquí...)"
        self.chat_display.cursor = (0, len(self.chat_display.text.splitlines()))

    def _update_chat_display_with_joi_response(self, user_input, joi_response):
        current_text = self.chat_display.text.replace("Joi: Pensando...", "")
        self.chat_display.text = current_text + f"\n[color=FFD700]Joi:[/color] {joi_response}"
        self.chat_display.cursor = (0, len(self.chat_display.text.splitlines()))

    def _reset_listen_button(self):
        self.listen_button.disabled = False
        self.listen_button.text = 'Toca para Hablar'

if __name__ == '__main__':
    # Capturar errores que ocurren antes de que Kivy inicie completamente
    try:
        JoiApp().run()
    except Exception as app_e:
        # Si la app falla al iniciar, imprimir el error al stderr capturado
        sys.stderr.write(f"\nFATAL ERROR AL INICIAR LA APP: {app_e}\n")
        import traceback
        sys.stderr.write(traceback.format_exc())
    finally:
        # Asegurarse de restaurar stderr al final
        sys.stderr = original_st
