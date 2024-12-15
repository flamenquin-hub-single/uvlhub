import os
import time
import glob
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from core.selenium.common import close_driver
from core.environment.host import get_host_for_selenium_testing

DOWNLOAD_DIR = "/tmp/selenium_downloads"  # Ruta de descargas personalizada

def initialize_driver(download_dir=None):
    options = Options()
    if download_dir:
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "directory_upgrade": True
        }
        options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)
    return driver

def clean_download_folder():
    """Elimina todos los archivos previos en la carpeta de descargas."""
    if os.path.exists(DOWNLOAD_DIR):
        for file in os.listdir(DOWNLOAD_DIR):
            file_path = os.path.join(DOWNLOAD_DIR, file)
            os.remove(file_path)

def is_file_downloaded_by_extension(extension, timeout=10):
    """Verifica si un archivo con una extensión específica ha sido descargado."""
    for _ in range(timeout):
        files = glob.glob(os.path.join(DOWNLOAD_DIR, f"*.{extension}"))
        if files:
            return True
        time.sleep(1)
    return False

def test_download_datasets():
    """Prueba la descarga de datasets en diferentes formatos."""
    driver = initialize_driver(download_dir=DOWNLOAD_DIR)
    clean_download_folder()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/")
        WebDriverWait(driver, 10).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )

        # Lista de formatos y extensiones esperadas
        formats = {
            "Glencoe": "txt",
            "SPLOT": "txt",
            "DIMACS": "txt",
            "ZIP": "zip"
        }

        for format_name, file_extension in formats.items():
            # Hacer clic en el botón "Download"
            download_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@id, 'btnDownloadDropdown')]"))
            )
            ActionChains(driver).move_to_element(download_button).click().perform()

            # Seleccionar el formato del desplegable
            dropdown_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//a[contains(@onclick, \"{format_name.lower()}\")]"))
            )
            dropdown_option.click()

            # Verificar que el archivo se ha descargado por su extensión
            print(f"Esperando la descarga del archivo con extensión .{file_extension}...")
            assert is_file_downloaded_by_extension(file_extension), f"El archivo con extensión .{file_extension} no se descargó correctamente."
            print(f"El archivo con extensión .{file_extension} se descargó correctamente.")

            time.sleep(2)  # Espera breve antes de continuar

        print("Todos los archivos se descargaron correctamente. Test completado con éxito.")

    finally:
        close_driver(driver)  # Cerrar el navegador al finalizar el test

# Ejecutar el test
if __name__ == "__main__":
    test_download_datasets()