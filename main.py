# main.py - Código corregido y completo para tu asistente Joi.

# Importamos las librerías necesarias de Kivy para la interfaz gráfica.
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window

# Importamos las librerías para manejar la voz y la concurrencia.
import threading
import speech_recognition as sr
import sys
import io

# --- Clase para capturar la salida de errores (stderr) ---
# Esto nos ayuda a ver errores que podrían no mostrarse en la pantalla.
class ErrorCapturingStringIO(io.StringIO):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_buffer = ""

    def write(self, s):
        self.error_buffer += s
        super().write(s)

# Redirigimos la salida de errores a nuestra clase para poder verla.
original_stderr = sys.stderr
sys.stderr = ErrorCapturingStringIO()

class JoiApp(App):
    def build(self):
        # NOTA: Asegúrate de que este archivo esté guardado con codificación UTF-8
        # para que las tildes y otros caracteres especiales no causen errores.
        
        Window.size = (360, 640)
        Window.clearcolor = (1, 1, 1, 1) # Fondo blanco

        # Creamos el layout principal de la aplicación, que organiza los elementos verticalmente.
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        # Título de la aplicación.
        title_label = Label(text="Joi: Tu Asistente Personal",
                            font_size='32sp',
                            bold=True,
                            color=[0.1, 0.1, 0.1, 1],
                            size_hint_y=None, height=40)
        self.layout.add_widget(title_label)
        
        # Área de texto para mostrar la conversación.
        self.chat_display = TextInput(
            text='¡Hola, Juan Eduardo! Estoy listo para escuchar. Toca el botón para hablar.',
            readonly=True,
            font_size=20,
            background_color=[0.9, 0.9, 0.9, 1], # Gris claro
            foreground_color=[0.1, 0.1, 0.1, 1], # Negro
            size_hint_y=0.8, # Ocupa la mayor parte de la pantalla.
            padding=[15, 15, 15, 15] # Espaciado interno.
        )
        self.layout.add_widget(self.chat_display)

        # Etiqueta para mostrar errores (nueva adición)
        # Aquí se cerró el paréntesis que faltaba.
        self.error_label = Label(
            text="Si hay errores, aparecerán aquí...",
            color=[1, 0, 0, 1], # Rojo
            size_hint_y=None, height=40,
            halign='center',
            valign='middle'
        )
        self.layout.add_widget(self.error_label)
        
        # Botón para iniciar el reconocimiento de voz.
        self.speak_button = Button(
            text="Toca para Hablar",
            font_size='24sp',
            bold=True,
            background_normal='',
            background_color=[0.1, 0.5, 0.8, 1], # Un tono de azul.
            color=[1, 1, 1, 1], # Texto blanco.
            size_hint_y=None, height=60
        )
        # Asignamos la acción que se ejecutará al tocar el botón.
        self.speak_button.bind(on_press=self.on_speak_button_press)
        self.layout.add_widget(self.speak_button)
        
        # Devolvemos el layout principal para que se muestre en la ventana.
        return self.layout

    def on_speak_button_press(self, instance):
        """Función que se ejecuta cuando se toca el botón de hablar."""
        self.update_chat_display("Escuchando...")
        self.error_label.text = "" # Limpiamos cualquier error previo.
        # Iniciamos el reconocimiento de voz en un hilo separado para no congelar la UI.
        threading.Thread(target=self.recognize_speech_thread, daemon=True).start()

    def recognize_speech_thread(self):
        """Función para el reconocimiento de voz que corre en un hilo."""
        r = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                # Ajustamos para el ruido ambiental.
                r.adjust_for_ambient_noise(source)
                # Escuchamos lo que dice el usuario.
                audio = r.listen(source, timeout=5, phrase_time_limit=5)
                
                # Intentamos reconocer el audio usando la API de Google.
                user_text = r.recognize_google(audio, language='es-ES')
                
                # Usamos Clock.schedule_once para actualizar la UI de Kivy desde el hilo.
                Clock.schedule_once(lambda dt: self.update_chat_display(f"Tú: {user_text}"), 0)
                
            except sr.UnknownValueError:
                Clock.schedule_once(lambda dt: self.update_chat_display("Joi no entendió lo que dijiste."), 0)
            except sr.RequestError as e:
                Clock.schedule_once(lambda dt: self.update_chat_display(f"Error de conexión: {e}"), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self.update_chat_display(f"Ocurrió un error: {e}"), 0)

    def update_chat_display(self, text):
        """Función para agregar texto al área de conversación."""
        self.chat_display.text += f"\n{text}"

# Corregimos el error del paréntesis en el mensaje.
# Cuando el programa inicia, si hay errores en el buffer, los muestra.
if sys.stderr.error_buffer:
    print("Errores capturados antes del inicio de la app:")
    print(sys.stderr.error_buffer)
    sys.stderr = original_stderr # Restauramos la salida de errores original.
    
# Si no hay errores, restauramos la salida y ejecutamos la app.
sys.stderr = original_stderr
if __name__ == '__main__':
    JoiApp().run()
