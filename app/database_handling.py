
from flask import Flask
import hashlib, os
from flask_sqlalchemy import SQLAlchemy

application = Flask(__name__)
application.config.from_object('config')

alch_db = SQLAlchemy(application)

def get_x_randoms(x):
    return str(hashlib.md5(os.urandom(64).encode("base-64")).hexdigest())[:x]

# take in raw password, return it hashed
def hash_pass(rawpassword):
    h = hashlib.md5(rawpassword.encode())
    return str(h.hexdigest())

class User_alch(alch_db.Model):
    __tablename__="users"
    # TODO: what if they leave firstname/lastname/etc blank?  Should check for valid text in each one in __init__.py
    firstname = alch_db.Column(alch_db.String(50), nullable=False)
    lastname = alch_db.Column(alch_db.String(50), nullable=False)
    username = alch_db.Column(alch_db.String(50), primary_key=True, nullable=False)
    password = alch_db.Column(alch_db.String(80), nullable=False)
    salt = alch_db.Column(alch_db.String(80), nullable=False)
    # TODO: refactor the CSVs with SQLAlchemy "relationship"s
    ownedEventsCSV = alch_db.Column(alch_db.String(500), nullable=True)
    email = alch_db.Column(alch_db.String(80), nullable=False)
    followedEventsCSV = alch_db.Column(alch_db.String(500), nullable=True)
    verifiedEmail = alch_db.Column(alch_db.String(20), nullable=True)

    def __init__(self, firstname, lastname, username, email, rawpassword):
        super(User_alch, self).__init__()
        self.firstname = firstname
        self.lastname = lastname
        self.username = username
        self.email = email
        self.assignPassAndSalt(rawpassword)
        self.assignVerifiedEmail()
        self.ownedEventsCSV = ""
        self.followedEventsCSV = ""

    def __repr__(self):
        return '<User %r>\n\tfirstname: %r\n\tlastname: %r\n\temail: %r\n\townedevents: %r\n\tfollowedevents: %r' % (self.username, self.firstname, self.lastname, self.email, self.ownedEventsCSV, self.followedEventsCSV)

    def checkHashPass(self, rawPassIn):
        correctPass = hash_pass(rawPassIn + self.salt)
        return correctPass == self.password

    def assignPassAndSalt(self, rawPass):
        self.salt = get_x_randoms(64)
        self.password = hash_pass(rawPass+self.salt)

    def assignVerifiedEmail(self):
        self.verifiedEmail = get_x_randoms(16)

    # TODO: Refactor this with many-to-many relation between User_alch and Event_alch...
    #           Uses a secondary table with cols of users and rows of events, or vice versa
    def getListOfOwnedEventNames(self):
        urlList = self.ownedEventsCSV.split(",")
        nameList = []
        for url in urlList:
            event = Event_alch.query.filter_by(eventUrl=url).first()
            if event is not None:
                nameList.append(event.eventName)
        return nameList

    def getListOfFollowedEventNames(self):
        urlList = self.followedEventsCSV.split(",")
        nameList = []
        for url in urlList:
            event = Event_alch.query.filter_by(eventUrl=url).first()
            if event is not None:
                nameList.append(event.eventName)
        return nameList

def usernameAvail(usernameIn):
    user_count = User_alch.query.filter_by(username=usernameIn).count()
    if user_count==0:
        return True
    return False

class Event_alch(alch_db.Model):
    __tablename__="events"
    eventUrl = alch_db.Column(alch_db.String(50), primary_key=True, nullable=False)
    eventName = alch_db.Column(alch_db.String(200), nullable=False)
    eventDesc = alch_db.Column(alch_db.String(1000), nullable=True)
    followers = alch_db.Column(alch_db.String(1000), nullable=True)

    def __repr__(self):
        return '<Event Url: %r>' % self.eventUrl

    def __init__(self, url, name, desc):
        super(Event_alch, self).__init__()
        self.eventUrl = url
        self.eventName = name
        self.eventDesc = desc
        self.followers = ""

def eventUrlAvail(urlIn):
    event_count = Event_alch.query.filter_by(eventUrl=urlIn).count()
    if event_count == 0:
        return True
    return False

def eventUrlCSV_to_eventNameStrList(csvIn):
    urlList = csvIn.split(",")
    nameList = []
    for url in urlList:
        event = db_h.Event_alch.query.filter_by(eventUrl=url).first()
        if event is not None:
            nameList.append(event.eventName)
    return nameList

def is_EventUrl_in_EventUrlCSV(urlIn, csvIn):
    UrlList = csvIn.split(",")
    for url in UrlList:
        if urlIn==url:
            return True
    return False

def killDb():
    alch_db.drop_all()
    alch_db.create_all()

# def killDb():
#     connectionTemp = mysql.connect()
#     cursorTemp = connectionTemp.cursor()
#     ##########################################################
#     ###### Database notes:
#     ###### verifiedEmail is initially a 16 character random string.
#     ######        Once the user has verified their email, it is updated to "0"
#     ##########################################################
#     out = '''DROP database IF EXISTS userDb;
#     CREATE DATABASE userDb;
#     USE userDb;
#     CREATE TABLE User(
#     firstname VARCHAR(50) NOT NULL,
#     lastname VARCHAR(50) NOT NULL,
#     username VARCHAR(50) NOT NULL,
#     password VARCHAR(80) NOT NULL,
#     salt VARCHAR(80) NOT NULL,
#     ownedEventsCSV VARCHAR(500),
#     email VARCHAR(80) NOT NULL,
#     followedEventsCSV VARCHAR(500),
#     verifiedEmail VARCHAR(20),
#     primary key(username)
#     );
#     CREATE TABLE Event(
#     eventUrl VARCHAR(50) NOT NULL,
#     eventName VARCHAR(200) NOT NULL,
#     eventDesc VARCHAR(1000) NOT NULL,
#     followers VARCHAR(1000) NOT NULL,
#     primary key(eventUrl)
#     );'''
#     cursorTemp.execute(out)
#     connectionTemp.commit()
#     connectionTemp.close()
