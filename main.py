# main.py - Código actualizado para usar secretos de GitHub y la memoria en Firestore.

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
import json # Necesario para serializar el grafo a JSON
import os # Necesario para leer la variable de entorno con el secreto de GitHub

# Importamos las nuevas librerías para la memoria y el LLM.
import networkx as nx
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

# Importamos las librerías de Firebase para la memoria en la nube (Firestore).
import firebase_admin
from firebase_admin import credentials, firestore

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
    Ahora, también se encarga de guardar y cargar la memoria en la nube.
    """
    def __init__(self, db, user_id):
        self.graph = nx.Graph()
        self.db = db
        self.user_id = user_id
        # Cargamos la memoria desde la nube al iniciar.
        self.load_from_firestore()

    def add_fact(self, subject, relation, obj):
        """Añade un nuevo hecho al grafo y lo guarda en Firestore."""
        try:
            self.graph.add_node(subject, type='entity')
            self.graph.add_node(obj, type='entity')
            self.graph.add_edge(subject, obj, relation=relation)
            print(f"Nuevo hecho añadido al grafo: {subject} --({relation})--> {obj}")
            self.save_to_firestore() # Guardamos en la nube.
        except Exception as e:
            print(f"Error al añadir hecho al grafo: {e}")

    def query(self, entity):
        """Busca información relacionada con una entidad en el grafo."""
        if entity in self.graph:
            relevant_facts = ""
            for neighbor in nx.neighbors(self.graph, entity):
                relation = self.graph.get_edge_data(entity, neighbor)['relation']
                relevant_facts += f"- {entity} {relation} {neighbor}\n"
            return relevant_facts
        return ""

    def save_to_firestore(self):
        """Serializa el grafo a un formato JSON y lo guarda en Firestore."""
        # Serializamos el grafo a una lista de aristas para poder guardarlo.
        edges = list(self.graph.edges(data=True))
        # El documento se guardará en una colección específica para el usuario.
        doc_ref = self.db.collection(f'joi_memory/{self.user_id}/graph_data').document('knowledge_graph')
        
        try:
            doc_ref.set({'edges': json.dumps(edges)})
            print("Grafo guardado exitosamente en Firestore.")
        except Exception as e:
            print(f"Error al guardar el grafo en Firestore: {e}")

    def load_from_firestore(self):
        """Carga el grafo desde Firestore al iniciar la aplicación."""
        doc_ref = self.db.collection(f'joi_memory/{self.user_id}/graph_data').document('knowledge_graph')
        try:
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                edges_json = data.get('edges')
                if edges_json:
                    edges = json.loads(edges_json)
                    self.graph.add_edges_from(edges)
                    print("Grafo cargado exitosamente desde Firestore.")
            else:
                print("No se encontró el grafo en Firestore. Creando uno nuevo.")
        except Exception as e:
            print(f"Error al cargar el grafo desde Firestore: {e}")

class JoiApp(App):
    def build(self):
        # --- Configuración de la API del modelo de lenguaje ---
        # Pega aquí tu clave de API de Gemini.
        self.api_key = "AIzaSyCWbUT_EGRvwml4Y4_zJlcD_Ps8KlkyaTE"
        self.model = None
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # --- Inicialización de Firebase (Memoria en la nube) ---
        # Ahora el código obtendrá el secreto de forma segura.
        try:
            # Obtener el secreto del entorno de GitHub Actions
            firebase_service_account_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
            
            if firebase_service_account_json:
                cred = credentials.Certificate(json.loads(firebase_service_account_json))
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                # Reemplaza con un ID único para ti.
                self.user_id = "Juan_Eduardo" 
            else:
                # Si el secreto no está disponible, la app se ejecutará sin memoria en la nube.
                self.db = None
                self.user_id = None
                print("El secreto de Firebase no se encontró en el entorno.")
                
        except Exception as e:
            self.db = None
            self.user_id = None
            print(f"Error al inicializar Firebase: {e}")
            
        # Inicializamos la "memoria" de Joi con la conexión a Firestore.
        if self.db and self.user_id:
            self.memory = KnowledgeGraph(self.db, self.user_id)
        else:
            self.memory = None
            print("La memoria en la nube no está disponible. Joi no podrá recordar.")

        Window.size = (360, 640)
        Window.clearcolor = (1, 1, 1, 1)

        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        title_label = Label(text="Joi: Tu Asistente Personal",
                            font_size='32sp',
                            bold=True,
                            color=[0.1, 0.1, 0.1, 1],
                            size_hint_y=None, height=40)
        self.layout.add_widget(title_label)
        
        self.chat_display = TextInput(
            text='¡Hola, Juan Eduardo! Estoy listo para escuchar. Toca el botón para hablar.',
            readonly=True,
            font_size=20,
            background_color=[0.9, 0.9, 0.9, 1],
            foreground_color=[0.1, 0.1, 0.1, 1],
            size_hint_y=0.8,
            padding=[15, 15, 15, 15]
        )
        self.layout.add_widget(self.chat_display)

        self.error_label = Label(
            text="Si hay errores, aparecerán aquí...",
            color=[1, 0, 0, 1],
            size_hint_y=None, height=40,
            halign='center',
            valign='middle'
        )
        self.layout.add_widget(self.error_label)
        
        self.speak_button = Button(
            text="Toca para Hablar",
            font_size='24sp',
            bold=True,
            background_normal='',
            background_color=[0.1, 0.5, 0.8, 1],
            color=[1, 1, 1, 1],
            size_hint_y=None, height=60
        )
        self.speak_button.bind(on_press=self.on_speak_button_press)
        self.layout.add_widget(self.speak_button)
        
        return self.layout

    def on_speak_button_press(self, instance):
        """Función que se ejecuta cuando se toca el botón de hablar."""
        if not self.memory:
            self.update_chat_display("Error: La memoria en la nube no está configurada.")
            return

        self.update_chat_display("Escuchando...")
        self.error_label.text = ""
        threading.Thread(target=self.process_user_input, daemon=True).start()

    def process_user_input(self):
        """Procesa la entrada de voz del usuario, genera una respuesta y actualiza el grafo."""
        user_text = self.recognize_speech()
        if user_text:
            Clock.schedule_once(lambda dt: self.update_chat_display(f"Tú: {user_text}"), 0)
            
            # Buscamos en la memoria del grafo por información relevante.
            relevant_info = self.memory.query(user_text)
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

    def extract_facts_with_llm(self, user_text, joi_response):
        """
        Utiliza el LLM para extraer hechos estructurados de la conversación.
        """
        if not self.model:
            return []

        conversation = f"Usuario: {user_text}\nJoi: {joi_response}"
        extraction_prompt = f"""
        Extrae hechos clave de la siguiente conversación. Cada hecho debe ser una tripleta de (sujeto, relación, objeto).
        Si un hecho es sobre el usuario, usa 'el usuario' como sujeto.
        Por ejemplo, si la conversación es 'Mi nombre es Juan.', un hecho sería ['el usuario', 'se llama', 'Juan'].
        Otro ejemplo: 'Tengo un gato que se llama Misa.' -> ['el usuario', 'tiene un gato llamado', 'Misa'].

        Conversación:
        {conversation}

        Devuelve solo un array de JSONs. Cada JSON debe tener los campos 'subject', 'relation' y 'object'. Si no hay hechos, devuelve un array vacío.
        """
        
        try:
            response = self.model.generate_content(
                extraction_prompt,
                generation_config=GenerationConfig(response_mime_type="application/json")
            )
            facts = json.loads(response.text)
            return facts
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_chat_display(f"Error al extraer hechos con LLM: {e}"), 0)
            return []

    def extract_and_add_facts(self, user_text, joi_response):
        """
        Extrae hechos clave de la conversación y los añade a la memoria.
        Ahora llama a la nueva función de extracción basada en el LLM.
        """
        facts = self.extract_facts_with_llm(user_text, joi_response)
        for fact in facts:
            subject = fact.get("subject", "")
            relation = fact.get("relation", "")
            obj = fact.get("object", "")
            if subject and relation and obj:
                self.memory.add_fact(subject, relation, obj)

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
