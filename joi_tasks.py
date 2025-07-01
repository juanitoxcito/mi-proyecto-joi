import json
import os

TASKS_FILE = 'joi_tasks.json'

def load_tasks():
    """Carga las tareas desde el archivo JSON."""
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"--- Joi: Error al leer '{TASKS_FILE}'. Archivo JSON corrupto. Creando nueva lista. ---")
                return []
    return []

def save_tasks(tasks):
    """Guarda las tareas en el archivo JSON."""
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=4, ensure_ascii=False)

def add_task(description):
    """Añade una nueva tarea a la lista."""
    tasks = load_tasks()
    new_task = {
        "id": len(tasks) + 1, # ID simple basado en el tamaño actual de la lista
        "description": description,
        "completed": False
    }
    tasks.append(new_task)
    save_tasks(tasks)
    return new_task

def get_all_tasks():
    """Devuelve una lista formateada de todas las tareas."""
    tasks = load_tasks()
    if not tasks:
        return "No tienes tareas pendientes, Juan. ¡Un día relajado!"

    task_strings = []
    for task in tasks:
        status = "[COMPLETADA]" if task["completed"] else "[PENDIENTE]"
        task_strings.append(f"- {task['id']}. {status} {task['description']}")

    return "Tu lista de tareas:\n" + "\n".join(task_strings)

def mark_task_completed(task_id):
    """Marca una tarea como completada por su ID."""
    tasks = load_tasks()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = True
            found = True
            break
    if found:
        save_tasks(tasks)
        return True
    return False

def delete_task(task_id):
    """Elimina una tarea por su ID."""
    tasks = load_tasks()
    initial_len = len(tasks)
    tasks = [task for task in tasks if task["id"] != task_id]
    if len(tasks) < initial_len:
        save_tasks(tasks)
        return True
    return False

# Este bloque solo se ejecutará si corres joi_tasks.py directamente para pruebas
if __name__ == "__main__":
    print("--- Probando joi_tasks.py ---")

    # Asegurarse de que el archivo de tareas esté vacío al inicio de la prueba
    if os.path.exists(TASKS_FILE):
        os.remove(TASKS_FILE)

    print("\nAñadiendo tareas...")
    add_task("Comprar leche")
    add_task("Llamar a María")
    add_task("Estudiar Python")
    print(get_all_tasks())

    print("\nMarcando tarea 2 como completada...")
    if mark_task_completed(2):
        print("Tarea 2 marcada como completada.")
    else:
        print("Tarea 2 no encontrada.")
    print(get_all_tasks())

    print("\nEliminando tarea 1...")
    if delete_task(1):
        print("Tarea 1 eliminada.")
    else:
        print("Tarea 1 no encontrada.")
    print(get_all_tasks())

    print("\nIntentando eliminar una tarea inexistente (ID 99)...")
    if delete_task(99):
        print("Tarea 99 eliminada (esto no debería pasar).")
    else:
        print("Tarea 99 no encontrada (¡Correcto!).")
    print(get_all_tasks())

    print("\nAñadiendo otra tarea para verificar IDs...")
    add_task("Sacar la basura")
    print(get_all_tasks())