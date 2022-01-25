#!/usr/bin/env python

import sys
sys.path.append('..')

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import User, Rankapp, Searchkey, SearchRank
from sqlalchemy import func, desc

from config import make_session

from pyvirtualdisplay import Display
from selenium.webdriver.chrome.service import Service
import geckodriver_autoinstaller

display = Display(visible=0, size=(1024, 768))
display.start()

geckodriver_autoinstaller.install()

def get_apps(searchkey):

    try:
        books = driver.find_element_by_class_name("Ktdaqe")
        cwisses = books.find_elements_by_tag_name('c-wiz')
    except Exception as e:
        cwisses = []
        print(f"No results in search: {searchkey.searchsentence}")


    for cwsis in cwisses:

        ass = cwsis.find_elements_by_tag_name('a')
        if len(ass) >= 4:

            idstring = ass[0].get_attribute('href').split("=")[1]
            rankapp = session.query(Rankapp).filter(idstring==Rankapp.appidstring).first()
            if not rankapp or searchkey not in rankapp.searchkeys:

                rankapp = Rankapp(ass[2].find_elements_by_tag_name('div')[0].get_attribute('innerHTML'), idstring)
                rankapp.imageurl = cwsis.find_elements_by_tag_name('img')[2].get_attribute('src')

            searchrank= SearchRank()
            searchrank.rank = cwisses.index(cwsis) + 1
            if searchrank.rank <= 50:
                rankapp.searchranks.append(searchrank)
                rankapp.searchkeys.append(searchkey)
                print(f"adding {rankapp.name} to db. Search word: {searchkey.searchsentence}".encode('utf-8'))
                session.add(rankapp)

    session.commit()




session = make_session()
options = Options()
options.add_argument("--headless")


results = session.query(Searchkey).all()


for result in results:
    # ser = Service("../geckodriver", log_path="service_log_path.log")
    driver = webdriver.Firefox(options=options)
    driver.get(f'https://play.google.com/store/search?q={result.searchsentence}&c=apps')
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(5)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


    get_apps(result)


    # session.close()
    driver.quit()

display.stop()
