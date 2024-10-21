import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def initialize_driver():
    # Initializes the browser options
    options = webdriver.ChromeOptions()
    driver_path = ChromeDriverManager().install()

    # Initialise the browser using WebDriver Manager
    chrome_driver_binary = os.path.join(os.path.dirname(driver_path), 'chromedriver')
    service = Service(chrome_driver_binary)
    
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def close_driver(driver):
    driver.quit()
