# main.py
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.clock import Clock # Para actualizar la UI desde otro hilo
import speech_recognition as sr # ¡NUEVO! Librería para reconocimiento de voz
# from plyer import stt # ¡ELIMINADO! Ya no usaremos plyer para STT
# from plyer import tts # ¡ELIMINADO TEMPORALMENTE! Lo reincorporaremos después si es necesario
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
