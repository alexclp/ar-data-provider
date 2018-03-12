import os
import pickle

from time import sleep

from flask import Flask, abort, render_template, request, url_for, jsonify

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains

app = Flask(__name__)

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

driver = None

def getOrCreateWebdriver():
    chrome_options = ChromeOptions()
    chrome_options.binary_location = "/app/.apt/usr/bin/google-chrome-stable"
    # timeout after 1 second
    chrome_options.add_argument('--timeout 1000')
    global driver
    # driver = driver or webdriver.Chrome(chrome_options=chrome_options)
    driver = webdriver.Chrome(chrome_options=chrome_options)
    return driver

def guest_login():
    # give the user time to log in
    element = WebDriverWait(driver, 120).until(
        EC.presence_of_element_located((By.ID, "bGuestLogin"))
    )
    # navigate to the "view module timetable" form
    element.click()

def fill_location_form(room):
    department = "z-Informatics"
    department_dropdown = Select(driver.find_element_by_name("dlFilter"))
    search_string = department

    for option in department_dropdown.options:
        if search_string in option.text:
            option.click()
            break

    room_dropdown = Select(driver.find_element_by_name("dlObject"))
    for option in room_dropdown.options:
        if room in option.text:
            option.click()
            break
    # get a list view, not grid schedule view
    driver.find_element_by_id("RadioType_0").click()

    # submit the form
    submit = driver.find_element_by_name("bGetTimetable")
    submit.click()

def get_course_timetable():
    try:
        driver.find_element_by_id("tErrorTable")
        print(bcolors.FAIL + "[!] Error finding data" + bcolors.ENDC)
    except:
        pass
    class_title_html = driver.find_element_by_css_selector('td b')
    bs = BeautifulSoup(class_title_html.get_attribute('innerHTML'))
    class_data = {'times': []}

    class_times = driver.find_elements_by_css_selector('body table:not(:first-child) tr')
    for element in class_times:
        row = element.get_attribute('innerHTML')
        bs = BeautifulSoup(row)
        tds = bs.findAll('td')
        days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        if tds[0].text not in days:
            continue
        data = {
            "day": tds[0].text,
            "start_time": tds[1].text,
            "end_time": tds[2].text,
            "activity": tds[3].text,
            "type": tds[5].text,
            "room": tds[6].text
        }
        class_data['times'].append(data)
    print(class_data)
    return class_data

######################################################

# driver = webdriver.Chrome(chrome_options=chrome_options)
# driver.set_page_load_timeout(5)


@app.route("/timetable/<room>")
def runIt(room):
    # driver = new ChromeDriver(chrome_options=chrome_options)
    driver = getOrCreateWebdriver()
    driver.set_page_load_timeout(10)
    driver.get("https://timetables.kcl.ac.uk")

    guest_login()
    driver.execute_script("javascript:__doPostBack('LinkBtn_location','')")
    # fill_location_form("6.02")
    fill_location_form(room)
    sleep(1)
    driver.switch_to_window(driver.window_handles[-1])

    course_data = get_course_timetable()
    driver.close()
    driver.switch_to_window(driver.window_handles[0])

    driver.quit()
    
    # driver = None
    return jsonify(course_data)