from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from config.settings import CHROME_DRIVER_PATH, CHROME_USER_DATA_DIR, CHROME_PROFILE_DIRECTORY

def criar_driver_chrome():
    chrome_options = Options()
    
    if CHROME_USER_DATA_DIR:
        chrome_options.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
        chrome_options.add_argument(f"--profile-directory={CHROME_PROFILE_DIRECTORY}")
    
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    
    return driver