
from flask import Flask
import hashlib, os
from flaskext.mysql import MySQL
# from app import app

# TODO: bring all mysql interaction into here, out of mainOne.py
# TODO: rename User and Event tables UserTable and EventTable to differentiate between them and classes

app = Flask(__name__)
app.config.from_object('config')

mysql = MySQL()
mysql.init_app(app)

def get_x_randoms(x):
    return str(hashlib.md5(os.urandom(64).encode("base-64")).hexdigest())[:x]

# take in raw password, return it hashed
def hash_pass(rawpassword):
    h = hashlib.md5(rawpassword.encode())
    return str(h.hexdigest())

class User:
    # pullFromDb tells the constructor to query the User table for info on the user
    #       It should be set to false if the user is not yet in the database
    # def __init__ (self, username, pullFromDb=True, password=""):
    def __init__ (self, username, pullFromDb=True):
        self.username = username
        self.firstname = ""
        self.lastname = ""
        self.email = ""
        # if password is not None:
        #     self.salt = get_x_randoms(64)
        #     self.password = hash_pass(password + self.salt)
        # else:
        self.password = ""
        self.salt = ""
        self.ownedEventsCSV = ""
        self.followedEventsCSV = ""
        self.verifiedEmail = ""
        # TODO: instead of CSVs, put these in as actual lists:
        self.ownedEventsList = []
        self.followedEventsList = []
        if pullFromDb==True:
            # TODO: probably surround this with a try/except...
            cursor = mysql.connect().cursor()
            out = "SELECT * from User where username= %s"
            #cursor.execute("SELECT * from User where username='" + self.username + "'")
            cursor.execute(out,(self.username))
            data = cursor.fetchone()
            self.firstname = data[0]
            self.lastname = data[1]
            self.password = data[3]
            self.salt = data[4]
            self.ownedEventsCSV = data[5]
            self.email = data[6]
            self.followedEventsCSV = data[7]
            self.verifiedEmail = data[8]
        # else:
        #     self.insert()

    @staticmethod
    def usernameAvail(usernameIn):
        cursor = mysql.connect().cursor()
        out = "SELECT * from User where username= %s"
        #cursor.execute("SELECT * from User where username ='" + usernameIn + "'")
        cursor.execute(out,(usernameIn))
        data = cursor.fetchone()
        if data is None:
            return True
        return False

    def checkHashPass(self, rawPassIn):
        correctPass = hash_pass(rawPassIn + self.salt)
        return correctPass == self.password

    def assignPassAndSalt(self, rawPass):
        self.salt = get_x_randoms(64)
        self.password = hash_pass(rawPass+self.salt)

    def assignVerifiedEmail(self):
        self.verifiedEmail = get_x_randoms(16)

    def getListOfOwnedEventNames(self):
        UrlList = self.ownedEventsCSV.split(",")
        nameList = []
        cursor = mysql.connect().cursor()
        for Url in UrlList:
            # TODO: fix this, obviously
            out = "SELECT * from Event where eventUrl= %s"
            #cursor.execute("SELECT * from Event where eventUrl='" + Url + "'")
            cursor.execute(out,(Url))
            data = cursor.fetchone()
            if data is not None:
                eventName = data[1]
                nameList.append(eventName)
        return nameList

    def getListOfFollowedEventNames(self):
        UrlList = self.followedEventsCSV.split(",")
        nameList = []
        cursor = mysql.connect().cursor()
        for Url in UrlList:
            # TODO: fix this, obviously
            out = "SELECT * from Event where eventUrl=%s"
            #cursor.execute("SELECT * from Event where eventUrl='" + Url + "'")
            cursor.execute(out,(Url))
            data = cursor.fetchone()
            if data is not None:
                eventName = data[1]
                nameList.append(eventName)
        return nameList

    def insert(self):
        connection = mysql.connect()
        cursor = connection.cursor()
        cmd = "INSERT INTO User values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        #out = "INSERT INTO User values(\'" + self.firstname + "\',\'" + self.lastname + "\',\'" + self.username + "\',\'" + self.password + "\',\'" + self.salt + "\',\'" + self.getOwnedEventsCSV() + "\',\'" + self.email + "\',\'" + self.getFollowedEventsCSV() + "\',\'" + self.verifiedEmail + "\')"
        #send = mysql.escape(out)
        cursor.execute(cmd, (self.firstname,self.lastname,self.username,self.password,self.salt,self.getOwnedEventsCSV(),self.email,self.getFollowedEventsCSV(),self.verifiedEmail))
        #cursor.execute(out)
        connection.commit()

    # def update(self, attribute, value):
    #     # TODO: this doesn't update the user object, just its entry in the table
    #     cursor = mysql.connect().cursor()
    #     out = toreturn = "UPDATE User SET " + attribute + "='" + value + "' WHERE username='" + self.username + "'"
    def updateFirstname(self):
        connection = mysql.connect()
        cursor = connection.cursor()
        #out = "UPDATE User SET firstname='" + self.firstname + "' WHERE username='" + self.username + "'"
        out = "UPDATE User SET firstname=%s WHERE username=%s"
        cursor.execute(out,(self.firstname,self.username))
        connection.commit()
    def updateLastname(self):
        connection = mysql.connect()
        cursor = connection.cursor()
        #out = "UPDATE User SET lastname='" + self.lastname + "' WHERE username='" + self.username + "'"
        out = "UPDATE User SET lastname=%s WHERE username=%s"
        cursor.execute(out,(self.lastname,self.username))
        connection.commit()
    def updateEmail(self):
        connection = mysql.connect()
        cursor = connection.cursor()
       # out = "UPDATE User SET email='" + self.email + "' WHERE username='" + self.username + "'"
        out = "UPDATE User SET email=%s WHERE username=%s"
        cursor.execute(out, (self.email,self.username))
        connection.commit()
    def updateVerifiedemail(self):
        connection = mysql.connect()
        cursor = connection.cursor()
        #out = "UPDATE User SET verifiedEmail='" + self.verifiedEmail + "' WHERE username='" + self.username + "'"
        out = "UPDATE User SET verifiedEmail=%s WHERE username=%s"
        cursor.execute(out,(self.verifiedEmail,self.username))
        connection.commit()

    def appendToOwnedEventsCSV(self, newEventUrl):
        self.ownedEventsCSV = self.ownedEventsCSV + newEventUrl + ","
        connection = mysql.connect()
        cursor = connection.cursor()
        #out = "UPDATE User SET ownedEventsCSV='" + self.ownedEventsCSV + "' WHERE username='" + self.username + "'"
        out = "UPDATE User SET ownedEventsCSV=%s WHERE username=%s"
        cursor.execute(out,(self.ownedEventsCSV,self.username))
        connection.commit()
    def appendToFollowedEventsCSV(self, newEventUrl):
        self.followedEventsCSV = self.followedEventsCSV + newEventUrl + ","
        connection = mysql.connect()
        cursor = connection.cursor()
        #out = "UPDATE User SET followedEventsCSV='" + self.followedEventsCSV + "' WHERE username='" + self.username + "'"
        out = "UPDATE User SET followedEventsCSV=%s WHERE username=%s"
        cursor.execute(out,(self.followedEventsCSV,self.username))
        connection.commit()

    # TODO: to be implemented when "/deleteEvent" goes live:
    # def deleteFromOwnedEventsCSV(self, deleteEventUrl):
    #     cursor = mysql.connect().cursor()
    #

    # TODO: create the verifiedEmail string in this script, not __init__.py

    # TODO: need way to add to these via the CSV or something...
    #           Maybe admit defeat on having the lists and work with CSVs?
    def getOwnedEventsCSV(self):
        toreturn = ""
        for event in self.ownedEventsList:
            toreturn = toreturn + ","
        return toreturn

    def getFollowedEventsCSV(self):
        toreturn = ""
        for event in self.followedEventsList:
            toreturn = toreturn + ","
        return toreturn

    def printUser(self):
        print "firstname: " + self.firstname + "\nlastname: " + self.lastname + "\nusername: " + self.username + "\nemail: " + self.email + "\nownedEvents: " + self.ownedEventsCSV + "\nfollowedEvents: " + self.followedEventsCSV

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
    connectionTemp = mysql.connect()
    cursorTemp = connectionTemp.cursor()
    ##########################################################
    ###### Database notes:
    ###### verifiedEmail is initially a 16 character random string.
    ######        Once the user has verified their email, it is updated to "0"
    ##########################################################
    out = '''DROP database IF EXISTS userDb;
    CREATE DATABASE userDb;
    USE userDb;
    CREATE TABLE User(
    firstname VARCHAR(50) NOT NULL,
    lastname VARCHAR(50) NOT NULL,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(80) NOT NULL,
    salt VARCHAR(80) NOT NULL,
    ownedEventsCSV VARCHAR(500),
    email VARCHAR(80) NOT NULL,
    followedEventsCSV VARCHAR(500),
    verifiedEmail VARCHAR(20),
    primary key(username)
    );
    CREATE TABLE Event(
    eventUrl VARCHAR(50) NOT NULL,
    eventName VARCHAR(200) NOT NULL,
    eventDesc VARCHAR(1000) NOT NULL,
    followers VARCHAR(1000) NOT NULL,
    primary key(eventUrl)
    );'''
    cursorTemp.execute(out)
    connectionTemp.commit()
    connectionTemp.close()
