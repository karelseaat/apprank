import json

import requests
from flask import (
    Flask,
    redirect,
    request,
    url_for,
    render_template,
    flash,
    session as browsersession
)
from datetime import datetime, timedelta
from cerberus import Validator
from flask_mail import Mail, Message

from authlib.integrations.flask_client import OAuth

from flask_login import (
    login_required,
    login_user,
    logout_user,
    current_user,
    LoginManager
)

import os

from flask_cachecontrol import (FlaskCacheControl, cache_for, dont_cache)
from config import (
    make_session,
    oauthconfig,
    recaptchasecret,
    recapchasitekey,
    domain
)

import statistics

from models import User, Rankapp, Searchkey, SearchRank

from lib.translator import PyNalator

from colour import Color

app = Flask(
    __name__,
    static_url_path='/assets',
    static_folder="assets",
    template_folder="dist",
)

login_manager = LoginManager()
login_manager.setup_app(app)

app.secret_key = os.getenv("SECRETKEY")
app.session = make_session()

app.config.from_object("config.Config")

flask_cache_control = FlaskCacheControl()
flask_cache_control.init_app(app)

oauth = OAuth(app)
oauth.register(**oauthconfig)

vallcontact = Validator({
    'subject': {'required': True, 'type': 'string'},
    'message': {'required': True, 'type': 'string'},
    # 'g-recaptcha-response': {'required': True}
})


@app.errorhandler(401)
def unauthorized(_):
    """the error handler for unauthorised"""
    flash('You need to login to go to that page!', 'has-text-danger')
    return redirect("/")


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
    klont.saturation = 0.9
    return klont.hex


def is_human(captcha_response):
    """ Validating recaptcha response from google server
        Returns True captcha test passed for submitted form else returns False.
    """
    payload = {'response': captcha_response, 'secret': recaptchasecret}
    response = requests.post(
        "https://www.google.com/recaptcha/api/siteverify",
        payload
    )
    response_text = json.loads(response.text)
    return response_text['success']



def round_up(num):
    """does rounding up without importing the math module"""
    return int(-(-num // 1))


def extrapagina(result, itemnum):
    pagenum = 0

    if 'pagenum' in request.args and request.args.get('pagenum').isnumeric():
        pagenum = int(request.args.get('pagenum'))

    total = len(result.all())

    app.data['total'] = list(range(1, round_up(total/itemnum)+1))
    app.data['pagenum'] = pagenum+1, round_up(total/itemnum)

    return result.limit(itemnum).offset(pagenum*itemnum)


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
        'logged-in': current_user.is_authenticated,
        'dev': os.getenv('FLASK_ENV')
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


@app.route("/developlogin")
@dont_cache()
def developlogin():
    if app.data['dev'] == "development":
        customuser = app.session.query(User).filter(User.googleid == 666).first()
        if not customuser:
            customuser = User(666)
            customuser.fullname = "developer"
            customuser.picture = "/assets/img/searchrank.svg"
            customuser.locale = "nl"
            app.session.add(customuser)
            app.session.commit()
        login_user(customuser)
        app.session.close()
        app.pyn.close()
    return redirect("/", 303)


@app.route('/authorize')
@dont_cache()
def authorize():
    """part of the google oauth login"""
    google_auth = oauth.create_client('google')
    google_auth.authorize_access_token()

    resp = google_auth.get('userinfo')
    user_info = resp.json()

    if user_info and 'id' in user_info and 'verified_email' in user_info:
        user = (app.
                session.query(User).
                filter(User.googleid == user_info['id']).
                first())

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
        return redirect(browsersession['redirect'], 303)
    else:
        return redirect("/", 303)


@app.route('/')
@dont_cache()
def index():
    app.data['pagename'] = 'App Rank'
    result = render_template('index.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result


def average(lst):
    return round(sum(lst) / len(lst))


@app.route("/app_details/<id>")
@dont_cache()
def app_details(id):

    app.data['aapp'] = app.session.query(Rankapp).filter(Rankapp.id == id).first()

    result = render_template('appdetails.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

def get_percent_labels(percent):
    return [f"{x*10}-{(x+1)*10}" for x in range(10)]

def get_percentapps(listoresults, percent, index):
    nrofapps = len(listoresults)
    percentofapps = round((nrofapps / 100) * percent)

    return listoresults[percentofapps * index:percentofapps * (index+1)]

def get_percent_adds(listoresults):
    temp = []
    for x in range(10):
        temp.append(statistics.mean([bool(x.adds) for x in get_percentapps(listoresults, 10, x)]))
    return temp

def get_percent_movie(listoresults):
    temp = []
    for x in range(10):
        temp.append(statistics.mean([bool(x.movie) for x in get_percentapps(listoresults, 10, x)]))
    return temp

def get_percent_installs(listoresults):
    temp = []
    for x in range(10):
        temp.append(statistics.mean([x.installs for x in get_percentapps(listoresults, 10, x)]))
    return temp

@app.route("/keyword_details/<id>")
@dont_cache()
def keyword_details(id):

    weekearl = datetime.now() - timedelta(days = 8)
    searchsentresult = app.session.query(Rankapp).join((Rankapp, Searchkey.rankapps)).join(SearchRank, Rankapp.searchranks).filter(SearchRank.ranktime > weekearl).filter(Searchkey.id == id).order_by(SearchRank.rank).all()

    keywors = app.session.query(Searchkey).filter(Searchkey.id == id).first()

    installs = [x.installs for x in searchsentresult  if x.installs]
    ratings = [x.ratings for x in searchsentresult  if x.ratings]
    sises = [x.installsize for x in searchsentresult if x.installsize  and x.installsize >= 0]

    app.data['labels'] = get_percent_labels(10)
    app.data['adddata'] = get_percent_adds(searchsentresult)
    app.data['moviedata'] = get_percent_movie(searchsentresult)
    app.data['installdata'] = get_percent_installs(searchsentresult)

    app.data['pagename'] = keywors.searchsentence

    app.data['installs'] = {
        'max': max(installs),
        'min': min(installs),
        'avg': average(installs)
    }
    app.data['ratings'] = {
        'max': max(ratings),
        'min': min(ratings),
        'avg': average(ratings)
    }
    app.data['sises'] = {
        'max': max(sises),
        'min': min(sises),
        'avg': average(sises)
    }

    result = render_template('keywordetails.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result


@app.route("/all_keywords")
def all_keywords():
    if 'searchkey' in request.args and request.args['searchkey']:
        searchkey = request.args['searchkey']
        results = (
                app.session.query(Searchkey).
                filter(Searchkey.searchsentence.like(f"%{searchkey}%")).
                all())
    else:
        results = app.session.query(Searchkey).all()

    app.data['data'] = results
    app.data['pagename'] = 'All keywords'

    result = render_template('allkeywords.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result


@app.route('/logout')
@dont_cache()
@login_required
def logout():
    """here you can logout, it is not used since you login via google oauth.
        So as soon as you are on the site you are loggedin"""
    browsersession['redirect'] = "/"
    logout_user()
    app.session.close()
    app.pyn.close()
    return redirect('/')


@app.route("/processadd", methods=['POST'])
@dont_cache()
@login_required
def processadd():
    """This will process the post of a form to add a trade"""

    searchkeys = request.form.get('searchkeys')
    locale = request.form.get('locale')
    if not searchkeys:
        app.session.close()
        app.pyn.close()
        flash('No search keys', 'has-text-danger')
        return redirect('/add')

    results = (
                app.
                session.
                query(Searchkey).
                filter(Searchkey.searchsentence == searchkeys.lower().strip()).
                filter(Searchkey.locale == locale).all()
                )

    if not results:
        searchkey = Searchkey()
        searchkey.searchsentence = searchkeys.lower().strip()
        searchkey.locale = locale.lower().strip()
        app.session.add(searchkey)
        app.session.commit()
        app.session.close()
        app.pyn.close()

        flash(str("Added search keys in the database come back in a week to see the rank results"), 'has-text-primary')
        return redirect('/all_keywords')

    searchkeyid = searchkey.id
    app.session.close()
    app.pyn.close()

    return redirect(f'/rankapp/{searchkeyid}')


@app.route("/add")
@login_required
def add_it():
    app.data['countrys'] = countrys()
    result = render_template('add.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result


@app.route("/rankapp/<id>")
@dont_cache()
def rankapp(id):
    """ dit gaat veel dingen doen, het laten zien van de grafieken,
    ook displayen van de zoek bar het gaat ook een zoekterm
    opslaan als je een nieuwe invoert"""

    app.data['pagename'] = 'Playstore rank history'

    app.data['searchkeyid'] = id

    # weekearl = datetime.now() - timedelta(days = 8)
    # searchsentresult = app.session.query(Rankapp).join((Rankapp, Searchkey.rankapps)).join(SearchRank, Rankapp.searchranks).filter(SearchRank.ranktime > weekearl).filter(Searchkey.id == id).order_by(SearchRank.rank).all()

    results = extrapagina(
                        app.
                        session.
                        query(Rankapp).
                        join((Searchkey, Rankapp.searchkeys)).
                        join((SearchRank, Rankapp.searchranks)).
                        filter(Searchkey.id == id).
                        order_by(SearchRank.ranktime, SearchRank.rank), 10).all()

    searchsentresult = (
        app.
        session.
        query(Searchkey).
        filter(Searchkey.id == id).
        first()
    )

    if searchsentresult:
        app.data['searchkey'] = searchsentresult.searchsentence
    app.data['rawres'] = results

    if results:
        labels = results[0].first_rank_plus_twelfe()
    else:
        labels = []
    app.data['labels'] = labels
    if results:
        app.data['data'] = [{
            "stuff": x.get_ranks(),
            "name": x.name,
            "color": convertToColor(x.name),
            "id": x.id} for x in results]
    else:
        app.data['data'] = []

    result = render_template('rankapp.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result


@app.route('/contact')
@cache_for(hours=12)
def contact():
    """Showin a contact form !"""
    app.data['pagename'] = 'Contact'
    result = render_template('contact.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result


@app.route('/processcontact', methods=['POST'])
@dont_cache()
@login_required
def processcontact():
    """this will prcess a contact form"""
    vallcontact.validate(dict(request.form))

    message = request.form.get('message')
    subject = request.form.get('subject')

    if not message:
        flash("no message?!", 'has-text-danger')
        app.session.close()
        app.pyn.close()
        return redirect('/')

    if vallcontact.errors:
        for key, val in vallcontact.errors.items():
            flash(key + ": " + val[0], 'has-text-danger')

        app.session.close()
        app.pyn.close()
        return redirect('/')

    mail = Mail(app)

    msg = Message(
        f"App rank contact form!, {subject}",
        sender='sixdots.soft@gmail.com',
        body=f"name: {current_user.fullname}\nemail: {current_user.email}\nmessage: {message}",
        recipients=['sixdots.soft@gmail.com']
    )

    mail.send(msg)

    app.session.close()
    app.pyn.close()
    flash("Message send !", 'has-text-primary')
    return redirect('/all_keywords')


def countrys():
    return {
        "AF": "Afghanistan",
        "AX": "Aland Islands",
        "AL": "Albania",
        "DZ": "Algeria",
        "AS": "American Samoa",
        "AD": "Andorra",
        "AO": "Angola",
        "AI": "Anguilla",
        "AQ": "Antarctica",
        "AG": "Antigua And Barbuda",
        "AR": "Argentina",
        "AM": "Armenia",
        "AW": "Aruba",
        "AU": "Australia",
        "AT": "Austria",
        "AZ": "Azerbaijan",
        "BS": "Bahamas",
        "BH": "Bahrain",
        "BD": "Bangladesh",
        "BB": "Barbados",
        "BY": "Belarus",
        "BE": "Belgium",
        "BZ": "Belize",
        "BJ": "Benin",
        "BM": "Bermuda",
        "BT": "Bhutan",
        "BO": "Bolivia",
        "BA": "Bosnia And Herzegovina",
        "BW": "Botswana",
        "BV": "Bouvet Island",
        "BR": "Brazil",
        "IO": "British Indian Ocean Territory",
        "BN": "Brunei Darussalam",
        "BG": "Bulgaria",
        "BF": "Burkina Faso",
        "BI": "Burundi",
        "KH": "Cambodia",
        "CM": "Cameroon",
        "CA": "Canada",
        "CV": "Cape Verde",
        "KY": "Cayman Islands",
        "CF": "Central African Republic",
        "TD": "Chad",
        "CL": "Chile",
        "CN": "China",
        "CX": "Christmas Island",
        "CC": "Cocos (Keeling) Islands",
        "CO": "Colombia",
        "KM": "Comoros",
        "CG": "Congo",
        "CD": "Congo, Democratic Republic",
        "CK": "Cook Islands",
        "CR": "Costa Rica",
        "CI": "Cote D\"Ivoire",
        "HR": "Croatia",
        "CU": "Cuba",
        "CY": "Cyprus",
        "CZ": "Czech Republic",
        "DK": "Denmark",
        "DJ": "Djibouti",
        "DM": "Dominica",
        "DO": "Dominican Republic",
        "EC": "Ecuador",
        "EG": "Egypt",
        "SV": "El Salvador",
        "GQ": "Equatorial Guinea",
        "ER": "Eritrea",
        "EE": "Estonia",
        "ET": "Ethiopia",
        "FK": "Falkland Islands (Malvinas)",
        "FO": "Faroe Islands",
        "FJ": "Fiji",
        "FI": "Finland",
        "FR": "France",
        "GF": "French Guiana",
        "PF": "French Polynesia",
        "TF": "French Southern Territories",
        "GA": "Gabon",
        "GM": "Gambia",
        "GE": "Georgia",
        "DE": "Germany",
        "GH": "Ghana",
        "GI": "Gibraltar",
        "GR": "Greece",
        "GL": "Greenland",
        "GD": "Grenada",
        "GP": "Guadeloupe",
        "GU": "Guam",
        "GT": "Guatemala",
        "GG": "Guernsey",
        "GN": "Guinea",
        "GW": "Guinea-Bissau",
        "GY": "Guyana",
        "HT": "Haiti",
        "HM": "Heard Island & Mcdonald Islands",
        "VA": "Holy See (Vatican City State)",
        "HN": "Honduras",
        "HK": "Hong Kong",
        "HU": "Hungary",
        "IS": "Iceland",
        "IN": "India",
        "ID": "Indonesia",
        "IR": "Iran, Islamic Republic Of",
        "IQ": "Iraq",
        "IE": "Ireland",
        "IM": "Isle Of Man",
        "IL": "Israel",
        "IT": "Italy",
        "JM": "Jamaica",
        "JP": "Japan",
        "JE": "Jersey",
        "JO": "Jordan",
        "KZ": "Kazakhstan",
        "KE": "Kenya",
        "KI": "Kiribati",
        "KR": "Korea",
        "KP": "North Korea",
        "KW": "Kuwait",
        "KG": "Kyrgyzstan",
        "LA": "Lao People\"s Democratic Republic",
        "LV": "Latvia",
        "LB": "Lebanon",
        "LS": "Lesotho",
        "LR": "Liberia",
        "LY": "Libyan Arab Jamahiriya",
        "LI": "Liechtenstein",
        "LT": "Lithuania",
        "LU": "Luxembourg",
        "MO": "Macao",
        "MK": "Macedonia",
        "MG": "Madagascar",
        "MW": "Malawi",
        "MY": "Malaysia",
        "MV": "Maldives",
        "ML": "Mali",
        "MT": "Malta",
        "MH": "Marshall Islands",
        "MQ": "Martinique",
        "MR": "Mauritania",
        "MU": "Mauritius",
        "YT": "Mayotte",
        "MX": "Mexico",
        "FM": "Micronesia, Federated States Of",
        "MD": "Moldova",
        "MC": "Monaco",
        "MN": "Mongolia",
        "ME": "Montenegro",
        "MS": "Montserrat",
        "MA": "Morocco",
        "MZ": "Mozambique",
        "MM": "Myanmar",
        "NA": "Namibia",
        "NR": "Nauru",
        "NP": "Nepal",
        "NL": "Netherlands",
        "AN": "Netherlands Antilles",
        "NC": "New Caledonia",
        "NZ": "New Zealand",
        "NI": "Nicaragua",
        "NE": "Niger",
        "NG": "Nigeria",
        "NU": "Niue",
        "NF": "Norfolk Island",
        "MP": "Northern Mariana Islands",
        "NO": "Norway",
        "OM": "Oman",
        "PK": "Pakistan",
        "PW": "Palau",
        "PS": "Palestinian Territory, Occupied",
        "PA": "Panama",
        "PG": "Papua New Guinea",
        "PY": "Paraguay",
        "PE": "Peru",
        "PH": "Philippines",
        "PN": "Pitcairn",
        "PL": "Poland",
        "PT": "Portugal",
        "PR": "Puerto Rico",
        "QA": "Qatar",
        "RE": "Reunion",
        "RO": "Romania",
        "RU": "Russian Federation",
        "RW": "Rwanda",
        "BL": "Saint Barthelemy",
        "SH": "Saint Helena",
        "KN": "Saint Kitts And Nevis",
        "LC": "Saint Lucia",
        "MF": "Saint Martin",
        "PM": "Saint Pierre And Miquelon",
        "VC": "Saint Vincent And Grenadines",
        "WS": "Samoa",
        "SM": "San Marino",
        "ST": "Sao Tome And Principe",
        "SA": "Saudi Arabia",
        "SN": "Senegal",
        "RS": "Serbia",
        "SC": "Seychelles",
        "SL": "Sierra Leone",
        "SG": "Singapore",
        "SK": "Slovakia",
        "SI": "Slovenia",
        "SB": "Solomon Islands",
        "SO": "Somalia",
        "ZA": "South Africa",
        "GS": "South Georgia And Sandwich Isl.",
        "ES": "Spain",
        "LK": "Sri Lanka",
        "SD": "Sudan",
        "SR": "Suriname",
        "SJ": "Svalbard And Jan Mayen",
        "SZ": "Swaziland",
        "SE": "Sweden",
        "CH": "Switzerland",
        "SY": "Syrian Arab Republic",
        "TW": "Taiwan",
        "TJ": "Tajikistan",
        "TZ": "Tanzania",
        "TH": "Thailand",
        "TL": "Timor-Leste",
        "TG": "Togo",
        "TK": "Tokelau",
        "TO": "Tonga",
        "TT": "Trinidad And Tobago",
        "TN": "Tunisia",
        "TR": "Turkey",
        "TM": "Turkmenistan",
        "TC": "Turks And Caicos Islands",
        "TV": "Tuvalu",
        "UG": "Uganda",
        "UA": "Ukraine",
        "AE": "United Arab Emirates",
        "GB": "United Kingdom",
        "US": "United States",
        "UM": "United States Outlying Islands",
        "UY": "Uruguay",
        "UZ": "Uzbekistan",
        "VU": "Vanuatu",
        "VE": "Venezuela",
        "VN": "Vietnam",
        "VG": "Virgin Islands, British",
        "VI": "Virgin Islands, U.S.",
        "WF": "Wallis And Futuna",
        "EH": "Western Sahara",
        "YE": "Yemen",
        "ZM": "Zambia",
        "ZW": "Zimbabwe"
    }
