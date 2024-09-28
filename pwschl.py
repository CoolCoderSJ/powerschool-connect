import requests
from get_cookie import get_cookie
from bs4 import BeautifulSoup
import uuid

from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.query import Query

from dotenv import load_dotenv
load_dotenv()
import os

import contiguity
cg = contiguity.login(os.environ['CONTIGUITY_KEY'])

client = Client()
client.set_endpoint("https://appwrite.shuchir.dev/v1")
client.set_project(os.environ['APPWRITE_ID'])
client.set_key(os.environ['APPWRITE_KEY'])
db = Databases(client)

r = requests.get(os.environ['KUMA_PUSH'])

cookies = get_cookie()
cookieDict = {}
for cookie in cookies:
    cookieDict[cookie['name']] = cookie['value']
r = requests.get(f"https://{os.environ['HOST']}/guardian/home.html", cookies=cookieDict)
html = r.text


from selenium import webdriver
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

service = Service(executable_path='/home/shuchir/powerschool-connect/geckodriver')

options = FirefoxOptions()
options.add_argument("--headless")
driver = webdriver.Firefox(options=options, service=service)
print("DRIVER DEFINED") 

driver.set_window_size(1024, 768)
driver.get(f"https://{os.environ['HOST']}/student/idp?_userTypeHint=student")
print("NAVIGATING")

for cookie in cookies:
    driver.add_cookie({
        'name': cookie['name'],
        'value': cookie['value'],
        'path': cookie.get('path', '/'),
        'domain': cookie.get('domain', os.environ['HOST']),
        'secure': cookie.get('secure', False),
        'httpOnly': cookie.get('httpOnly', False),
        'sameSite': cookie.get('sameSite', 'None')
    })
print("COOKIES SET")

def getGrades(url):
    assignments = []
    driver.get(url)
    score_table = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'scoreTable'))
    )
    rows = score_table.find_elements(By.TAG_NAME, 'tr')[1:-1]
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, 'td')
        try:
            print(cells[2].text, end=" -- ")
            print(cells[10].text)
            assignment = {}
            try: given = float(cells[10].text.split("/")[0])
            except: given = -1

            try: total = float(cells[10].text.split("/")[1])
            except: total = -1

            assignment['name'] = cells[2].text
            assignment['score'] = given
            assignment['total'] = total
            assignment['id'] = row.get_attribute('id')
            assignments.append(assignment)
        except:
            print("No assignments found.")
    return assignments


uuidMap = db.list_documents("meta", "classes")['documents']

soup = BeautifulSoup(html, 'html.parser')
element = soup.find(id='quickLookup')
table = element.find('table')
rows = table.find_all('tr')[2:-1]
for row in rows:
    tds = row.find_all('td')
    className = tds[11].text.split('Email')[0]
    print(className)

    try:
        class_ = next(item for item in uuidMap if item['name'] == className)
    except:
        class_ = {
            "name": className,
            "uuid": str(uuid.uuid4())
        }
        db.create_document("meta", "classes", "unique()", class_)
        uuidMap.append(class_)

    url = f"https://{os.environ['HOST']}/guardian/" + tds[12].find('a')['href']
    print(url)
    assignments = getGrades(url)
    print("---")

    colls = db.list_collections("grades")['collections']
    try:
        collection = next(item for item in colls if item['$id'] == class_['uuid'])
    except:
        db.create_collection("grades", class_['uuid'], class_['name'])
        db.create_string_attribute("grades", class_['uuid'], "id", 99, False)
        db.create_string_attribute("grades", class_['uuid'], "name", 200, False)
        db.create_float_attribute("grades", class_['uuid'], "score", False)
        db.create_float_attribute("grades", class_['uuid'], "total", False)
    
    dbAll = db.list_documents("grades", class_['uuid'], [Query.limit(100)])['documents']

    localAssignments = assignments.copy()
    for a in assignments:
        if a['score'] < 0 or a['total'] < 0:
            localAssignments.remove(a)

    try:
        percentTotal = round(sum([a['score'] for a in localAssignments]) / sum([a['total'] for a in localAssignments]) * 100)
    except:
        percentTotal = "--"

    for assignment in assignments:
       try:
            doc = db.get_document("grades", class_['uuid'], assignment['id'])
            if doc['score'] != assignment['score']:
                cg.send.text({
                    "to": os.environ['PHONE_NUM'], 
                    "message": f"Updated assignment in {class_['name']}: {assignment['name']}.\nScore: {assignment['score']}/{assignment['total']}\nClass Grade: {percentTotal}%"
                })
            if doc['total'] != assignment['total']:
                cg.send.text({
                    "to": os.environ['PHONE_NUM'], 
                    "message": f"Updated assignment in {class_['name']}: {assignment['name']}.\nScore: {assignment['score']}/{assignment['total']}\nClass Grade: {percentTotal}%"
                })
            db.update_document("grades", class_['uuid'], assignment['id'], assignment)
       except:
            db.create_document("grades", class_['uuid'], assignment['id'], assignment)
            cg.send.text({
                "to": os.environ['PHONE_NUM'], 
                "message": f"New assignment in {class_['name']}: {assignment['name']}.\nScore: {assignment['score']}/{assignment['total']}\nClass Grade: {percentTotal}%"
            })