#!/usr/bin/env python

#the two lines bellow, hate it !
import sys
import os
dirname = "/".join(os.path.realpath(__file__).split('/')[:-1])

sys.path.append(dirname + '/..')

from config import make_session
from config import Config
from config import domain
from models import Rankapp
import sqlalchemy
import time

from google_play_scraper import app

def check_apps():
    dbsession = make_session()
    apps = dbsession.query(sqlalchemy.distinct(Rankapp.appidstring)).all()

    appresults = []

    for aapp in apps:
        try:
            singleresult = app(aapp[0])
            # print(singleresult['size'])
            appresults.append(singleresult)
        except Exception as e:
            print(e)


        time.sleep(1)
    dbsession.close()

    return appresults

def noretozero(value):
    if value:
        return value
    else:
        return 0

def texttomin(value):
    if value and value.isdigit():
        return int(value)
    else:
        return -1


def add_to_apps(apps):
    dbsession = make_session()

    for aapp in apps:
        appresults = dbsession.query(Rankapp).filter(Rankapp.appidstring == aapp['appId']).all()

        for result in appresults:
            result.paid = not aapp['free']
            result.installs = noretozero(aapp['minInstalls'])
            result.ratings = noretozero(aapp['ratings'])
            result.installsize = noretozero(texttomin(aapp['size'].replace("M", "")))
            dbsession.add(result)
    dbsession.commit()
    dbsession.close()

if __name__ == "__main__":
    results = check_apps()
    add_to_apps(results)
