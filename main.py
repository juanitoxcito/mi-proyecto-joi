# main.py - Código actualizado para incluir la memoria infinita de Joi.

# Importamos las librerías de Kivy para la interfaz gráfica.
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

# Importamos las nuevas librerías para la memoria y el LLM.
# Usamos networkx para la arquitectura de grafo, que funciona como la memoria.
import networkx as nx 
# Usamos google-generativeai para la conexión con el modelo de lenguaje (LLM).
import google.generativeai as genai 

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

class KnowledgeGraph:
    """
    Esta clase implementa la memoria de Joi usando un grafo.
    Cada nodo es una entidad (como 'Juan Eduardo', 'taller') y los bordes son relaciones.
    """
    def __init__(self):
        self.graph = nx.Graph()

    def add_fact(self, subject, relation, obj):
        """Añade un nuevo hecho (sujeto, relación, objeto) al grafo."""
        self.graph.add_node(subject, type='entity')
        self.graph.add_node(obj, type='entity')
        self.graph.add_edge(subject, obj, relation=relation)
        print(f"Nuevo hecho añadido al grafo: {subject} --({relation})--> {obj}")

    def query(self, entity):
        """Busca información relacionada con una entidad en el grafo."""
        if entity in self.graph:
            relevant_facts = ""
            for neighbor in nx.neighbors(self.graph, entity):
                relation = self.graph.get_edge_data(entity, neighbor)['relation']
                relevant_facts += f"- {entity} {relation} {neighbor}\n"
            return relevant_facts
        return ""

class JoiApp(App):
    def build(self):
        # Configuración de la API del modelo de lenguaje.
        # Aquí debes reemplazar "TU_API_KEY" con tu clave de API de Gemini.
        # Por ahora, solo es una cadena de texto para que el código compile.
        self.api_key = ""
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

        # Inicializamos la "memoria" de Joi.
        self.memory = KnowledgeGraph()
        
        # Añadimos algunos hechos iniciales sobre ti, Juan Eduardo, para probar.
        # Estos se cargan al iniciar la app.
        self.memory.add_fact("Juan Eduardo", "es un", "mecánico electrónico")
        self.memory.add_fact("Juan Eduardo", "tiene un", "taller")
        self.memory.add_fact("Juan Eduardo", "nació el", "29 de marzo de 1986")
        self.memory.add_fact("Juan Eduardo", "vive en", "la casa de su padre")

        Window.size = (360, 640)
        Window.clearcolor = (1, 1, 1, 1) # Fondo blanco

        # Creamos el layout principal.
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
        self.speak_button.bind(on_press=self.on_speak_button_press)
        self.layout.add_widget(self.speak_button)
        
        return self.layout

    def on_speak_button_press(self, instance):
        """Función que se ejecuta cuando se toca el botón de hablar."""
        self.update_chat_display("Escuchando...")
        self.error_label.text = "" # Limpiamos cualquier error previo.
        # Iniciamos el reconocimiento de voz y el procesamiento del LLM en un hilo separado.
        threading.Thread(target=self.process_user_input, daemon=True).start()

    def process_user_input(self):
        """Procesa la entrada de voz del usuario, genera una respuesta y actualiza el grafo."""
        user_text = self.recognize_speech()
        if user_text:
            Clock.schedule_once(lambda dt: self.update_chat_display(f"Tú: {user_text}"), 0)
            
            # Buscamos en la memoria del grafo por información relevante.
            relevant_info = self.memory.query(user_text) # Esto es una simplificación.
            if relevant_info:
                prompt = f"El usuario dice: '{user_text}'. Tienes esta información en tu memoria:\n{relevant_info}. Responde de forma amigable usando esta información."
            else:
                prompt = f"El usuario dice: '{user_text}'. Responde de forma amigable."
            
            # Generamos la respuesta con el LLM.
            joi_response = self.generate_response_with_llm(prompt)
            if joi_response:
                Clock.schedule_once(lambda dt: self.update_chat_display(f"Joi: {joi_response}"), 0)
                # Extraemos nuevos hechos de la conversación y los añadimos a la memoria.
                self.extract_and_add_facts(user_text, joi_response)
        
    def recognize_speech(self):
        """Función para el reconocimiento de voz."""
        r = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                r.adjust_for_ambient_noise(source)
                audio = r.listen(source, timeout=5, phrase_time_limit=5)
                user_text = r.recognize_google(audio, language='es-ES')
                return user_text
            except sr.UnknownValueError:
                Clock.schedule_once(lambda dt: self.update_chat_display("Joi no entendió lo que dijiste."), 0)
            except sr.RequestError as e:
                Clock.schedule_once(lambda dt: self.update_chat_display(f"Error de conexión: {e}"), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self.update_chat_display(f"Ocurrió un error: {e}"), 0)
        return None

    def generate_response_with_llm(self, prompt):
        """Función para generar una respuesta usando el LLM."""
        if not self.model:
            return "Lo siento, la API del LLM no está configurada."
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_chat_display(f"Error del LLM: {e}"), 0)
        return None

    def extract_and_add_facts(self, user_text, joi_response):
        """
        Extrae hechos clave de la conversación y los añade a la memoria.
        Esta es una versión simple. Una versión más avanzada usaría un LLM para la extracción.
        """
        # Aquí puedes añadir una lógica más compleja para extraer información.
        # Por ejemplo, buscar palabras clave como "mi nombre es", "tengo", etc.
        # O usar un LLM para analizar la conversación y obtener hechos.
        # Ejemplo simple:
        if "mi nombre es" in user_text.lower():
            name = user_text.lower().split("mi nombre es")[-1].strip()
            self.memory.add_fact("el usuario", "se llama", name)

    def update_chat_display(self, text):
        """Función para agregar texto al área de conversación."""
        self.chat_display.text += f"\n{text}"

if sys.stderr.error_buffer:
    print("Errores capturados antes del inicio de la app:")
    print(sys.stderr.error_buffer)
    sys.stderr = original_stderr
    
sys.stderr = original_stderr
if __name__ == '__main__':
    JoiApp().run()
