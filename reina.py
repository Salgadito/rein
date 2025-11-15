import random
from playwright.sync_api import sync_playwright, expect
import time

def run(playwright):
    browser = None # Definir browser como None para manejo de errores
    try:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page() # Pestaña principal de registro
        
        page_tempmail = None # La definimos como None para poder manejarla en 'finally'
        
        # Define una contraseña para usar en ambos campos
        contrasena = "TuClaveSegura_123!"

        url = "https://vota.reto3x.com.co/participantes/marlon-"

        # 1. Ir a la URL
        print(f"Navegando a {url}...")
        page.goto(url)
        print("Página cargada.")

        # 2. Clic en 'Votar'
        print("Haciendo clic en 'Votar'...")
        page.get_by_label("Votar").click()
        print("¡'Votar' presionado!")

        # 3. Clic en 'Confirmar'
        print("Haciendo clic en 'Confirmar'...")
        page.get_by_role("button", name="Confirmar").click()
        print("¡'Confirmar' presionado!")

        # 4. Clic en 'Registrarse'
        print("Haciendo clic en 'Registrarse'...")
        page.get_by_role("link", name="Registrarse").click()
        print("¡'Registrarse' presionado!")
        
        # --- INICIO DE LA LÓGICA DE EMAIL TEMPORAL ---
        
        try:
            # 5. Abrir pestaña de mail temporal
            print("Abriendo https://mail.tm/es/ en una nueva pestaña...")
            page_tempmail = context.new_page()
            page_tempmail.goto("https://mail.tm/es/")

            # 6. Extraer el email
            print("Esperando que se genere el email temporal...")
            email_selector = "#Dont_use_WEB_use_API_OK"
            
            email_input_element = page_tempmail.locator(email_selector)
            email_input_element.wait_for(state="visible", timeout=10000)
            
            expect(email_input_element).not_to_have_value("...", timeout=20000)
            
            email = email_input_element.input_value()
            
            if not email or email == "...":
                raise Exception("Email temporal no se pudo generar.")
                
            print(f"Email temporal obtenido: {email}")
            print("Pestaña de email temporal se mantendrá abierta.")
        
        except Exception as e:
            print(f"Error esperando email con el selector: {e}")
            if page_tempmail:
                page_tempmail.screenshot(path="error_tempmail_selector.png")
            raise e

        # --- FIN DE LA LÓGICA DE EMAIL TEMPORAL ---

        # 7. Volver a la pestaña principal y rellenar el correo
        page.bring_to_front()
        print("Rellenando el correo electrónico en el formulario...")
        page.locator("#email").fill(email) 
        print("¡Correo rellenado!")

        # 8. Clic en el primer checkmark
        print("Haciendo clic en el primer checkmark...")
        xpath_1 = "/html/body/main/div/div/div/div/div[1]/form/div[2]/div[1]/label/span"
        page.locator(f"xpath={xpath_1}").click()
        print("¡Primer checkmark presionado!")

        # 9. Clic en el segundo checkmark
        print("Haciendo clic en el segundo checkmark...")
        xpath_2 = "/html/body/main/div/div/div/div/div[1]/form/div[3]/div[1]/label/span"
        page.locator(f"xpath={xpath_2}").click()
        print("¡Segundo checkmark presionado!")

        # 10. Clic en 'Continuar' (Formulario de correo)
        print("Haciendo clic en 'Continuar'...")
        page.get_by_role("button", name="Continuar").click()
        print("¡Formulario de correo enviado!")

        # 11. Rellenar Nombre
        print("Rellenando nombre...")
        page.locator("#firstName").fill("TuNombre")
        print("¡Nombre rellenado!")

        # 12. Rellenar Apellido
        print("Rellenando apellido...")
        page.locator("#lastName").fill("TuApellido")
        print("¡Apellido rellenado!")

        # 13. Rellenar Número de Celular
        print("Rellenando número de celular...")
        page.locator("#phoneNumber").fill("3001234567")
        print("¡Celular rellenado!")

        # 14. Clic en 'Continuar' (Formulario de datos personales)
        print("Haciendo clic en 'Continuar' para enviar datos personales...")
        page.get_by_role("button", name="Continuar").click()
        print("¡Formulario de datos personales enviado! Esperando página de Contraseña...")
        
        # 15. Rellenar Contraseña
        print("Rellenando contraseña...")
        page.locator("#password").fill(contrasena)
        print("¡Contraseña rellenada!")

        # 16. Confirmar Contraseña
        print("Confirmando contraseña...")
        page.locator("#confirmPassword").fill(contrasena)
        print("¡Contraseña confirmada!")

        # 17. Clic en 'Finalizar registro'
        print("Haciendo clic en 'Finalizar registro'...")
        page.get_by_role("button", name="Finalizar registro").click()
        print("¡Contraseña enviada! Esperando página de OTP...")

        # --- INICIO DE LA LÓGICA DE VERIFICACIÓN OTP (CORREGIDA) ---

        # 18. Volver a la pestaña de email
        print("Volviendo a la pestaña de email para buscar el código...")
        page_tempmail.bring_to_front()

        # 19. Esperar y hacer clic en el email (CON BUCLE DE RECARGA)
        print("Esperando el email de 'Código de verificación' (máx 3 intentos de 20s)...")
        email_found = False
        for i in range(3): # Intentar 3 veces
            try:
                email_subject_locator = page_tempmail.get_by_text("Código de verificación")
                expect(email_subject_locator.first).to_be_visible(timeout=10000) 
                
                email_subject_locator.locator("xpath=..").first.click() 
                print("Email de verificación encontrado y abierto.")
                email_found = True
                break # Salir del bucle si se encuentra
            
            except Exception as e:
                print(f"Intento {i+1}/3 fallido. Recargando la página de email...")
                page_tempmail.reload()
                
                try:
                    email_input_element = page_tempmail.locator("#Dont_use_WEB_use_API_OK")
                    expect(email_input_element).not_to_have_value("...", timeout=10000)
                    print("Página de email recargada.")
                except Exception as reload_e:
                    print(f"Error fatal al recargar la página de email: {reload_e}")
                    raise reload_e

        if not email_found:
            raise Exception("No se pudo encontrar el email de verificación después de 3 intentos.")

        # 20. Localizar el código
        print("Buscando el iframe del cuerpo del mensaje...")
        iframe_selector = 'iframe[id="iFrameResizer0"]'
        iframe_locator = page_tempmail.frame_locator(iframe_selector)
        
        print("Iframe encontrado. Buscando el <span> con el estilo específico...")
        css_selector = 'span[style*="font-size:26px"][style*="font-weight:700"]'
        
        code_locator = iframe_locator.locator(css_selector)
        
        # 21. Extraer el código
        expect(code_locator).to_be_visible(timeout=10000) 
        
        codigo = code_locator.text_content()
        codigo = codigo.strip() 
        
        if not (len(codigo) == 6 and codigo.isdigit()):
             raise Exception(f"El código extraído no es válido: {codigo}")
        
        print(f"Código OTP obtenido: {codigo}")
        page_tempmail.close() # Ahora sí cerramos la pestaña de email

        # 22. Volver a la pestaña de registro
        print("Volviendo a la pestaña de registro...")
        page.bring_to_front()

        # 23. Rellenar el código OTP
        print("Ingresando el código OTP...")

        for i in range(6):
            page.locator(f"#otp-input-{i}").fill(codigo[i])
            time.sleep(random.uniform(0.3, 0.8))

            print("¡Código OTP ingresado!")

        time.sleep(15) # Pequeña pausa antes de continuar
        
        # 24. Clic en 'Continuar' después del OTP
        print("Esperando que el botón 'Continuar' se active...")
        continuar_otp_button = page.get_by_role("button", name="Continuar")
        
        expect(continuar_otp_button).to_be_enabled(timeout=10000)
        
        print("Haciendo clic en 'Continuar'...")
        continuar_otp_button.click()
        print("Proceso de verificación completado.")
        time.sleep(3) # Esperar un poco a que se procese todo

        # --- (NUEVO) INICIO DE SECUENCIA DE VOTOS POST-REGISTRO ---
        print("Iniciando secuencia de votos post-registro...")
        
        # 25. Voto 1/2
        print("Voto 1/2: Esperando 2 segundos y volviendo a la página...")
        time.sleep(1)
        page.goto(url)
        page.get_by_label("Votar").click()
        page.get_by_role("button", name="Confirmar").click()
        print("¡Voto 1/2 emitido!")

        # 26. Voto 2/2
        print("Voto 2/2: Esperando 2 segundos y volviendo a la página...")
        time.sleep(1)
        page.goto(url)
        page.get_by_label("Votar").click()
        page.get_by_role("button", name="Confirmar").click()
        print("¡Voto 2/2 emitido!")
        
        # --- FIN DE SECUENCIA DE VOTOS ---
        
        print("Cerrando el navegador para este ciclo.")

    except Exception as e:
        print(f"Ocurrió un error en este ciclo: {e}")
        # Guardar capturas de pantalla si hay un error
        try:
            if page:
                page.screenshot(path="error_registro.png")
            if page_tempmail and not page_tempmail.is_closed():
                page_tempmail.screenshot(path="error_tempmail.png")
        except:
            pass # Ignora si alguna página ya estaba cerrada

    finally:
        # Cerrar el navegador al final del ciclo (haya o no error)
        if browser:
            browser.close()

# --- (NUEVO) BUCLE INFINITO ---
# Esto ejecutará la función 'run' una y otra vez.
# Cada vez que 'run' se ejecute, abrirá un navegador nuevo y lo cerrará.

with sync_playwright() as playwright:
    while True:
        print("\n" + "="*50)
        print("--- INICIANDO NUEVO CICLO DE REGISTRO Y VOTO ---")
        print("="*50 + "\n")
        
        run(playwright)
        
        print("\n" + "="*50)
        print("--- CICLO COMPLETADO. ESPERANDO 5 SEGUNDOS ANTES DE REINICIAR ---")
        print("="*50 + "\n")
        time.sleep(2) # Pequeña pausa para no saturar el servidor

