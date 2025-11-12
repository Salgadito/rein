import asyncio
import re
# --- MODIFICADO: Importar 'TimeoutError' y renombrarlo a 'PlaywrightTimeoutError' ---
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Route
# --- NUEVOS IMPORTS ---
from datetime import datetime
import random
import os

# --- Lista de dominios para bloquear (ejemplo) ---
# ... (lista sin cambios) ...
BLOCK_LIST = [
    "doubleclick.net",
    "google-analytics.com",
    "googletagservices.com",
    "googlesyndication.com",
    "adservice.google.com",
    "z.moatads.com",
    "pagead2.googlesyndication.com",
]

# --- NUEVA CONSTANTE ---
# Define el nombre del archivo de log
LOG_FILE = "success_log.txt"


async def block_ads(route: Route):
# ... (función sin cambios) ...
    """
    Función asíncrona que intercepta las peticiones.
    Aborta la petición si la URL coincide con la lista de bloqueo.
    """
    url = route.request.url
    try:
        if any(domain in url for domain in BLOCK_LIST):
            # print(f"Bloqueando (async): {url}") # Descomenta para depuración
            await route.abort()
        else:
            await route.continue_()
    except Exception as e:
        # Esto puede pasar si la página se cierra mientras la ruta está pendiente
        # print(f"Error al procesar la ruta {url}: {e}") # Opcional: puede ser muy ruidoso
        pass # Ignoramos errores si la ruta falla (ej. página cerrándose)

# --- NUEVA FUNCIÓN DE LOG ---
async def log_success(log_id: str, lock: asyncio.Lock):
    """
    Escribe una entrada de éxito en el archivo de log de forma asíncrona y segura.
    Usa un Lock para prevenir escrituras concurrentes.
    """
    # Obtenemos la fecha y hora actual
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] - {log_id} - Voto exitoso.\n"
    
    # Adquirimos el lock antes de escribir en el archivo
    async with lock:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_entry)
            print(f"    {log_id} -> ¡Éxito registrado en {LOG_FILE}!")
        except Exception as e:
            print(f"[ERROR] {log_id} No se pudo escribir en el log: {e}")

# --- LÓGICA REESTRUCTURADA EN UN "WORKER" ---
async def run_worker(worker_id: int, browser, lock: asyncio.Lock, url_a_visitar: str):
    """
    Un solo "trabajador" que se ejecuta en un bucle infinito.
    Cada trabajador simula un usuario, creando un nuevo contexto por iteración.
    """
    iteration_count = 0
    while True:
        iteration_count += 1
        # log_id dinámico para este worker
        log_id = f"[Worker {worker_id} | Iter {iteration_count}]"
        context = None  # Definimos context aquí para el 'finally'
        
        try:
            # --- 3. "Sesión Limpia": Creamos un NUEVO contexto ---
            print(f"{log_id} Creando nuevo contexto...")
            context = await browser.new_context()
            
            # --- 4. Aplicamos el bloqueo de anuncios AL NUEVO CONTEXTO ---
            await context.route("**/*", block_ads)
            
            # --- 5. Creamos una nueva página en este contexto ---
            page = await context.new_page()
            
            print(f"{log_id} Navegando a: {url_a_visitar}")
            
            # --- 6. GOTO ---
            await page.goto(url_a_visitar, timeout=60000)
            page_title = await page.title()
            print(f"{log_id} Página cargada. Título: {page_title}")

            # --- 7. CLIC PARTICIPANTE (XPath) ---
            try:
                selector_xpath = "/html/body/div/div[2]/form/div[2]/div/div[2]/div/div/div/div[2]/div/div/span/div/div[25]/label/div[2]/div[1]/div"
                print(f"{log_id} Buscando (XPath)...")
                element_locator = page.locator(f"xpath={selector_xpath}").first
                await element_locator.click(timeout=10000)
                print(f"{log_id} ¡Clic (Participante) OK!")

            except PlaywrightTimeoutError:
                print(f"[ERROR] {log_id} No se encontró (Participante) después de 10s.")
                # Si esto falla, saltamos el resto de la iteración
                continue 
            except Exception as e:
                print(f"[ERROR] {log_id} Clic (Participante): {e}")
                continue


            # --- 8. CLIC ENVIAR (MODIFICADO A XPATH) ---
            try:
                # Este es el XPath que proporcionaste para el botón de enviar
                selector_enviar_xpath = "/html/body/div/div[2]/form/div[2]/div/div[3]/div/div[1]/div/span/span"
                
                print(f"{log_id} Buscando 'Enviar' (con XPath)...")
                
                # Usamos el localizador de XPath en lugar de page.get_by_text()
                enviar_locator = page.locator(f"xpath={selector_enviar_xpath}").first
                
                await enviar_locator.click(timeout=5000)
                print(f"{log_id} ¡Clic (Enviar) OK!")
                
                # --- ¡ÉXITO! Registramos en el log ---
                await log_success(log_id, lock)

            except PlaywrightTimeoutError:
                # Actualicé el mensaje de error para reflejar el cambio
                print(f"[ERROR] {log_id} No se encontró 'Enviar' (XPath) después de 5s.")
            except Exception as e:
                print(f"[ERROR] {log_id} Clic (Enviar): {e}")


            # --- 9. Pausa corta y aleatoria ---
            # Espera entre 3 y 7 segundos para no sobrecargar
            sleep_time = random.uniform(0.5, 2)
            print(f"{log_id} Iteración completada. Esperando {sleep_time:.1f}s...")
            await asyncio.sleep(sleep_time)

        except PlaywrightTimeoutError:
            print(f"[ERROR] {log_id} Timeout: No se pudo cargar la página en 60s.")
        except Exception as e:
            print(f"[ERROR] {log_id} Ocurrió un error inesperado: {e}")
        finally:
            # --- 10. Limpieza de la iteración ---
            if context:
                # print(f"{log_id} Cerrando contexto.") # Descomentar para depuración
                await context.close()
        
        # Pequeña pausa para evitar que un worker fallido sature la consola
        if "ERROR" in log_id:
             await asyncio.sleep(5)


async def main():
    """
    Función principal asíncrona.
    --- MODIFICADO ---
    Lanza el navegador una vez.
    Lanza N 'workers' paralelos (definidos en NUM_PARALLEL_SESSIONS).
    Usa asyncio.gather para ejecutarlos todos concurrentemente.
    """
    
    # --- ¡CAMBIA ESTE NÚMERO! ---
    # Define cuántos navegadores paralelos quieres ejecutar
    NUM_PARALLEL_SESSIONS = 6
    # -----------------------------

    url_a_visitar = "https://docs.google.com/forms/d/e/1FAIpQLSfwaXdc-S_BBC3f6zQGZsl9B5845j6ef7nCT4MXMmLbsDYYkw/viewform"
    print(f"[INFO] Iniciando el script con {NUM_PARALLEL_SESSIONS} workers paralelos.")

    # Creamos un Lock para pasarlo a los workers (para el log)
    lock = asyncio.Lock()

    async with async_playwright() as playwright:
        # --- 1. Lanzamos el navegador UNA SOLA VEZ ---
        print("[INFO] Lanzando el navegador (visible)...")
        browser = await playwright.chromium.launch(headless=True)
        
        # --- 2. Creamos la lista de tareas (workers) ---
        tasks = []
        for i in range(1, NUM_PARALLEL_SESSIONS + 1):
            tasks.append(
                run_worker(
                    worker_id=i, 
                    browser=browser, 
                    lock=lock, 
                    url_a_visitar=url_a_visitar
                )
            )
        
        try:
            # --- 3. Ejecutamos todas las tareas en paralelo ---
            print(f"[INFO] Lanzando {len(tasks)} workers. Presiona Ctrl+C para detener.")
            await asyncio.gather(*tasks)
        
        except KeyboardInterrupt:
            # Permite detener el bucle con Ctrl+C en la terminal
            print("\n[INFO] Deteniendo workers (Ctrl+C)...")
        
        finally:
            # --- 4. Limpieza final ---
            print("[INFO] Cerrando el navegador.")
            await browser.close()
            print("[INFO] Script finalizado.")

# --- Punto de entrada estándar para scripts asíncronos ---
# ... (sin cambios) ...
if __name__ == "__main__":
    # asyncio.run() se encarga de iniciar y cerrar el bucle de eventos
    asyncio.run(main())


