
from flask import Flask
import hashlib, os
from flaskext.mysql import MySQL
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')

alch_db = SQLAlchemy(app)

mysql = MySQL()
mysql.init_app(app)

def get_x_randoms(x):
    return str(hashlib.md5(os.urandom(64).encode("base-64")).hexdigest())[:x]

# take in raw password, return it hashed
def hash_pass(rawpassword):
    h = hashlib.md5(rawpassword.encode())
    return str(h.hexdigest())

class User_alch(alch_db.Model):
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

    # TODO: bring salt and verification stuff back in this file, out of __init__
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
        return '<User %r>' % self.username

    def checkHashPass(self, rawPassIn):
        correctPass = hash_pass(rawPassIn + self.salt)
        return correctPass == self.password

    def assignPassAndSalt(self, rawPass):
        self.salt = get_x_randoms(64)
        self.password = hash_pass(rawPass+self.salt)

    def assignVerifiedEmail(self):
        self.verifiedEmail = get_x_randoms(16)

    # TODO: FIX THIS!!!  Need to use relation between User_alch and Event_alch...
    def getListOfOwnedEventNames(self):
        return []
        # UrlList = self.ownedEventsCSV.split(",")
        # nameList = []
        # cursor = mysql.connect().cursor()
        # for Url in UrlList:
        #     # TODO: fix this, obviously
        #     out = "SELECT * from Event where eventUrl= %s"
        #     #cursor.execute("SELECT * from Event where eventUrl='" + Url + "'")
        #     cursor.execute(out,(Url))
        #     data = cursor.fetchone()
        #     if data is not None:
        #         eventName = data[1]
        #         nameList.append(eventName)
        # return nameList

    # TODO: Fix as above
    def getListOfFollowedEventNames(self):
        return []
        # UrlList = self.followedEventsCSV.split(",")
        # nameList = []
        # cursor = mysql.connect().cursor()
        # for Url in UrlList:
        #     # TODO: fix this, obviously
        #     out = "SELECT * from Event where eventUrl=%s"
        #     #cursor.execute("SELECT * from Event where eventUrl='" + Url + "'")
        #     cursor.execute(out,(Url))
        #     data = cursor.fetchone()
        #     if data is not None:
        #         eventName = data[1]
        #         nameList.append(eventName)
        # return nameList

def usernameAvail(usernameIn):
    user_count = User_alch.query.filter_by(username=usernameIn).count()
    # print data
    # if data is None:
    if user_count==0:
        # print "RETURNING TRUE"
        return True
    # print "RETURNING FALSE"
    return False

class Event_alch(alch_db.Model):
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


# def printUser(self):
#     print "firstname: " + self.firstname + "\nlastname: " + self.lastname + "\nusername: " + self.username + "\nemail: " + self.email + "\nownedEvents: " + self.ownedEventsCSV + "\nfollowedEvents: " + self.followedEventsCSV

class Event:
    # pullFromDb tells the constructor to query the Event table for info on the event
    #       It should be set to false if the event is not yet in the database
    def __init__(self, eventUrl, pullFromDb=True):
        self.eventUrl = eventUrl
        self.eventName = ""
        self.eventDesc = ""
        self.followers = ""
        self.followersList = []
        if pullFromDb==True:
            cursor = mysql.connect().cursor()
            out = "SELECT * from Event where eventUrl =%s"
            #cursor.execute("SELECT * from Event where eventUrl ='" + self.eventUrl + "'")
            cursor.execute(out,(self.eventUrl))
            data = cursor.fetchone()
            self.eventName = data[1]
            self.eventDesc = data[2]
            self.followers = data[3]

    @staticmethod
    def eventUrlAvail(urlIn):
        cursor = mysql.connect().cursor()
        out = "SELECT * from Event where eventUrl =%s"
        cursor.execute("SELECT * from Event where eventUrl ='" + urlIn + "'")
        #cursor.exectue(out,(urlIn))
        data = cursor.fetchone()
        if data is None:
            return True
        return False

    @staticmethod
    def eventUrlCSV_to_eventNameStrList(csvIn):
        urlList = csvIn.split(",")
        nameList = []
        cursor = mysql.connect().server()
        for url in urlList:
            out = "SELECT * from Event where eventUrl=%s"
            #cursor.execute("SELECT * from Event where eventUrl='" + url + "'")
            cursor.execute(out,(url))
            data = cursor.fetchone()
            if data is not None:
                eventName = data[1]
                nameList.append(eventName)
        return nameList

    @staticmethod
    def is_EventUrl_in_EventUrlCSV(urlIn, csvIn):
        # print "looking for url: " + urlIn + " in CSV: " + csvIn
        UrlList = csvIn.split(",")
        for url in UrlList:
            if urlIn==url:
                return True
        return False

    def insert(self):
        connection = mysql.connect()
        cursor = connection.cursor()
        #out = "INSERT INTO Event values(\'" + self.eventUrl + "\',\'" + self.eventName + "\',\'" + self.eventDesc + "\',\'" + self.followers + "\')"
        out = "INSERT INTO Event values(%s,%s,%s,%s)"
        cursor.execute(out,(self.eventUrl,self.eventName,self.eventDesc,self.followers))
        connection.commit()

    def getFollowersCSV(self):
        toreturn = ""
        for event in self.followersList:
            toreturn = toreturn + ","
        return toreturn

    def insertString(self):
        # toreturn = "INSERT INTO Event values('" + self.eventUrl + "', '" + self.eventName + "', '" + self.eventDesc + "','')"
        toreturn = "INSERT INTO Event values('" + self.eventUrl + "', '" + self.eventName + "', '" + self.eventDesc + "','" + self.getFollowersCSV() + "')"
        #toreturn = "INSERT INTO Event values(%s,%s,%s,%s)"
        return toreturn

    def updateString(self, attribute, value):
        toreturn = "UPDATE Event SET " + attribute + "='" + value + ",' WHERE eventUrl='" + self.eventUrl + "'"
        return toreturn

    def selectString(self, attribute):
        toreturn = "SELECT " + attribute + " from Event WHERE eventUrl='" + self.eventUrl + "'"








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
