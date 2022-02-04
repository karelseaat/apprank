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


def random_searchrank(searchrank, rank):
    faker = Faker()

    searchrank.ranktime = datetime.datetime.now() - relativedelta(weeks=rank)
    # searchrank.ranktime = faker.date_between(start_date='-1y', end_date='today')
    searchrank.rank = faker.random_int(1, 50)
    return searchrank

def random_app(app):
    faker = Faker()
    aapp = app(faker.name().lower(), faker.name().lower())
    aapp.imageurl = "/assets/img/searchrank.svg"
    aapp.paid = faker.random_int(0, 1)
    return aapp

def random_searchkeys(searchkey):
    faker = Faker()
    searchkey.searchsentence = faker.name().lower()
    searchkey.locale = 'us'
    for _ in range(10):
        name = faker.name()
        appidstring = faker.name()
        rankapp = Rankapp(name, appidstring)

    return searchkey

def fake_filler():
    session = make_session()
    faker = Faker()

    for _ in range(10):
        searchkey = random_searchkeys(Searchkey())
        for _ in range(10):
            searchapp = random_app(Rankapp)
            for rank in range(10):
                searchapp.searchranks.append(random_searchrank(SearchRank(), rank))
            searchkey.rankapps.append(searchapp)
        session.add(searchkey)

    session.commit()
    session.close()

if __name__ == "__main__":
    fake_filler()
