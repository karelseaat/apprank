#!/usr/bin/env python

import sys
sys.path.append('..')


import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dateutil.relativedelta import relativedelta
import datetime
from models import User, Rankapp, Searchkey, SearchRank
from config import make_session


session = make_session()
olddate = (datetime.datetime.now() - relativedelta(weeks=52))
results = session.query(Rankapp).filter(SearchRank.ranktime < olddate).delete()
session.commit()
session.close()
