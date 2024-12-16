import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from core.selenium.common import initialize_driver, close_driver
import time


def test_check_smallest_first():
    driver = initialize_driver()
    try:
        driver.get("http://localhost:5000/explore")
        results_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@value='filesize_asc']"))
        )
        driver.execute_script("arguments[0].click();", results_container)
        time.sleep(3)
        results_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "results"))
        )
        first_result = WebDriverWait(results_container, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div:nth-child(1)"))
        )
        dataset_name = first_result.text

        assert "Sample dataset 4" in dataset_name, f"Test failed: Expected 'Sample dataset 4', but got '{dataset_name}'"
        print("Test passed: The first dataset is 'Sample dataset 4'.")

    except TimeoutException:
        pytest.fail("Error: Timeout while waiting for elements to load.")
    except NoSuchElementException:
        pytest.fail("Error: Unable to locate the required element.")
    except AssertionError as e:
        pytest.fail(f"Test failed: {e}")

    finally:
        close_driver(driver)


def test_check_largest_first():
    driver = initialize_driver()
    try:
        driver.get("http://localhost:5000/explore")
        results_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@value='filesize_desc']"))
        )
        driver.execute_script("arguments[0].click();", results_container)
        time.sleep(3)
        results_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "results"))
        )
        first_result = WebDriverWait(results_container, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div:nth-child(1)"))
        )
        dataset_name = first_result.text

        assert "Sample dataset 2" in dataset_name, f"Test failed: Expected 'Sample dataset 2', but got '{dataset_name}'"
        print("Test passed: The first dataset is 'Sample dataset 2'.")

    except TimeoutException:
        pytest.fail("Error: Timeout while waiting for elements to load.")
    except NoSuchElementException:
        pytest.fail("Error: Unable to locate the required element.")
    except AssertionError as e:
        pytest.fail(f"Test failed: {e}")

    finally:
        close_driver(driver)


# Call the test function
test_check_smallest_first()
test_check_largest_first()
