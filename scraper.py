import os
import pickle

from time import sleep

from flask import Flask, abort, render_template, request, url_for, jsonify, send_file

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
    chrome_options = Options()
    # timeout after 1 second
    chrome_options.add_argument('--timeout 1000')
    global driver
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

def get_available_computers(room):
    for element in driver.find_elements_by_class_name('campus_info'):
        square = element.get_attribute('innerHTML')
        bs = BeautifulSoup(square, "html.parser")
        full_room_name = bs.find('h2').text
        if "BH(S)" in full_room_name:
            if room in full_room_name:
                available = bs.find('strong').text
                return available
    return "Failed"

######################################################

@app.route("/pcfree/<room>")
def parse_pc_free(room):
    driver = getOrCreateWebdriver()
    driver.set_page_load_timeout(10)
    driver.get("http://pcfree.kcl.ac.uk/strand/")
    sleep(1)
    result = {"result": get_available_computers(room)}
    driver.quit()
    return jsonify(result)

@app.route("/timetable/<room>")
def parse_timetable_for(room):
    driver = getOrCreateWebdriver()
    driver.set_page_load_timeout(10)
    driver.get("https://timetables.kcl.ac.uk")

    guest_login()
    driver.execute_script("javascript:__doPostBack('LinkBtn_location','')")
    fill_location_form(room)
    sleep(1)
    driver.switch_to_window(driver.window_handles[-1])

    driver.set_window_size(1920, 900)
    driver.save_screenshot('timetable.png')
    driver.close()
    driver.switch_to_window(driver.window_handles[0])
    driver.quit()
    return send_file('timetable.png', mimetype='image/png')
