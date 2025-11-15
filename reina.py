from playwright.sync_api import sync_playwright, expect
import time
import random
import string
import threading
import logging  # <--- NUEVO: Sistema de logging
import sys      # <--- NUEVO: Para enviar logs a la consola

# --- INICIO DE CONFIGURACIÓN ---
NOMBRES = [
    'Juan', 'Carlos', 'Ana', 'Maria', 'Luis', 'Jose', 'Sofia', 'Camila', 'Andres', 
    'Alejandro', 'Valentina', 'Isabella', 'David', 'Santiago', 'Laura', 'Daniela'
]
APELLIDOS = [
    'Garcia', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Perez',
    'Sanchez', 'Ramirez', 'Torres', 'Gomez', 'Diaz', 'Vasquez', 'Castro', 'Suarez'
]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0"
]
# --- Fin de Configuración ---


# --- (NUEVO) Constante para número de workers ---
NUM_WORKERS = 5 

# --- (NUEVO) Contadores globales y Lock para thread-safety ---
total_cycles_ok = 0
total_cycles_fail = 0
total_votes_ok = 0
counter_lock = threading.Lock()

# --- (NUEVO) Función para configurar el logging ---
def setup_logging():
    """Configura el logger para que escriba en archivo y consola."""
    # Formato del log
    log_formatter = logging.Formatter(
        '%(asctime)s [%(threadName)-11s] [%(levelname)-5.5s]  %(message)s'
    )
    
    # Logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO) # Nivel de log

    # Handler para el archivo 'bot_log.txt'
    file_handler = logging.FileHandler("bot_log.txt", mode='w')
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    # Handler para la consola (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)


# --- (Función 'block_ads' sin cambios) ---
def block_ads(route):
    blocked_domains = [
        "googlesyndication.com", "googleadservices.com", "googletagmanager.com",
        "google-analytics.com", "doubleclick.net", "facebook.net",
        "connect.facebook.net", "adservice.google.com",
    ]
    url = route.request.url
    if any(domain in url for domain in blocked_domains):
        try: route.abort()
        except Exception: pass
    else:
        try: route.continue_()
        except Exception: pass

# --- (MODIFICADA) Función 'generar_datos_aleatorios' con logging ---
def generar_datos_aleatorios():
    logger = logging.getLogger(__name__) # <--- Obtener el logger
    thread_name = threading.current_thread().name
    
    # 1. Generar Nombre y Apellido
    nombre = random.choice(NOMBRES)
    apellido = random.choice(APELLIDOS)
    
    # 2. Generar Contraseña
    letras_mayusculas = string.ascii_uppercase
    letras_minusculas = string.ascii_lowercase
    digitos = string.digits
    caracteres_especiales = '@$!%*?&'
    password_lista = [
        random.choice(letras_mayusculas), random.choice(letras_minusculas),
        random.choice(digitos), random.choice(caracteres_especiales)
    ]
    todos_los_caracteres = letras_mayusculas + letras_minusculas + digitos + caracteres_especiales
    for _ in range(4): 
        password_lista.append(random.choice(todos_los_caracteres))
    random.shuffle(password_lista)
    password = ''.join(password_lista)

    # 3. Generar Teléfono Aleatorio
    prefijos_validos = [str(p) for p in range(310, 322)] 
    prefijo = random.choice(prefijos_validos)
    sufijo = f"{random.randint(0, 9999999):07d}" 
    telefono = prefijo + sufijo
            
    datos = {
        "nombre": nombre, "apellido": apellido,
        "telefono": telefono, "password": password,
    }
    
    # <--- Reemplazamos print por logger.info
    logger.info(f"[{thread_name}] [Datos Generados] Usando: {nombre} {apellido}, Tel: {telefono}, Pass: {password}")
    return datos

# --- (MODIFICADA) Función 'run' con logging y conteo ---
def run():
    logger = logging.getLogger(__name__) # <--- Obtener el logger
    thread_name = threading.current_thread().name
    
    logger.info(f"[{thread_name}] --- INICIANDO NUEVO CICLO DE REGISTRO Y VOTO ---")
    
    # Variables de estado para este ciclo
    votes_in_this_cycle = 0
    cycle_succeeded = False

    with sync_playwright() as playwright:
        browser = None 
        
        datos = generar_datos_aleatorios()
        user_agent = random.choice(USER_AGENTS)
        
        logger.info(f"[{thread_name}] [User-Agent] Usando: {user_agent[:50]}...")
        
        try:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(user_agent=user_agent)
            context.route("**/*", block_ads)
            
            page = context.new_page() 
            page_tempmail = None 
            url = "https://vota.reto3x.com.co/participantes/marlon-"

            # --- (Todos los 'print' se reemplazan por 'logger.info') ---
            logger.info(f"[{thread_name}] Navegando a {url}...")
            page.goto(url)
            
            logger.info(f"[{thread_name}] Haciendo clic en 'Votar'...")
            page.get_by_label("Votar").click()

            logger.info(f"[{thread_name}] Haciendo clic en 'Confirmar'...")
            page.get_by_role("button", name="Confirmar").click()

            logger.info(f"[{thread_name}] Haciendo clic en 'Registrarse'...")
            page.get_by_role("link", name="Registrarse").click()
            
            # --- LÓGICA DE EMAIL TEMPORAL ---
            try:
                logger.info(f"[{thread_name}] Abriendo https://mail.tm/es/...")
                page_tempmail = context.new_page()
                page_tempmail.goto("https://mail.tm/es/")

                logger.info(f"[{thread_name}] Esperando que se genere el email temporal...")
                email_selector = "#Dont_use_WEB_use_API_OK"
                email_input_element = page_tempmail.locator(email_selector)
                email_input_element.wait_for(state="visible", timeout=10000)
                expect(email_input_element).not_to_have_value("...", timeout=20000)
                
                email = email_input_element.input_value()
                if not email or email == "...":
                    raise Exception("Email temporal no se pudo generar.")
                logger.info(f"[{thread_name}] Email temporal obtenido: {email}")

            except Exception as e:
                logger.error(f"[{thread_name}] Error esperando email: {e}")


            # --- RELLENADO DE FORMULARIO ---
            page.bring_to_front()
            logger.info(f"[{thread_name}] Rellenando el correo electrónico...")
            page.locator("#email").fill(email) 
            
            xpath_1 = "/html/body/main/div/div/div/div/div[1]/form/div[2]/div[1]/label/span"
            page.locator(f"xpath={xpath_1}").click()
            xpath_2 = "/html/body/main/div/div/div/div/div[1]/form/div[3]/div[1]/label/span"
            page.locator(f"xpath={xpath_2}").click()
            
            logger.info(f"[{thread_name}] Haciendo clic en 'Continuar' (email)...")
            page.get_by_role("button", name="Continuar").click()

            logger.info(f"[{thread_name}] Rellenando datos personales...")
            page.locator("#firstName").fill(datos["nombre"])
            page.locator("#lastName").fill(datos["apellido"])
            page.locator("#phoneNumber").fill(datos["telefono"])
            
            logger.info(f"[{thread_name}] Haciendo clic en 'Continuar' (datos)...")
            page.get_by_role("button", name="Continuar").click()
            
            logger.info(f"[{thread_name}] Rellenando contraseña...")
            page.locator("#password").fill(datos["password"])
            page.locator("#confirmPassword").fill(datos["password"])
            
            logger.info(f"[{thread_name}] Haciendo clic en 'Finalizar registro'...")
            page.get_by_role("button", name="Finalizar registro").click()

            # --- LÓGICA DE VERIFICACIÓN OTP ---
            logger.info(f"[{thread_name}] Volviendo a la pestaña de email para buscar el código...")
            page_tempmail.bring_to_front()

            logger.info(f"[{thread_name}] Esperando el email de 'Código de verificación'...")
            email_found = False
            for i in range(3): 
                try:
                    email_subject_locator = page_tempmail.get_by_text("Código de verificación")
                    expect(email_subject_locator.first).to_be_visible(timeout=5000) 
                    email_subject_locator.locator("xpath=..").first.click() 
                    logger.info(f"[{thread_name}] Email de verificación encontrado y abierto.")
                    email_found = True
                    break 
                except Exception:
                    logger.warning(f"[{thread_name}] Intento {i+1}/3 fallido. Recargando la página de email...")
                    page_tempmail.reload()
                    try:
                        email_input_element = page_tempmail.locator("#Dont_use_WEB_use_API_OK")
                        expect(email_input_element).not_to_have_value("...", timeout=10000)
                    except Exception as reload_e:
                        logger.error(f"[{thread_name}] Error fatal al recargar la página de email: {reload_e}")
                        raise reload_e

            if not email_found:
                raise Exception("No se pudo encontrar el email de verificación después de 3 intentos.")

            logger.info(f"[{thread_name}] Buscando el iframe del cuerpo del mensaje...")
            iframe_selector = 'iframe[id="iFrameResizer0"]'
            iframe_locator = page_tempmail.frame_locator(iframe_selector)
            css_selector = 'span[style*="font-size:26px"][style*="font-weight:700"]'
            code_locator = iframe_locator.locator(css_selector)
            
            expect(code_locator).to_be_visible(timeout=10000) 
            codigo = code_locator.text_content().strip() 
            
            if not (len(codigo) == 6 and codigo.isdigit()):
                 raise Exception(f"El código extraído no es válido: {codigo}")
            
            logger.info(f"[{thread_name}] Código OTP obtenido: {codigo}")
            page_tempmail.close()

            logger.info(f"[{thread_name}] Volviendo a la pestaña de registro...")
            page.bring_to_front()

            logger.info(f"[{thread_name}] Ingresando el código OTP...")
            for i in range(6):
                page.locator(f"#otp-input-{i}").fill(codigo[i])
            
            continuar_otp_button = page.get_by_role("button", name="Continuar")
            expect(continuar_otp_button).to_be_enabled(timeout=10000)
            
            logger.info(f"[{thread_name}] Haciendo clic en 'Continuar' (OTP)...")
            continuar_otp_button.click()
            logger.info(f"[{thread_name}] Proceso de verificación completado.")
            time.sleep(1) 

            # --- INICIO DE SECUENCIA DE VOTOS POST-REGISTRO ---
            logger.info(f"[{thread_name}] Iniciando secuencia de votos post-registro...")
            
            # 25. Voto 1/2
            logger.info(f"[{thread_name}] Voto 1/2: Esperando 1 segundo...")
            time.sleep(1)
            page.goto(url)
            page.get_by_label("Votar").click()
            page.get_by_role("button", name="Confirmar").click()
            logger.info(f"[{thread_name}] ¡Voto 1/2 emitido!")
            votes_in_this_cycle = 1 # <--- (NUEVO) Conteo de votos

            # 26. Voto 2/2
            logger.info(f"[{thread_name}] Voto 2/2: Esperando 1 segundo...")
            time.sleep(1)
            page.goto(url)
            page.get_by_label("Votar").click()
            page.get_by_role("button", name="Confirmar").click()
            logger.info(f"[{thread_name}] ¡Voto 2/2 emitido!")
            votes_in_this_cycle = 2 # <--- (NUEVO) Conteo de votos
            
            # --- (NUEVO) Si llega aquí, el ciclo fue exitoso ---
            cycle_succeeded = True

        except Exception as e:
            # <--- (MODIFICADO) Usar logger.error ---
            logger.error(f"[{thread_name}] Ocurrió un error en este ciclo: {e}", exc_info=True)
            # Guardar capturas de pantalla si hay un error


        finally:
            if browser:
                browser.close()
            
            # --- (NUEVO) Lógica de conteo al final del ciclo ---
            global total_cycles_ok, total_cycles_fail, total_votes_ok
            
            # Usar el lock para actualizar los contadores globales
            with counter_lock:
                if cycle_succeeded:
                    logger.info(f"[{thread_name}] --- CICLO EXITOSO. {votes_in_this_cycle} votos emitidos. ---")
                    total_cycles_ok += 1
                    total_votes_ok += votes_in_this_cycle
                else:
                    logger.warning(f"[{thread_name}] --- CICLO FALLIDO. 0 votos emitidos. ---")
                    total_cycles_fail += 1

            # Pausa breve antes de que el hilo termine
            time.sleep(random.randint(3, 8))


# --- (MODIFICADO) BUCLE PRINCIPAL "ORQUESTADOR" con logging ---
if __name__ == "__main__":
    # 1. Configurar el logging ANTES de crear hilos
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"--- Iniciando Orquestador con {NUM_WORKERS} workers paralelos ---")
    logger.info("--- Los logs se guardarán en 'bot_log.txt' ---")
    logger.info("--- Presiona Ctrl+C para detener el script ---")
    
    active_threads = []
    
    try:
        last_stats_report = time.time()
        
        while True:
            # 1. Limpiar hilos que ya terminaron
            active_threads = [t for t in active_threads if t.is_alive()]
            
            # 2. Si hay espacio, crear nuevos hilos
            while len(active_threads) < NUM_WORKERS:
                thread_name = f"Worker-{random.randint(100, 999)}"
                logger.info(f"[Orquestador] Capacidad: {len(active_threads)}/{NUM_WORKERS}. Iniciando {thread_name}...")
                
                thread = threading.Thread(target=run, name=thread_name)
                thread.daemon = True 
                thread.start()
                active_threads.append(thread)
                time.sleep(random.uniform(1.0, 3.0)) 
            
            # 3. (NUEVO) Reportar estadísticas cada 10 segundos
            current_time = time.time()
            if current_time - last_stats_report > 10:
                with counter_lock:
                    logger.info("="*60)
                    logger.info(f"[ESTADÍSTICAS] Ciclos OK: {total_cycles_ok} | Ciclos Fallidos: {total_cycles_fail} | Votos Totales: {total_votes_ok}")
                    logger.info("="*60)
                last_stats_report = current_time

            time.sleep(1) 

    except KeyboardInterrupt:
        logger.info("\n--- Interrupción de teclado detectada. Saliendo... ---")
