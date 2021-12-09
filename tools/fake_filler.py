#!/usr/bin/env python

import sys
sys.path.append('..')

import random
import os
import sqlalchemy
from sqlalchemy import create_engine
from faker import Faker
from sqlalchemy.orm import sessionmaker
from models import *
import random

from config import make_session, CONNECTIONURI


if CONNECTIONURI and 'sqlite:///' in CONNECTIONURI:
    realpath = "/"+"/".join(CONNECTIONURI.split('/')[5:])
    if os.path.exists(realpath):
        os.remove(realpath)

session = make_session()


def random_user(user):
    faker = Faker()
    initiateduser = user(faker.random_int(0, 100000))
    initiateduser.fullname = faker.name()
    initiateduser.picture = faker.name()
    return initiateduser

def random_searchkeys(searchkey):
    faker = Faker()
    searchkey.searchsentence = faker.name().lower()
    for _ in range(10):
        name = faker.name()
        appidstring = faker.name()
        for _ in range(10):
            rankapp = Rankapp(name, appidstring)
            # rankapp.name = name
            # rankapp.appidstring = appidstring
            rankapp.ranktime = faker.date_between(start_date='-1y', end_date='today')
            rankapp.rank = faker.random_int(1, 600)
            searchkey.rankapps.append(rankapp)
    return searchkey

def fake_filler():
    session = make_session()
    faker = Faker()

    for _ in range(10):
        searchkey = random_searchkeys(Searchkey())
        session.add(searchkey)

    session.commit()
    session.close()

if __name__ == "__main__":
    fake_filler()
