import os
import time
from flask import url_for
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import initialize_driver, close_driver


def get_driver_with_download_cwdir():
    # Initializes the browser options
    prefs = {
        "download.default_directory": os.getcwd(),
        "download.directory_upgrade": True,
        "download.prompt_for_download": False,
    }
    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", prefs)

    driver_path = ChromeDriverManager().install()


    # Initialise the browser using WebDriver Manager
    chrome_driver_binary = os.path.join(os.path.dirname(driver_path), 'chromedriver')
    
    service = Service(chrome_driver_binary)
    
    
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def wait_for_page_to_load(driver, timeout=4):
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )


def count_datasets(driver, host):
    driver.get(f"{host}/dataset/list")
    wait_for_page_to_load(driver)

    try:
        amount_datasets = len(driver.find_elements(By.XPATH, "//table//tbody//tr"))
    except Exception:
        amount_datasets = 0
    return amount_datasets

def has_datasets_synced(driver, host):
    driver.get(f"{host}/dataset/list")
    wait_for_page_to_load(driver)
    try:
        amount_datasets = len(driver.find_elements(By.XPATH, "//div[@class='card-body']//table//tbody//tr"))
    except Exception:
        amount_datasets = 0
    return amount_datasets

def has_datasets_unsynced(driver, host):
    driver.get(f"{host}/dataset/list")
    wait_for_page_to_load(driver)

    try:
        amount_datasets = len(driver.find_elements(By.XPATH, "//div[@class='card-body']//div[@class='card-body']//table//tbody//tr"))
    except Exception:
        amount_datasets = 0
    return amount_datasets>0

def exist_published_datasets(driver, host):
    driver.get(f"{host}/explore")
    wait_for_page_to_load(driver)
    try:
        amount_datasets = len(driver.find_element(By.ID, 'results').find_elements(By.CSS_SELECTOR, 'div.card'))
    except Exception:
        amount_datasets = 0
    return amount_datasets>0

def get_url_detalles(driver, host):
    if exist_published_datasets(driver, host):
        result = driver.find_element(By.ID, 'results').find_element(By.XPATH, '//div[@class="card"]//a').get_attribute('href')
    else:
        # Open the login page
        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)

        # Find the username and password field and enter the values
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")

        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")

        # Send the form
        password_field.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)

        if has_datasets_synced(driver, host): # tiene datasets publicados, usar esos
            result = driver.find_element(By.XPATH, "//div[@class='card-body']//table//tbody//tr//td//a").get_attribute('href')
        elif has_datasets_unsynced(driver, host): # solo tiene datasets sin publicar
            result = f"{host}" + driver.find_element(By.XPATH, "//div[@class='card-body']//div[@class='card-body']//table//tbody//tr//td//a").get_attribute('href')
        else: # No tiene datasets, crear uno
            # Count initial datasets
            initial_datasets = count_datasets(driver, host)

            # Open the upload dataset
            driver.get(f"{host}/dataset/upload")
            wait_for_page_to_load(driver)

            datos_dataset = {
                "titulo": "Titulo prueba bibtex",
                "descripcion": "Descripcion prueba bibtex",
                "tags": "tag1,tag2"
            }
            autores_dataset = [
                    {"name": "AutorBibtex0", "affiliation": "Club0","orcid":"0000-0000-0000-0000"},
                    {"name": "AutorBibtex1", "affiliation": "Club1"},
                    {"name": "AutorBibtex3", "affiliation": "Club3"}
            ]

            # Find basic info and UVL model and fill values
            title_field = driver.find_element(By.NAME, "title")
            title_field.send_keys(datos_dataset.get("titulo"))
            desc_field = driver.find_element(By.NAME, "desc")
            desc_field.send_keys(datos_dataset.get("descripcion"))
            tags_field = driver.find_element(By.NAME, "tags")
            tags_field.send_keys(datos_dataset.get("tags"))

            # Add two authors and fill
            add_author_button = driver.find_element(By.ID, "add_author")
            add_author_button.send_keys(Keys.RETURN)
            wait_for_page_to_load(driver)
            add_author_button.send_keys(Keys.RETURN)
            wait_for_page_to_load(driver)

            name_field0 = driver.find_element(By.NAME, "authors-0-name")
            name_field0.send_keys(autores_dataset[0].get("name"))
            affiliation_field0 = driver.find_element(By.NAME, "authors-0-affiliation")
            affiliation_field0.send_keys(autores_dataset[0].get("affiliation"))
            orcid_field0 = driver.find_element(By.NAME, "authors-0-orcid")
            orcid_field0.send_keys(autores_dataset[0].get("orcid"))

            name_field1 = driver.find_element(By.NAME, "authors-1-name")
            name_field1.send_keys(autores_dataset[1].get("name"))
            affiliation_field1 = driver.find_element(By.NAME, "authors-1-affiliation")
            affiliation_field1.send_keys(autores_dataset[1].get("affiliation"))

            # Obtén las rutas absolutas de los archivos
            file1_path = os.path.abspath("app/modules/dataset/uvl_examples/file1.uvl")
            file2_path = os.path.abspath("app/modules/dataset/uvl_examples/file2.uvl")

            # Subir el primer archivo
            dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
            dropzone.send_keys(file1_path)
            wait_for_page_to_load(driver)

            # Subir el segundo archivo
            dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
            dropzone.send_keys(file2_path)
            wait_for_page_to_load(driver)

            # Add authors in UVL models
            show_button = driver.find_element(By.ID, "0_button")
            show_button.send_keys(Keys.RETURN)
            add_author_uvl_button = driver.find_element(By.ID, "0_form_authors_button")
            add_author_uvl_button.send_keys(Keys.RETURN)
            wait_for_page_to_load(driver)

            name_field = driver.find_element(By.NAME, "feature_models-0-authors-2-name")
            name_field.send_keys("AutorBibtex3")
            affiliation_field = driver.find_element(By.NAME, "feature_models-0-authors-2-affiliation")
            affiliation_field.send_keys("Club3")

            # Check I agree and send form
            check = driver.find_element(By.ID, "agreeCheckbox")
            check.send_keys(Keys.SPACE)
            wait_for_page_to_load(driver)

            upload_btn = driver.find_element(By.ID, "upload_button")
            upload_btn.send_keys(Keys.RETURN)
            
            wait_for_page_to_load(driver)
            time.sleep(2)  # Force wait time

            assert driver.current_url == f"{host}/dataset/list", "Test failed!"

            # Count final datasets
            final_datasets = count_datasets(driver, host)
            assert final_datasets == initial_datasets + 2, "Test failed!"
            
            listado_unsync = driver.find_element(By.CLASS_NAME, "row") # TODO: encontrar el primer elemento de tipo tbody
            dataset_creado = listado_unsync.find_element(By.XPATH, "//table//tbody//tr")
            
            info_dataset_creado = dataset_creado.find_elements(By.TAG_NAME, "td")

            title_matches = info_dataset_creado[0].find_element(By.TAG_NAME, 'a').text==datos_dataset.get("titulo")
            desc_matches = info_dataset_creado[1].text==datos_dataset.get("descripcion")
            pub_type_matches = info_dataset_creado[2].text=="None"

            assert title_matches and desc_matches and pub_type_matches, "Test failed!"
            result = f"{host}" + info_dataset_creado[0].find_element(By.TAG_NAME, 'a').get_attribute('href')
    return result

def test_upload_dataset():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the login page
        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)

        # Find the username and password field and enter the values
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")

        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")

        # Send the form
        password_field.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)

        # Count initial datasets
        initial_datasets = count_datasets(driver, host)

        # Open the upload dataset
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)

        # Find basic info and UVL model and fill values
        title_field = driver.find_element(By.NAME, "title")
        title_field.send_keys("Title")
        desc_field = driver.find_element(By.NAME, "desc")
        desc_field.send_keys("Description")
        tags_field = driver.find_element(By.NAME, "tags")
        tags_field.send_keys("tag1,tag2")

        # Add two authors and fill
        add_author_button = driver.find_element(By.ID, "add_author")
        add_author_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)
        add_author_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)

        name_field0 = driver.find_element(By.NAME, "authors-0-name")
        name_field0.send_keys("Author0")
        affiliation_field0 = driver.find_element(By.NAME, "authors-0-affiliation")
        affiliation_field0.send_keys("Club0")
        orcid_field0 = driver.find_element(By.NAME, "authors-0-orcid")
        orcid_field0.send_keys("0000-0000-0000-0000")

        name_field1 = driver.find_element(By.NAME, "authors-1-name")
        name_field1.send_keys("Author1")
        affiliation_field1 = driver.find_element(By.NAME, "authors-1-affiliation")
        affiliation_field1.send_keys("Club1")

        # Obtén las rutas absolutas de los archivos
        file1_path = os.path.abspath("app/modules/dataset/uvl_examples/file1.uvl")
        file2_path = os.path.abspath("app/modules/dataset/uvl_examples/file2.uvl")

        # Subir el primer archivo
        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file1_path)
        wait_for_page_to_load(driver)

        # Subir el segundo archivo
        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file2_path)
        wait_for_page_to_load(driver)

        # Add authors in UVL models
        show_button = driver.find_element(By.ID, "0_button")
        show_button.send_keys(Keys.RETURN)
        add_author_uvl_button = driver.find_element(By.ID, "0_form_authors_button")
        add_author_uvl_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)

        name_field = driver.find_element(By.NAME, "feature_models-0-authors-2-name")
        name_field.send_keys("Author3")
        affiliation_field = driver.find_element(By.NAME, "feature_models-0-authors-2-affiliation")
        affiliation_field.send_keys("Club3")

        # Check I agree and send form
        check = driver.find_element(By.ID, "agreeCheckbox")
        check.send_keys(Keys.SPACE)
        wait_for_page_to_load(driver)

        upload_btn = driver.find_element(By.ID, "upload_button")
        upload_btn.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)
        time.sleep(2)  # Force wait time

        assert driver.current_url == f"{host}/dataset/list", "Test failed!"

        # Count final datasets
        final_datasets = count_datasets(driver, host)
        assert final_datasets == initial_datasets + 2, "Test failed!"

        print("Test passed!")

    finally:

        # Close the browser
        close_driver(driver)

def test_bibtex_preview():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()

        url_detalles = get_url_detalles(driver, host)
        
        # Accede a la vista de detalles del dataset
        driver.get(url_detalles)
        wait_for_page_to_load(driver)

        bibtex_resultado = []

        info_card = driver.find_element(By.CLASS_NAME, "card-body")

        titulo = info_card.find_element(By.XPATH, "//div//h1//b").text.strip()
        year = info_card.find_element(By.CSS_SELECTOR, 'p.text-secondary').text.strip().split(",")[1].strip().split(" ")[0].strip()
        
        aux_ = []
        for a_ in info_card.find_elements(By.XPATH, "//div[normalize-space(.//span)='Authors']//p"):
            a_n = a_.text.strip()
            if a_n.count("(")>0:
                aux_.append(a_n.split("(")[0].strip())
            else:
                aux_.append(a_n)
        autor = " and ".join(aux_)

        try:
            elemento_zenodo = info_card.find_element(By.XPATH, "//div[normalize-space(.//span)='Zenodo record']//a")
            howpublished = elemento_zenodo.get_attribute('href')
        except NoSuchElementException:
            howpublished = None

        note = "Accessed: {}".format(str(datetime.now().date()))
        annote = info_card.find_element(By.XPATH, "//div[normalize-space(.//span)='Description']//div//p").text.strip()

        bibtex_resultado.append("@misc{MiscUvl" + titulo.strip().replace(" ", "") + ",")
        bibtex_resultado.append("author = {" + autor + "},")
        bibtex_resultado.append("title = {" + titulo + "},")
        if howpublished:
            bibtex_resultado.append("howpublished = {" + howpublished + "},")
        bibtex_resultado.append("year = {" + year + "},")
        bibtex_resultado.append("note = {" + note + "},")
        bibtex_resultado.append("annote = {" + annote + "},")
        bibtex_resultado.append("}")

        # Obtener el boton de preview de bibtex
        bibtex_preview_btn = driver.find_element(By.XPATH, "//button[@id='bibtex_preview_btn']")
        bibtex_preview_btn.click()
        wait_for_page_to_load(driver)

        WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.ID, "bibtexContent"), "@misc{"))
        
        # COMPROBAR QUE LA PREVIEW MUESTRA EL DATASET EXPORTADO A BIBTEX CORRECTAMENTE
        contenido_bibtex = driver.find_element(By.ID, "bibtexContent").text
        assert contenido_bibtex is not None and contenido_bibtex!="None", "Test failed!"

        lineas = contenido_bibtex.splitlines()

        assert len(lineas)==len(bibtex_resultado), "Test failed!"
        
        for i in range(len(lineas)):
            assert lineas[i].strip()==bibtex_resultado[i].strip(), "Test failed!"
        print("Test passed!")

    finally:
        # Close the browser
        close_driver(driver)

def test_bibtex_copy():
    driver = initialize_driver()
    
    try:
        host = get_host_for_selenium_testing()

        url_detalles = get_url_detalles(driver, host)
        
        # Accede a la vista de detalles del dataset
        driver.get(url_detalles)
        wait_for_page_to_load(driver)

        bibtex_resultado = []

        info_card = driver.find_element(By.CLASS_NAME, "card-body")

        titulo = info_card.find_element(By.XPATH, "//div//h1//b").text.strip()
        year = info_card.find_element(By.CSS_SELECTOR, 'p.text-secondary').text.strip().split(",")[1].strip().split(" ")[0].strip()
        
        aux_ = []
        for a_ in info_card.find_elements(By.XPATH, "//div[normalize-space(.//span)='Authors']//p"):
            a_n = a_.text.strip()
            if a_n.count("(")>0:
                aux_.append(a_n.split("(")[0].strip())
            else:
                aux_.append(a_n)
        autor = " and ".join(aux_)

        try:
            elemento_zenodo = info_card.find_element(By.XPATH, "//div[normalize-space(.//span)='Zenodo record']//a")
            howpublished = elemento_zenodo.get_attribute('href')
        except NoSuchElementException:
            howpublished = None

        note = "Accessed: {}".format(str(datetime.now().date()))
        annote = info_card.find_element(By.XPATH, "//div[normalize-space(.//span)='Description']//div//p").text.strip()

        bibtex_resultado.append("@misc{MiscUvl" + titulo.strip().replace(" ", "") + ",")
        bibtex_resultado.append("author = {" + autor + "},")
        bibtex_resultado.append("title = {" + titulo + "},")
        if howpublished:
            bibtex_resultado.append("howpublished = {" + howpublished + "},")
        bibtex_resultado.append("year = {" + year + "},")
        bibtex_resultado.append("note = {" + note + "},")
        bibtex_resultado.append("annote = {" + annote + "},")
        bibtex_resultado.append("}")

        # Obtener el boton de preview de bibtex
        bibtex_preview_btn = driver.find_element(By.XPATH, "//button[@id='bibtex_preview_btn']")
        bibtex_preview_btn.click()
        wait_for_page_to_load(driver)

        WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.ID, "bibtexContent"), "@misc{"))
        
        # COMPROBAR QUE LOS DATOS SE COPIAN CORRECTAMENTE EN FORMATO BIBTEX
        bibtex_copy_btn = driver.find_element(By.XPATH, "//button[@id='bibtex_copy_btn']")
        bibtex_copy_btn.click()
        time.sleep(2)
        

        try:
            driver.find_element(By.XPATH, "//a[@href='/logout']")
        except NoSuchElementException: # No ha iniciado sesion
            driver.get(f"{host}/login")
            wait_for_page_to_load(driver)
            
            # Find the username and password field and enter the values
            email_field = driver.find_element(By.NAME, "email")
            password_field = driver.find_element(By.NAME, "password")

            email_field.send_keys("user1@example.com")
            password_field.send_keys("1234")

            # Send the form
            password_field.send_keys(Keys.RETURN)
            wait_for_page_to_load(driver)

        # Open the upload dataset
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)

        desc_field = driver.find_element(By.NAME, "desc")
        desc_field.send_keys(Keys.LEFT_CONTROL, 'v')
        
        lineas = desc_field.get_attribute("value").strip().splitlines()
        assert len(lineas)==len(bibtex_resultado), "Test failed!"
        for i in range(len(lineas)):
            assert lineas[i].strip()==bibtex_resultado[i].strip(), "Test failed!"

        print("Test passed!")

    finally:
        # Close the browser
        close_driver(driver)

def test_bibtex_download():
    driver = get_driver_with_download_cwdir()
    
    try:
        host = get_host_for_selenium_testing()

        url_detalles = get_url_detalles(driver, host)
        
        # Accede a la vista de detalles del dataset
        driver.get(url_detalles)
        wait_for_page_to_load(driver)

        bibtex_resultado = []

        info_card = driver.find_element(By.CLASS_NAME, "card-body")

        titulo = info_card.find_element(By.XPATH, "//div//h1//b").text.strip()
        year = info_card.find_element(By.CSS_SELECTOR, 'p.text-secondary').text.strip().split(",")[1].strip().split(" ")[0].strip()
        
        aux_ = []
        for a_ in info_card.find_elements(By.XPATH, "//div[normalize-space(.//span)='Authors']//p"):
            a_n = a_.text.strip()
            if a_n.count("(")>0:
                aux_.append(a_n.split("(")[0].strip())
            else:
                aux_.append(a_n)
        autor = " and ".join(aux_)

        try:
            elemento_zenodo = info_card.find_element(By.XPATH, "//div[normalize-space(.//span)='Zenodo record']//a")
            howpublished = elemento_zenodo.get_attribute('href')
        except NoSuchElementException:
            howpublished = None

        note = "Accessed: {}".format(str(datetime.now().date()))
        annote = info_card.find_element(By.XPATH, "//div[normalize-space(.//span)='Description']//div//p").text.strip()

        bibtex_resultado.append("@misc{MiscUvl" + titulo.strip().replace(" ", "") + ",")
        bibtex_resultado.append("author = {" + autor + "},")
        bibtex_resultado.append("title = {" + titulo + "},")
        if howpublished:
            bibtex_resultado.append("howpublished = {" + howpublished + "},")
        bibtex_resultado.append("year = {" + year + "},")
        bibtex_resultado.append("note = {" + note + "},")
        bibtex_resultado.append("annote = {" + annote + "},")
        bibtex_resultado.append("}")

        # Obtener el boton de preview de bibtex
        bibtex_preview_btn = driver.find_element(By.XPATH, "//button[@id='bibtex_preview_btn']")
        bibtex_preview_btn.click()
        wait_for_page_to_load(driver)

        WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.ID, "bibtexContent"), "@misc{"))
        
        # COMPROBAR QUE LOS DATOS SE DESCARGAN CORRECTAMENTE EN FORMATO BIBTEX
        bibtex_download_btn = driver.find_element(By.XPATH, "//a[@id='bibtexDownloadButton']")
        bibtex_download_btn.click()
        time.sleep(2)
        
        file_path = os.path.join(os.getcwd(), bibtex_download_btn.get_attribute('download'))

        lineas = []

        with open(file_path, 'r', encoding='utf-8') as archivo:
            lineas.extend(archivo.readlines())
        os.remove(file_path)
        
        assert len(lineas)==len(bibtex_resultado), "Test failed!"
        for i in range(len(lineas)):
            assert lineas[i].strip()==bibtex_resultado[i].strip(), "Test failed!"
        
        print("Test passed!")

    finally:
        # Close the browser
        close_driver(driver)

# Call the test function
test_upload_dataset()
test_bibtex_preview()
test_bibtex_copy()
test_bibtex_download()