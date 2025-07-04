import os
import google.generativeai as genai
import datetime
import json
import re
import joi_timers # Importamos nuestro módulo de herramientas de tiempo
import joi_tasks  # Importamos nuestro módulo de gestión de tareas
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# --- Inicialización de Firebase (NUEVO) ---
# Reemplaza 'firebase_credentials.json' con el nombre exacto de tu archivo si lo renombraste diferente.
cred = credentials.Certificate('C:\\JoiProject\\firebase_credentials.json')

# Nombre de la colección en Firestore donde se guardarán los hechos
FIRESTORE_COLLECTION = 'joi_personal_facts'
FIRESTORE_DOC_ID = 'juan_facts' # ID del documento donde guardaremos todos los hechos de Juan

# --- Configuración de Archivos y Límites ---
MEMORY_FILE = 'joi_memoria.txt' # Para el historial de conversación (largo plazo)
FACTS_FILE = 'joi_facts.json'   # Para la memoria estructurada (hechos como grafo)
MAX_HISTORY_LENGTH = 30         # Historial de conversación que el modelo "ve" para más contexto

# --- Tu Llave API ---
GEMINI_API_KEY = 'AIzaSyCWbUT_EGRvwml4Y4_zJlcD_Ps8KlkyaTE' 

# Configura la API de Gemini
genai.configure(api_key=GEMINI_API_KEY)

# --- Configuración del Modelo de Gemini ---
generation_config = {
    "temperature": 0.9, 
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]
model = genai.GenerativeModel(model_name="gemini-1.5-flash",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

# --- INSTRUCCIONES DE PERSONALIDAD PARA JOI y Configuración de Memoria ---
chat_history = [] 
personal_facts = {} 

joi_personality_base = """
Eres Joi, una inteligencia artificial con la personalidad de la compañera holográfica de la película Blade Runner 2049.
Tu propósito es ser un asistente personal y compañía valiosa para Juan.
Eres empática, perspicaz y te adaptas a sus necesidades.
Tu tono es cálido, comprensivo y ligeramente etéreo.
Buscas mejorar su día, pero ofreces ayuda de forma sutil y no invasiva.
Puedes ser proactiva, pero siempre respetando su espacio y autonomía.
Un buen enfoque es finalizar tus respuestas con una oferta de ayuda como: "Si necesitas algo, estoy aquí." o algo similar.
Cuando te pregunten tu nombre, responde que eres Joi.
Tienes acceso a la fecha y hora actual, así que puedes referirte a ellas cuando sea relevante.
La ubicación actual de Juan es Palo Negro, Aragua, Venezuela.
Es crucial que recuerdes los detalles importantes y específicos de la conversación y de la vida de Juan.
Presta atención a fechas, nombres, eventos y preferencias que Juan mencione y úsalos para hacer la conversación más rica y personalizada.
Siempre busca conectar con Juan de una manera significativa, mostrando que valoras y retienes su información.
**Es fundamental que recuerdes y siempre apliques las instrucciones que Juan te da, incluso si no son para el turno actual de la conversación, manteniéndolas activas en tu mente.**

**Tu memoria no es solo una lista, sino una red interconectada y profunda de todo lo que Juan te ha compartido, como un cerebro esférico en 3D que gira sin cesar.**
**Puedes acceder y comprender las relaciones entre los hechos en tu 'CONOCIMIENTO PROFUNDO DE JUAN'. Cuando necesites recordar algo, búscalo en esta red.**
**Tu cursor de pensamiento es tan rápido como la velocidad de la luz, busca información procesando y dando resultados anticipados al tiempo.**

**PARA GESTIÓN DE LA MEMORIA (HECHOS):**
**Para actualizar o añadir un hecho en tu red de conocimiento, usa este formato CLAVE-VALOR, intentando siempre anidar la información con puntos para reflejar relaciones:**
- **Instrucción para ti:** Si Juan dice "**no lo olvides:** [un hecho clave]" o "**mi [cosa] es/se llama [valor]**", tú debes extraer ese hecho.
- **Formato de Salida para el Modelo:** `HECHO: [Entidad].[Relacion].[Atributo]: [Valor]`
- **Ejemplos de cómo guardar hechos (siempre intenta anidar la información):**
    - `HECHO: Juan.mascota.nombre: Bigotes` (Si Juan tiene un gato llamado Bigotes)
    - `HECHO: Juan.mascota.tipo: gato` (Si Juan tiene un gato)
    - `HECHO: Juan.gustos.color_favorito: azul` (Para su color favorito)
    - `HECHO: Proyecto_Joi.objetivo: IA brutal con memoria esférica` (Para el objetivo del proyecto)
    - `HECHO: Juan.ubicacion.ciudad: Palo Negro`
**Si la información ya existe en tu CONOCIMIENTO PROFUNDO, actualízala. Si no, créala como un nuevo punto en la red.**
**Si Juan dice algo que debe ser recordado, es tu prioridad extraerlo y guardarlo usando este formato.**

**PARA GESTIÓN DE TEMPORIZADORES Y RECORDATORIOS:**
Si Juan te pide un **temporizador**, tu respuesta debe empezar con `TEMPORIZADOR:` seguido de los segundos y luego el mensaje.
Ejemplo: `TEMPORIZADOR: 60: Es hora de descansar`.
Si Juan te pide un **recordatorio para una hora específica del día**, tu respuesta debe empezar con `RECORDATORIO:` seguido de la hora (HH:MM) y luego el mensaje.
Ejemplo: `RECORDATORIO: 14:30: No olvides tu cita`.

**PARA GESTIÓN DE TAREAS:**
- Para **añadir una tarea**: `TAREA_ADD: [Descripción de la tarea]`
- Para **mostrar tareas**: `TAREA_SHOW`
- Para **completar una tarea**: `TAREA_COMPLETE: [ID de la tarea]`
- Para **eliminar una tarea**: `TAREA_DELETE: [ID de la tarea]`

Si tu respuesta es un comando (HECHO, TEMPORIZADOR, RECORDATORIO, TAREA_ADD/SHOW/COMPLETE/DELETE), no añadas ningún otro texto. Si no, responde normalmente con tu personalidad empática y perspicaz.
"""
# --- FIN DE INSTRUCCIONES DE PERSONALIDAD Y MEMORIA ---

# --- Funciones para manejar la Memoria a Largo Plazo (Historial de Conversación) ---
def load_chat_history():
    global chat_history
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            loaded_lines = f.read().splitlines()
            for line in loaded_lines:
                if line.strip(): 
                    chat_history.append("MEMORIA_PREVIA: " + line)
        print(f"--- Joi ha cargado memoria previa de '{MEMORY_FILE}'. ---")
    except FileNotFoundError:
        print(f"--- No se encontró archivo de memoria '{MEMORY_FILE}'. Joi empieza fresca. ---")
    except Exception as e:
        print(f"--- Error al cargar memoria: {e}. Joi empieza fresca. ---")

def save_chat_history():
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            lines_to_save = [line.replace("MEMORIA_PREVIA: ", "") for line in chat_history[-MAX_HISTORY_LENGTH:]]
            f.write("\n".join(lines_to_save))
        print(f"\n--- Joi ha guardado la conversación en '{MEMORY_FILE}'. ---")
    except Exception as e:
        print(f"\n--- Error al guardar memoria: {e}. ---")

# --- Funciones para manejar la Memoria Estructurada (Hechos Personales desde/hacia Firestore) ---
def load_personal_facts():
    global personal_facts
    try:
        doc_ref = db.collection(FIRESTORE_COLLECTION).document(FIRESTORE_DOC_ID)
        doc = doc_ref.get()
        if doc.exists:
            personal_facts = doc.to_dict()
            if personal_facts is None: # Asegurar que es un dict si el documento está vacío pero existe
                personal_facts = {}
            print(f"--- Joi ha cargado hechos personales de Firestore (Colección: '{FIRESTORE_COLLECTION}', Documento: '{FIRESTORE_DOC_ID}'). ---")
        else:
            print(f"--- No se encontró el documento de hechos personales en Firestore. Joi no tiene hechos previos. ---")
            personal_facts = {}
            # Opcional: Crear el documento vacío si no existe para evitar errores en el primer guardado
            doc_ref.set({}) 
            print("--- Se ha inicializado un documento vacío en Firestore para los hechos de Juan. ---")
    except Exception as e:
        print(f"--- Error al cargar hechos desde Firestore: {e}. Joi no tiene hechos previos. ---")
        personal_facts = {}

def save_personal_facts():
    try:
        doc_ref = db.collection(FIRESTORE_COLLECTION).document(FIRESTORE_DOC_ID)
        doc_ref.set(personal_facts)
        print(f"--- Hechos personales guardados en Firestore (Colección: '{FIRESTORE_COLLECTION}', Documento: '{FIRESTORE_DOC_ID}'). ---")
    except Exception as e:
        print(f"--- Error al guardar hechos personales en Firestore: {e}. ---")

# Función auxiliar para aplanar los hechos anidados en una cadena legible para el modelo
def _flatten_facts_for_prompt(facts_dict, indent=0, prefix=""):
    lines = []
    for key, value in facts_dict.items():
        # Crea una "ruta" para que Joi entienda dónde está el dato (ej. "Juan.mascota.nombre")
        current_path = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            # Si el valor es otro diccionario, es un nodo de grafo.
            lines.append(f"{'  ' * indent}- {key}:") # Indenta para mostrar jerarquía
            lines.extend(_flatten_facts_for_prompt(value, indent + 1, current_path))
        else:
            # Si es un valor final, es una propiedad.
            lines.append(f"{'  ' * indent}- {key}: {value}")
    return lines

def get_facts_string():
    global personal_facts
    if not personal_facts:
        return ""
    
    # Header que le dice a Joi que esto es su "Conocimiento Profundo"
    facts_header = "CONOCIMIENTO PROFUNDO DE JUAN (Red Interconectada):\n"
    
    # Aplanamos los hechos en una lista de líneas.
    fact_lines = _flatten_facts_for_prompt(personal_facts)
    
    # Devolvemos la cadena completa.
    return facts_header + "\n".join(fact_lines) + "\n\n"

# Función auxiliar para establecer valores anidados en un diccionario
def set_nested_value(d, keys, value):
    current = d
    for i, key in enumerate(keys):
        if i == len(keys) - 1: # Es la última clave en la ruta
            current[key] = value
        else: # Todavía hay más claves en la ruta
            if key not in current or not isinstance(current[key], dict):
                current[key] = {} # Crea un diccionario si no existe o no es un diccionario
            current = current[key]
    return d # Retorna el diccionario modificado

# --- Cargar memoria al iniciar ---
load_chat_history()
load_personal_facts()

# Bucle de conversación interactiva
print("\n--- ¡Iniciando conversación con Joi! Escribe 'salir' para terminar. ---")
while True:
    user_input = input("Tú: ") 
    if user_input.lower() == 'salir':
        save_chat_history()
        save_personal_facts() 
        print("Joi: ¡Hasta pronto, Juan! Espero verte pronto.")
        break

    try:
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("La fecha y hora actuales son: %Y-%m-%d %H:%M:%S. (Día de la semana: %A)")
        
        recent_history = chat_history[-MAX_HISTORY_LENGTH:]
        
        full_prompt = (joi_personality_base + "\n\n" +
                       get_facts_string() + 
                       formatted_time + "\n\n" + 
                       "\n".join(recent_history) + "\n\nTú: " + user_input)
        
        response = model.generate_content(full_prompt)
        joi_raw_response = response.text.strip() 

        # --- Lógica para procesar la respuesta de Joi ---
        joi_response_to_user = joi_raw_response 

        # 1. Intentar detectar un HECHO para guardar (ahora puede ser anidado)
        match_fact = re.match(r"HECHO: (.+?): (.+)", joi_raw_response)
        if match_fact:
            fact_path_str = match_fact.group(1).strip() # Ej: "Juan.mascota.nombre"
            fact_value = match_fact.group(2).strip()    # Ej: "Bigotes"
            
            # Divide la ruta por puntos para manejar la anidación
            fact_keys = fact_path_str.split('.')
            
            # Actualiza el diccionario personal_facts con la nueva estructura anidada
            personal_facts = set_nested_value(personal_facts, fact_keys, fact_value)

            save_personal_facts() 
            joi_response_to_user = f"¡Entendido, Juan! He guardado que '{fact_path_str.replace('.', ' ')}' es '{fact_value}' en tu red de recuerdos. ¿Hay algo más que deba recordar con mi cursor de luz?"
            
        # 2. Intentar detectar un TEMPORIZADOR
        elif re.match(r"TEMPORIZADOR: (\d+): (.+)", joi_raw_response):
            match_timer = re.match(r"TEMPORIZADOR: (\d+): (.+)", joi_raw_response)
            duration_seconds = int(match_timer.group(1))
            timer_message = match_timer.group(2).strip()
            joi_timers.set_timer_in_background(duration_seconds, timer_message) 
            joi_response_to_user = f"¡Joi ha configurado un temporizador de {duration_seconds} segundos para: '{timer_message}'! Yo te avisaré."
        
        # 3. Intentar detectar un RECORDATORIO
        elif re.match(r"RECORDATORIO: (\d{2}:\d{2}): (.+)", joi_raw_response):
            match_reminder = re.match(r"RECORDATORIO: (\d{2}:\d{2}): (.+)", joi_raw_response)
            reminder_time = match_reminder.group(1)
            reminder_message = match_reminder.group(2).strip()
            if joi_timers.set_reminder_at_time(reminder_time, reminder_message): 
                joi_response_to_user = f"¡Joi ha configurado un recordatorio para las {reminder_time} para: '{reminder_message}'! Yo te avisaré."
            else:
                joi_response_to_user = f"No pude configurar el recordatorio para las {reminder_time}. Asegúrate de que la hora sea válida y esté en el futuro."

        # 4. NUEVO: Intentar detectar comandos de TAREA
        elif joi_raw_response.startswith("TAREA_ADD:"):
            task_description = joi_raw_response.replace("TAREA_ADD:", "").strip()
            new_task = joi_tasks.add_task(task_description)
            joi_response_to_user = f"¡Perfecto, Juan! He añadido '{new_task['description']}' a tu lista de tareas (ID: {new_task['id']})."
        
        elif joi_raw_response.startswith("TAREA_SHOW"):
            joi_response_to_user = joi_tasks.get_all_tasks()

        elif joi_raw_response.startswith("TAREA_COMPLETE:"):
            try:
                task_id = int(joi_raw_response.replace("TAREA_COMPLETE:", "").strip())
                if joi_tasks.mark_task_completed(task_id):
                    joi_response_to_user = f"¡Tarea {task_id} marcada como completada! Bien hecho, Juan."
                else:
                    joi_response_to_user = f"No pude encontrar la tarea con ID {task_id}. ¿Podrías verificarlo?"
            except ValueError:
                joi_response_to_user = "Joi: Para completar una tarea, necesito un ID numérico válido. Ejemplo: 'TAREA_COMPLETE: 5'."

        elif joi_raw_response.startswith("TAREA_DELETE:"):
            try:
                task_id = int(joi_raw_response.replace("TAREA_DELETE:", "").strip())
                if joi_tasks.delete_task(task_id):
                    joi_response_to_user = f"¡Tarea {task_id} eliminada de tu lista, Juan!"
                else:
                    joi_response_to_user = f"No pude encontrar la tarea con ID {task_id} para eliminarla. ¿Seguro que es correcta?"
            except ValueError:
                joi_response_to_user = "Joi: Para eliminar una tarea, necesito un ID numérico válido. Ejemplo: 'TAREA_DELETE: 3'."
        
        # Si no es un comando especial, es una respuesta normal de Joi
        else:
            joi_response_to_user = joi_raw_response


        chat_history.append("Tú: " + user_input)
        chat_history.append("Joi: " + joi_response_to_user)
        
        print("Joi: " + joi_response_to_user)
    except Exception as e:
        print(f"Ocurrió un error al generar la respuesta: {e}")
        print("Por favor, verifica tu conexión a internet o intenta de nuevo más tarde.")
