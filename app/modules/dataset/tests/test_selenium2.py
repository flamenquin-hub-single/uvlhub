import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Configuración del driver
options = webdriver.ChromeOptions()
download_dir = os.path.join(os.path.expanduser("~"), "Descargas")
prefs = {"download.default_directory": download_dir}
options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=options)

# URL de la aplicación Flask
driver.get("http://127.0.0.1:5000")
print("URL actual:", driver.current_url)

# Imprimir el DOM generado
print("DOM generado:")
print(driver.page_source)

# Esperar a que el DOM esté completamente cargado
wait = WebDriverWait(driver, 20)
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

# Formatos de prueba
formats = {
    "Glencoe": "file4.uvl_glencoe.txt",
    "DIMACS": "file4.uvl_cnf.txt",
    "SPLOT": "file4.uvl_splot.txt",
    "ZIP": "dataset_4.zip",
}

# Función para probar un formato de descarga
def test_download(format_name, expected_file):
    try:
        print("Esperando el botón de descarga...")
        # Buscar el botón con un selector más específico
        download_button = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".btn-primary.dropdown-toggle"))
        )
        print("Botón encontrado, intentando clic.")

        # Hacer clic en el botón con ActionChains
        ActionChains(driver).move_to_element(download_button).click().perform()

        # Alternativamente, forzar clic con JavaScript
        # driver.execute_script("document.querySelector('.btn-primary.dropdown-toggle').click();")

        # Esperar que el dropdown esté visible
        print("Esperando el menú desplegable...")
        dropdown = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "dropdown-menu"))
        )

        # Haz clic en la opción correspondiente al formato
        option = dropdown.find_element(By.LINK_TEXT, format_name)
        option.click()
        print(f"Seleccionando formato: {format_name}")

        # Esperar para que la descarga se complete
        time.sleep(5)
        downloaded_files = os.listdir(download_dir)

        # Verificar si el archivo esperado está presente
        assert expected_file in downloaded_files, f"Fallo en la descarga de {format_name}"
        print(f"Prueba pasada para {format_name}: Archivo {expected_file} encontrado.")
    except Exception as e:
        driver.save_screenshot(f"debug_{format_name}.png")
        print(f"Error al probar {format_name}: {e}")
        raise

# Ejecutar las pruebas
try:
    for format_name, expected_file in formats.items():
        test_download(format_name, expected_file)
finally:
    driver.quit()
