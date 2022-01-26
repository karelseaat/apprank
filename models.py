import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Table, Column, ForeignKey, String, Integer, Boolean, Date, DateTime
from sqlalchemy_utils import get_hybrid_properties
from sqlalchemy.ext.hybrid import hybrid_property

from dateutil.relativedelta import relativedelta


Base = declarative_base(name="Base")
metadata = Base.metadata


class DictSerializableMixin(Base):
    __abstract__ = True

    def _asdict(self):
        """will return a query and its props in dict form"""
        result = {}

        for key in self.__mapper__.c.keys() + list(get_hybrid_properties(self).keys()):
            result[key] = getattr(self, key)
        return result

    def _asattrs(self, adict, afilter):
        """will return a query and its props as attrs ?"""
        for key, val in adict.items():
            if hasattr(self, key) and key in afilter:
                setattr(self, key, val)

user_search_association = Table('usersearch', Base.metadata,
    Column('user_id', ForeignKey('users.id')),
    Column('searchkey_id', ForeignKey('searchkey.id'))
)

class User(DictSerializableMixin):
    """Users with names emails google ids etc"""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    fullname = Column(String(64))
    picture = Column(String(256))
    email = Column(String(256))
    locale = Column(String(3))
    googleid = Column(String(256), nullable=False)

    searchkeys = relationship(
        "Searchkey",
        secondary=user_search_association,
        back_populates="users"
    )

    def __init__(self, googleid):
        self.googleid = googleid

    def is_active(self):
        """user is alwais active"""
        return True

    def get_id(self):
        """it is needed for login functionality, yes it will return the id"""
        return self.googleid

    def is_authenticated(self):
        """yes"""
        return True

    def is_anonymous(self):
        """never"""
        return False

search_app_association = Table('searchapp', Base.metadata,
    Column('rankingapp_id', ForeignKey('rankingapp.id')),
    Column('searchkey_id', ForeignKey('searchkey.id'))
)

class SearchRank(DictSerializableMixin):
    __tablename__ = 'searchrank'
    id = Column(Integer, primary_key=True)
    rankapp = relationship("Rankapp", back_populates="searchranks")
    rankapp_id = Column(ForeignKey('rankingapp.id'))
    rank = Column(Integer)
    ranktime = Column(DateTime, default=datetime.datetime.utcnow)

class Rankapp(DictSerializableMixin):
    __tablename__ = 'rankingapp'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    appidstring = Column(String(64), nullable=False)
    imageurl = Column(String(256))

    paid = Column(Boolean, default=False)
    searchkeys = relationship(
        "Searchkey",
        secondary=search_app_association,
        back_populates="rankapps"
    )

    searchranks = relationship(
        "SearchRank",
        back_populates="rankapp"
    )

    def first_rank_plus_twelfe(self):
        if self.searchranks:
            return [(self.searchranks[0].ranktime - relativedelta(weeks=i)).strftime("%d/%m/%Y") for i in range(52)]
        else:
            [(datetime.datetime.now() - relativedelta(weeks=i)).strftime("%d/%m/%Y") for i in range(52)]

    def get_first_rank(self):
        ranks = self.searchranks
        if ranks:
            return ranks[0]
        else:
            return []

    def __init__(self, name, idstring):
        self.name = name
        self.appidstring = idstring

    def get_ranks(self):
        test = [x.rank for x in self.searchranks]
        # test.reverse()
        # return test
        return test[::-1]


    def get_url(self):
        """this will get the url for an app back to the apps playstore"""
        return "https://play.google.com/store/apps/details?id=" + self.appidstring

class Searchkey(DictSerializableMixin):
    __tablename__ = 'searchkey'
    id = Column(Integer, primary_key=True)
    searchsentence = Column(String(256), nullable=False)
    rankapps = relationship(
        "Rankapp",
        secondary=search_app_association,
        back_populates="searchkeys"
    )

    users = relationship(
        "User",
        secondary=user_search_association,
        back_populates="searchkeys"
    )

    def get_first_age(self):

        if self.rankapps:
            return (datetime.datetime.now() - self.rankapps[0].get_first_rank().ranktime).days
