import json
from datetime import timedelta
import datetime as dt
import time
import requests
from flask import (
    Flask,
    redirect,
    request,
    url_for,
    render_template,
    flash, Response,
    session as browsersession
)

import pprint

from authlib.integrations.flask_client import OAuth

from flask_login import (
    login_required,
    login_user,
    logout_user,
    current_user,
    LoginManager
)


from flask_cachecontrol import (FlaskCacheControl, cache_for, dont_cache)
from config import (
    make_session,
    oauthconfig,
    REVIEWLIMIT,
    recaptchasecret,
    recapchasitekey,
    domain
)

from models import User, Rankapp, Searchkey
from sqlalchemy import func, desc

from lib.filtersort import FilterSort
from lib.translator import PyNalator

from colour import Color

app = Flask(
    __name__,
    static_url_path='/assets',
    static_folder = "assets",
    template_folder = "dist",
)

login_manager = LoginManager()
login_manager.setup_app(app)

app.secret_key = 'random secret223'
app.session = make_session()

app.config.from_object("config.Config")

flask_cache_control = FlaskCacheControl()
flask_cache_control.init_app(app)

oauth = OAuth(app)
oauth.register(**oauthconfig)
#
@app.errorhandler(401)
def unauthorized(_):
    """the error handler for unauthorised"""
    browsersession['redirect'] = request.path
    return redirect('/login')

def local_breakdown(local):
    """Will filter out the locale language from a structure"""
    if "-" in local:
        boff = local.split("-")[1]
    else:
        boff = local
    return boff.lower()

def convertToColor(s):
    value = str(s.encode().hex()[-6:])
    klont = Color(f"#{value}")
    klont.saturation = 0.6

    return klont.hex


def pagination(db_object, itemnum):
    """it does the pagination for db results"""
    pagenum = 0
    if 'pagenum' in request.args and request.args.get('pagenum').isnumeric():
        pagenum = int(request.args.get('pagenum'))

    total = app.session.query(db_object).count()
    app.data['total'] = list(range(1, round_up(total/itemnum)+1))
    app.data['pagenum'] = pagenum+1, round_up(total/itemnum)
    return (
        app.
        session.
        query(db_object).
        limit(itemnum).
        offset(pagenum*itemnum).
        all()
    )

def nongetpagination(db_object, itemnum):
    """it does the pagination for db results"""
    pagenum = 0

    if 'pagenum' in request.args and request.args.get('pagenum').isnumeric():
        pagenum = int(request.args.get('pagenum'))

    total = db_object.count()
    app.data['total'] = list(range(1, round_up(total/itemnum)+1))
    app.data['pagenum'] = pagenum+1, round_up(total/itemnum)
    return db_object.limit(itemnum).offset(pagenum*itemnum)
#
@login_manager.user_loader
def load_user(userid):
    """we need this for authentication"""
    return app.session.query(User).filter(User.googleid == userid).first()

@app.before_request
def before_request_func():
    """do this before any request"""
    if isinstance(current_user, User) and current_user.locale:
        app.pyn = PyNalator(localename=current_user.locale, subdir="translations")
    else:
        app.pyn = PyNalator(subdir="translations")

    app.jinja_env.globals.update(trans=app.pyn.trans)

    navigation = {

        'apprank': ('All keywords', '/all_keywords'),
        'profile': ('My profile', '/userprofile'),
        'contact': ('Contact', '/contact')
    }

    app.data = {
        'domain': domain,
        'pagename': 'Unknown',
        'user': None,
        'navigation': navigation,
        'recapchasitekey': recapchasitekey,
        'data': None,
        'logged-in': current_user.is_authenticated
    }

    app.data['currentnavigation'] = request.full_path[1:-1]


    if current_user.is_authenticated:
        app.data['user'] = {
            'fullname': current_user.fullname,
            'language': current_user.locale,
            'email': current_user.email,
            'picture': current_user.picture,
            'cancreate': False,
            'score': 0,
            'trade_credit': 0,
            'pending':  0,
        }

@app.route('/userprofile')
@cache_for(hours=12)
@login_required
def userprofile():
    """ this will show a users profile"""
    app.data['pagename'] = 'User profile'
    app.data['data'] = current_user
    app.data['userscore'] = 0
    result = render_template('userprofile.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route('/login')
@dont_cache()
def login():
    """login that will call google oauth to you can login with your gooogle account"""
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    result = google.authorize_redirect(redirect_uri)
    app.session.close()
    app.pyn.close()
    return result

@app.route("/customlogin", methods = ['POST'])
@dont_cache()
def customlogin():
    """a custom login that will be used by the locust runner, for now it is a security risk"""
    if 'beest' in request.form and request.form.get('beest') == "Lollozotoeoobnenfmnbsf":
        customuser = app.session.query(User).filter(User.googleid == 666).first()

        if not customuser:
            customuser = User(666)
            customuser.fullname = "customuser"
            app.session.add(customuser)
            app.session.commit()

        login_user(customuser)
        app.session.close()
        app.pyn.close()
        return "success"

    app.session.close()
    app.pyn.close()
    return "fail"

@app.route('/authorize')
def authorize():
    """part of the google oauth login"""
    google_auth = oauth.create_client('google')
    google_auth.authorize_access_token()

    resp = google_auth.get('userinfo')
    user_info = resp.json()

    if user_info and 'id' in user_info and 'verified_email' in user_info:
        user = app.session.query(User).filter(User.googleid == user_info['id']).first()

        if user:
            login_user(user)
            if (user.fullname != user_info['name'] or
            user.email != user_info['email'] or
            user.locale != local_breakdown(user_info['locale'])
            or user.email != user_info['email']):
                user.fullname = user_info['name']
                user.email = user_info['email']
                user.locale = local_breakdown(user_info['locale'])
                app.session.commit()
        else:
            newuser = User(user_info['id'])
            newuser.fullname = user_info['name']
            newuser.picture = user_info['picture']
            newuser.email = user_info['email']
            newuser.locale = local_breakdown(user_info['locale'])
            app.session.add(newuser)
            app.session.commit()
            login_user(newuser)

    app.session.close()
    if 'redirect' in browsersession:
        return redirect(browsersession['redirect'])
    else:
        return redirect("/")

@app.route('/')
@cache_for(hours=12)
def index():

    app.data['pagename'] = 'Trade A Rate'
    result = render_template('index.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route("/all_keywords")
def all_keywords():
    results = app.session.query(Searchkey).all()

    app.data['data'] = results

    result = render_template('alltrades.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route("/add")
@login_required
def add_it():
    return "lel"

@app.route("/rankapp/<searchkey>")
@dont_cache()
@login_required
def rankapp(searchkey):
    """ dit gaat veel dingen doen, het laten zien van de grafieken, ook displayen van de zoek bar het gaat ook een zoekterm opslaan als je een nieuwe invoert"""

    searchkey = searchkey.strip().lower()

    results = app.session.query(Rankapp).join((Searchkey, Rankapp.searchkeys)).filter(Searchkey.searchsentence == searchkey).all()


    if results:
        labels = results[0].first_rank_plus_twelfe()
    else:
        labels = []


    app.data['searchkey'] = searchkey
    app.data['labels'] = labels
    if not results:
        search = Searchkey()
        search.searchsentence = searchkey
        search.user = current_user
        app.session.add(search)
        app.session.commit()
        app.data['data'] = []
    else:
        app.data['data'] = [{'stuff': x.get_ranks(),'name': x.name, 'color': convertToColor(x.name)} for x in results]

    result = render_template('rankapp.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result
