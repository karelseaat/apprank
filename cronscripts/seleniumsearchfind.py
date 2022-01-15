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



def get_apps(searchkey):

    books = driver.find_element_by_class_name("Ktdaqe").find_elements_by_tag_name('c-wiz')

    for book in books:

        ass = book.find_elements_by_tag_name('a')
        if len(ass) >= 4:

            rankapp = Rankapp(ass[2].find_elements_by_tag_name('div')[0].get_attribute('innerHTML'), ass[0].get_attribute('href').split("=")[1])
            rankapp.imageurl = book.find_elements_by_tag_name('img')[2].get_attribute('src')
            searchrank= SearchRank()
            searchrank.rank = books.index(book)
            rankapp.searchranks.append(searchrank)
            rankapp.searchkeys.append(searchkey)
            # searchkey.rankapps.append(rankapp)

            # session.add(searchkey)
            session.add(rankapp)

    session.commit()



session = make_session()
options = Options()
options.add_argument("--headless")



results = session.query(Searchkey).all()


for result in results:
    driver = webdriver.Firefox(executable_path= r"/home/aat/Desktop/geckodriver", options=options)
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

    driver.quit()
