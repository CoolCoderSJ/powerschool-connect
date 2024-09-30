from selenium import webdriver
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from dotenv import load_dotenv
load_dotenv()
import os

def get_cookie():
    service = Service(executable_path='/home/shuchir/powerschool-connect/geckodriver')
    options = FirefoxOptions()
    options.binary_location = "/usr/bin/firefox"
    options.add_argument("--headless")
    print("INITIALIZING...")
    driver = webdriver.Firefox(options=options, service=service)
    print("DRIVER DEFINED")

    driver.set_window_size(1024, 768)
    driver.get(f"https://{os.environ['HOST']}/student/idp?_userTypeHint=student")
    print("NAVIGATING")

    wait = WebDriverWait(driver, 10)  # Wait for up to 10 seconds
    wait.until(EC.presence_of_element_located((By.ID, 'identification')))
    print("LOGIN LOADED")

    text_box = driver.find_element(By.ID, 'identification')
    text_box.send_keys(os.environ['TIGERID_USERNAME'])

    text_box = driver.find_element(By.ID, 'ember503')
    text_box.send_keys(os.environ['TIGERID_PWD'])

    driver.find_element(By.ID, 'authn-go-button').click()

    print("LOGGED IN, WAITING")

    wait = WebDriverWait(driver, 10)  # Wait for up to 10 seconds
    wait.until(EC.presence_of_element_located((By.ID, 'quickLookup')))

    cookies = driver.get_cookies()

    print("COMPLETE")
    driver.quit()
    print("QUIT")

    return cookies
