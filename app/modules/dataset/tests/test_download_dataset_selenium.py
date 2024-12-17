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

# Asegurarse de que la carpeta de descargas exista
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
    print(f"✅ Carpeta de descargas creada: {DOWNLOAD_DIR}")


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


def is_file_downloaded_by_extension(extension, timeout=20, exact=False):
    """
    Verifica si un archivo con una extensión específica ha sido descargado.

    :param extension: Extensión del archivo o patrón para búsqueda.
    :param timeout: Tiempo máximo de espera.
    :param exact: Si es True, busca archivos con nombre exacto. Si no, busca solo por extensión.
    """
    for _ in range(timeout):
        files = glob.glob(os.path.join(DOWNLOAD_DIR, f"{extension}" if exact else f"*{extension}"))
        print("Archivos actuales en la carpeta:", os.listdir(DOWNLOAD_DIR))  # Debug
        print("Coincidencias encontradas:", files)  # Debug
        if files:
            return True
        time.sleep(1)
    return False


def test_download_datasets_index():
    """Prueba la descarga de datasets desde el index en diferentes formatos."""
    driver = initialize_driver(download_dir=DOWNLOAD_DIR)
    clean_download_folder()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/")  # Página index
        WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")

        formats = {
            "Glencoe": "_glencoe.zip",
            "SPLOT": "_splot.zip",
            "DIMACS": "_dimacs.zip",
            "ZIP": ".zip"  # Validar cualquier archivo con extensión .zip
        }

        for format_name, file_extension in formats.items():
            print(f"Probando descarga para el formato: {format_name}")  # Debug
            download_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@id, 'btnDownloadDropdown')]"))
            )
            ActionChains(driver).move_to_element(download_button).click().perform()

            dropdown_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//a[contains(@onclick, \"{format_name.lower()}\") or contains(text(), 'ZIP')]"))
            )
            dropdown_option.click()

            if format_name == "ZIP":
                # Validar cualquier archivo .zip descargado
                assert is_file_downloaded_by_extension(".zip"), f"Archivo ZIP no descargado desde index."
            else:
                assert is_file_downloaded_by_extension(file_extension), f"Archivo *{file_extension} no descargado desde index."

            print(f"Archivo *{file_extension} descargado correctamente.")
            clean_download_folder()

        print("Todos los archivos se descargaron correctamente desde el index.")
    finally:
        close_driver(driver)


if __name__ == "__main__":
    test_download_datasets_index()
