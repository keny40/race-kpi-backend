from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

opts = Options()
opts.add_argument("--headless=new")

driver = webdriver.Chrome(
    service=Service(r"C:\chromedriver\chromedriver.exe"),
    options=opts,
)

driver.get("https://www.google.com")
print(driver.title)
driver.quit()
