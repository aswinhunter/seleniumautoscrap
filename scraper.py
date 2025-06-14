

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from selenium.webdriver.chrome.options import Options

import time
import firebase_admin
from firebase_admin import credentials, firestore


try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Successfully connected to Firebase.")
except Exception as e:
    print(f"FIREBASE ERROR: Could not connect. Error: {e}")
    exit()


chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox") 
chrome_options.add_argument("--disable-dev-shm-usage") 
chrome_options.add_argument("--window-size=1920,1080") 


service = Service()
driver = webdriver.Chrome(service=service, options=chrome_options)
print("WebDriver initialized in headless mode.")



website = 'https://enam.gov.in/web/dashboard/trade-data'
driver.get(website)
time.sleep(8) 

try:
    driver.find_element(By.XPATH, '//option[@value="509"]').click()
    print("Clicked on Daily Prices")
    driver.find_element(By.XPATH, '//input[@value="Refresh"]').click()
    print("Clicked on Refresh")
except Exception as e:
    print(f"Error during initial setup: {e}")

time.sleep(5)

all_commodity_data = []
n = 1

while n <= 18:
    print(f"--- Processing Page {n} ---")
    if n > 1:
        try:
            dropdown_box = driver.find_element(By.ID, "min_max_no_of_list")
            dropdown_box.click()
            time.sleep(1)
            page_option_to_click = driver.find_element(By.XPATH, f"//select[@id='min_max_no_of_list']/option[@value='{n}']")
            page_option_to_click.click()
            time.sleep(3)
        except Exception as e:
            print(f"Error clicking on page {n}, stopping scrape. Error: {e}")
            break
    
    rows = driver.find_elements(By.XPATH, "//div[@class='grid-container']//tbody/tr")
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, 'td')
        if len(cells) == 10:
            try:
                commodity_info = {
                    'state': cells[0].text, 'apmc': cells[1].text, 'commodity': cells[2].text,
                    'min_price': int(cells[3].text.replace(',', '')), 'modal_price': int(cells[4].text.replace(',', '')), 'max_price': int(cells[5].text.replace(',', '')),
                    'commodity_arrivals': int(cells[6].text.replace(',', '')), 'commodity_traded': int(cells[7].text.replace(',', '')),
                    'unit': cells[8].text, 'date': cells[9].text,
                }
                all_commodity_data.append(commodity_info)
            except ValueError:
                print(f"Skipping row due to data conversion error: {row.text}")

    n += 1

print(f"\nScraping complete. Found {len(all_commodity_data)} total records.")
driver.quit() 
if all_commodity_data:
    try:
        doc_ref = db.collection('daily_prices').document('latest')
        doc_ref.set({
            'updated_at': firestore.SERVER_TIMESTAMP,
            'commodities': all_commodity_data
        })
        print("SUCCESS: Data has been uploaded to Firebase.")
    except Exception as e:
        print(f"ERROR: Failed to upload data to Firebase. {e}")
else:
    print("WARNING: No data was scraped, so nothing was uploaded to Firebase.")

