import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Table, Column, ForeignKey, String, Integer, Boolean, Date
from sqlalchemy_utils import get_hybrid_properties
from sqlalchemy.ext.hybrid import hybrid_property


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
    Column('user_id', ForeignKey('users.id'), primary_key=True),
    Column('searchkey_id', ForeignKey('searchkey.id'), primary_key=True)
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
    Column('rankingapp_id', ForeignKey('rankingapp.id'), primary_key=True),
    Column('searchkey_id', ForeignKey('searchkey.id'), primary_key=True)
)

class SearchRank(DictSerializableMixin):
    __tablename__ = 'searchrank'
    id = Column(Integer, primary_key=True)
    rankapp = relationship("Rankapp", back_populates="searchranks")
    rankapp_id = Column(ForeignKey('rankingapp.id'), index=True)
    rank = Column(Integer)
    ranktime = Column(Date, default=datetime.datetime.utcnow)

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

    def __init__(self, name, idstring):
        self.name = name
        self.appidstring = idstring

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
