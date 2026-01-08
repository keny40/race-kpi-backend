# backend/services/kra_crawler.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import os

LIST_URL = "https://race.kra.co.kr/chulmainfo/chulmaInfoList.do"


def fetch_entries_with_selenium():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    try:
        driver.get(LIST_URL)

        # 서울 1경주 예시 (첫 번째 경주 링크)
        race_link = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "table.tbl tbody tr td a")
            )
        )

        # JS 클릭 (중요)
        ActionChains(driver).move_to_element(race_link).click().perform()

        # 출전표 로딩 대기
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "table.tbl tbody tr")
            )
        )

        rows = driver.find_elements(By.CSS_SELECTOR, "table.tbl tbody tr")

        results = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 5:
                continue

            results.append({
                "horse_no": cols[0].text.strip(),
                "horse_name": cols[1].text.strip(),
                "country": cols[2].text.strip(),
                "gender": cols[3].text.strip(),
                "age": cols[4].text.strip(),
            })

        return results

    finally:
        driver.quit()


def save_csv(rows, path):
    if not rows:
        print("❌ no rows fetched")
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ saved {len(rows)} rows → {path}")


if __name__ == "__main__":
    data = fetch_entries_with_selenium()
    save_csv(data, "data/entries.csv")
