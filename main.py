# pylint: disable=C0114, C0115, C0116
import time
import os
from datetime import datetime
import yaml
from yaml.dumper import SafeDumper
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv(".env")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
SIGNIN_URL = "https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin"
SIGNIN_BUTTON_CLASS = "btn__primary--large.from__button--floating"
DIV_CLASS = "display-flex flex-row justify-space-between"
USERNAME_FIELD_ID = "username"
PASSWORD_FIELD_ID = "password"
EXPERIENCES_BUTTON_CLASS = "navigation-index-see-all-experiences"

def create_driver():
    options = Options()
    options.add_argument("--disable-search-engine-choice-screen")
    return webdriver.Chrome(options=options)

def get_raw_experiences(html):
    experiences = []
    soup = BeautifulSoup(html, "html.parser")
    ul = soup.find("ul", tabindex="-1")
    for li in ul.find_all("li"):
        one_experience = []
        div = li.find("div", class_=DIV_CLASS)
        if not div:
            continue
        spans = div.find_all('span', attrs={"aria-hidden": "true"})
        for span in spans:
            one_experience.append(span.get_text())
        experiences.append(one_experience)
    return experiences

def scraper(driver, profile_url):
    information = {}
    driver.get(SIGNIN_URL)
    username_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, USERNAME_FIELD_ID)))
    username_field.send_keys(EMAIL)
    password_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, PASSWORD_FIELD_ID)))
    password_field.send_keys(PASSWORD)
    signin_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, SIGNIN_BUTTON_CLASS)))
    signin_button.click()
    time.sleep(20)  # need to do CAPTCHA
    driver.get(profile_url)
    experiences_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, EXPERIENCES_BUTTON_CLASS)))
    experiences_button.click()
    time.sleep(3)  # todo, replace with webdriverwait
    information["experiences"] = get_raw_experiences(driver.page_source)
    return information

class IndentedSafeDumper(SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentedSafeDumper, self).increase_indent(flow, False)

def write_yaml(data, filename="experience.yaml"):
    with open(filename, 'w', encoding="utf-8") as file:
        yaml.dump(data, file, Dumper=IndentedSafeDumper, sort_keys=False,
                  default_flow_style=False, allow_unicode=True)

def parse_date_range(date_range):
    date_part, _ = date_range.split(" · ")
    start_date_str, end_date_str = date_part.split(" - ")
    start_date = datetime.strptime(start_date_str, "%b %Y").strftime("%Y-%m")
    if end_date_str.strip().lower() == "present":
        return {"from": start_date}
    else:
        end_date = datetime.strptime(end_date_str, "%b %Y").strftime("%Y-%m")
        return {"from": start_date, "to": end_date}

def parse_experiences(information):
    experiences = []
    for experience in information["experiences"]:
        result = {}
        result["company"] = experience[1]
        result["title"] = experience[0]
        result.update(parse_date_range(experience[2]))
        experiences.append(result)
    return experiences

def main():
    driver = create_driver()
    information = scraper(driver, "https://www.linkedin.com/in/hypponen/")
    write_yaml({"experience": parse_experiences(information)})
    driver.quit()


if __name__ == "__main__":
    main()
