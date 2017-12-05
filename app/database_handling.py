
from flask import Flask, render_template
import hashlib, os, pytz
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from threading import Thread
from datetime import datetime

application = Flask(__name__)
application.config.from_object('config')

alch_db = SQLAlchemy(application)

mail = Mail(application)

def get_x_randoms(x):
    return str(hashlib.md5(os.urandom(64).encode("base-64")).hexdigest())[:x]

# take in raw password, return it hashed
def hash_pass(rawpassword):
    h = hashlib.md5(rawpassword.encode())
    return str(h.hexdigest())

# takes in an email message to send, and sends it on a separate thread so main process doesn't hang
def send_async_email(application, msg):
    with application.app_context():
        # print "about to send email"
        mail.send(msg)
        # print "sent email"

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
    resetPass = alch_db.Column(alch_db.String(80), nullable=False)

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
        self.resetPass = get_x_randoms(16)

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

    def assignResetPass(self):
        self.resetPass = get_x_randoms(16)

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

    def ownsEventUrl(self, urlIn):
        urlList = self.ownedEventsCSV.split(",")
        for url in urlList:
            if urlIn == url:
                return True
        return False

    def followsEventUrl(self, urlIn):
        urlList = self.followedEventsCSV.split(",")
        for url in urlList:
            if urlIn == url:
                return True
        return False

    def unownEvent(self, url):
        eventList = self.ownedEventsCSV.split(",")
        toSet = ""
        for event in eventList:
            if event != url:
                if event != "":
                    toSet += (event+",")
        self.ownedEventsCSV = toSet

    def unfollowEvent(self, url):
        eventList = self.followedEventsCSV.split(",")
        toSet = ""
        for event in eventList:
            if event != url:
                if event != "":
                    toSet += (event+",")
        self.followedEventsCSV = toSet

def usernameAvail(usernameIn):
    user_count = User_alch.query.filter_by(username=usernameIn).count()
    if user_count==0:
        return True
    return False

def emailAvail(emailIn):
    user_count = User_alch.query.filter_by(email=emailIn).count()
    if user_count==0:
        return True
    return False

# TODO: deleting event should look for event in all user's ownedEventsCSV (since multiple owenrs is now a thing)
class Event_alch(alch_db.Model):
    __tablename__="events"
    eventUrl = alch_db.Column(alch_db.String(50), primary_key=True, nullable=False)
    eventName = alch_db.Column(alch_db.String(200), nullable=False)
    eventDesc = alch_db.Column(alch_db.String(1000), nullable=True)
    followers = alch_db.Column(alch_db.String(1000), nullable=True)
    yesGoingCSV = alch_db.Column(alch_db.String(1000), nullable=True)
    maybeGoingCSV = alch_db.Column(alch_db.String(1000), nullable=True)
    noGoingCSV = alch_db.Column(alch_db.String(1000), nullable=True)
    password = alch_db.Column(alch_db.String(80), nullable=False)
    salt = alch_db.Column(alch_db.String(80), nullable=False)
    commentsCSV = alch_db.Column(alch_db.String(10000), nullable=True)
    ownersCSV = alch_db.Column(alch_db.String(1000), nullable=False)

    def __repr__(self):
        return '<Event Url: %r>' % self.eventUrl

    # def __init__(self, url, name, desc):
    def __init__(self, url, name, desc, username, password=None):
        super(Event_alch, self).__init__()
        self.eventUrl = url
        self.eventName = name
        self.eventDesc = desc
        self.followers = ""
        self.yesGoingCSV = ""
        self.maybeGoingCSV = ""
        self.noGoingCSV = ""
        # print password
        if password is not None and password != "":
            # print "not none: "+repr(password)
            self.assignPassAndSalt(password)
        else:
            self.password=""
            self.salt=""
        self.commentsCSV = ""
        self.ownersCSV = username+","

    def clearComments(self):
        self.commentsCSV = ""

    def addComment(self, username, comment):
        # CSV with "user~~comment~~time~$~" format
        # fullComment = username + "~~" + comment + "~~" + datetime.now().strftime('%m-%d-%Y at %H:%M')
        # print "In addComment, setting time as: " + datetime.now().strftime('%A, %b %d at %I:%M %p')
        fullComment = username + "~~" + comment + "~~" + datetime.now(pytz.timezone('US/Eastern')).strftime('%A, %b %d at %I:%M %p')

        # now = datetime.now(utc) # timezone-aware datetime.utcnow()
        # today = datetime(now.year, now.month, now.day, now.hour, now.minute, tzinfo=utc) # midnight
        # fullComment = username + "~~" + comment + "~~" + today.strftime('%A, %b %d at %I:%M %p')

        # Puts most recent comment at start of list (so at top of comments)
        self.commentsCSV = self.commentsCSV + fullComment + "~$~"
        # self.commentsCSV = fullComment + "~$~" + self.commentsCSV

    def returnComments(self):
        toReturn = []
        for rawComment in self.commentsCSV.split("~$~"):
            if rawComment is not None and rawComment!= "":
                commentArr = []
                for commentSection in rawComment.split("~~"):
                    if commentSection is not None and commentSection != "":
                        commentArr.append(commentSection)
                # TODO: what if commentArr is still []?
                toReturn.append(commentArr)
        return toReturn

    def checkHashPass(self, rawPassIn):
        if rawPassIn is None or rawPassIn=="":
            if self.password is None or self.password=="":
                return True
            return False
        correctPass = hash_pass(rawPassIn + self.salt)
        return correctPass == self.password

    def assignPassAndSalt(self, rawPass):
        self.salt = get_x_randoms(64)
        self.password = hash_pass(rawPass+self.salt)

    def unfollowUser(self, username):
        userList = self.followers.split(",")
        toSet = ""
        for user in userList:
            if user != username:
                if user != "":
                    toSet += (user+",")
        self.followers = toSet

    # To be called when an event is edited/updated
    def sendEmailToFollowers(self):
        userList = self.followers.split(",")
        for user in userList:
            usr = User_alch.query.filter_by(username=user).first()
            if usr is not None:
                msg = Message(
                        '%s has been updated!' % self.eventName,
                        sender='timsemailforlols@google.com',
                        recipients=[usr.email]
                        )
                msg.body = render_template("eventUpdatedEmail.txt", firstname=usr.firstname, eventname=self.eventName, eventurl=self.eventUrl)
                msg.html = render_template("eventUpdatedEmail.html", firstname=usr.firstname, eventname=self.eventName, eventurl=self.eventUrl)
                # TODO: currently, this starts a new thread for each user.  Should it instead start one new thread, and iterate through users there?  Basically, what happens if there are 100 users?  Will it currently try to start 100 threads, choke, and die?  (Total immediacy of the emails is also less important here than in the verification section)
                thr = Thread(target=send_async_email, args=[application, msg])
                thr.start()

    def rsvp(self, username, response):
        # remove user from any lists they might be on currently (so they can't be on more than one)
        newYes=""
        for randUser in self.yesGoingCSV.split(","):
            if randUser != username and randUser is not None and randUser != "":
                newYes+=(randUser + ",")
        self.yesGoingCSV = newYes
        newMaybe=""
        for randUser in self.maybeGoingCSV.split(","):
            if randUser != username and randUser is not None and randUser != "":
                newMaybe+=(randUser + ",")
        self.maybeGoingCSV = newMaybe
        newNo=""
        for randUser in self.noGoingCSV.split(","):
            if randUser != username and randUser is not None and randUser != "":
                newNo+=(randUser + ",")
        self.noGoingCSV = newNo

        print "response = "+response
        if response == "yes":
            self.yesGoingCSV+=(username + ",")
            print "Adding "+username+" to yesCSV"
        elif response == "maybe":
            self.maybeGoingCSV+=(username + ",")
            print "Adding "+username+" to maybeCSV"
        elif response == "no":
            self.noGoingCSV+=(username + ",")
            print "Adding "+username+" to noCSV"

    # clear list of RSVPs when event is updated
    def clearRsvps(self):
        self.yesGoingCSV = ""
        self.maybeGoingCSV = ""
        self.noGoingCSV = ""

    def getUsersRSVP(self, username):
        for user in self.yesGoingCSV.split(","):
            if user == username:
                return "yes"
        for user in self.maybeGoingCSV.split(","):
            if user == username:
                return "maybe"
        for user in self.noGoingCSV.split(","):
            if user == username:
                return "no"
        return "unknown"


def eventUrlAvail(urlIn):
    protectedUrls = ["login","lougout","register","createEvent","validateEmail","editUser","KILL_DB"]
    event_count = Event_alch.query.filter_by(eventUrl=urlIn).count()
    if event_count == 0:
        for url in protectedUrls:
            if urlIn.lower() == url.lower():
                return False
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

# def killDb():
#     alch_db.drop_all()
#     alch_db.create_all()
