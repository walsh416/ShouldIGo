# TODO: rename User and Event tables UserTable and EventTable to differentiate between them and classes

class User:
    def __init__ (self, username):
        self.username = username
        self.firstname = ""
        self.lastname = ""
        self.email = ""
        self.password = ""
        self.salt = ""
        self.ownedEventsList = []
        self.followedEventsList = []
        self.verifiedEmail = ""

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

    def insertString(self):
        # toreturn = "INSERT INTO User values(\'" + self.firstname + "\',\'" + self.lastname + "\',\'" + self.username + "\',\'" + self.password + "\',\'" + self.salt + "\',\'\',\'" + self.email + "\',\'\',\'" + self.verifiedEmail + "\')"
        toreturn = "INSERT INTO User values(\'" + self.firstname + "\',\'" + self.lastname + "\',\'" + self.username + "\',\'" + self.password + "\',\'" + self.salt + "\',\'" + self.getOwnedEventsCSV() + "\',\'" + self.email + "\',\'" + self.getFollowedEventsCSV() + "\',\'" + self.verifiedEmail + "\')"
        return toreturn

    def updateString(self, attribute, value):
        toreturn = "UPDATE User SET " + attribute + "='" + value + "' WHERE username='" + self.username + "'"
        return toreturn

    def selectString(self, attribute):
        toreturn = "SELECT " + attribute + " from User where username='" + self.username + "'"

    #### lololol wrote all of these before realizing "getattr()" and "setattr()" existed
    # def set_firstname (self, firstname):
    #     self.firstname = firstname
    # def set_lastname (self, lastname):
    #     self.lastname = lastname
    # def set_email (self, email):
    #     self.email = email
    # def set_password (self, password):
    #     self.password = password
    # def set_salt (self, salt):
    #     self.salt = salt
    # def set_ownedEventsCSV (self, ownedEventsCSV):
    #     self.ownedEventsCSV = ownedEventsCSV
    # def set_followedEventsCSV (self, followedEventsCSV):
    #     self.followedEventsCSV = followedEventsCSV

    def printUser(self):
        print "firstname: " + self.firstname +
            "\nlastname: " + self.lastname +
            "\nusername: " + self.username +
            "\nemail: " + self.email +
            "\nownedEvents: " + self.ownedEventsCSV +
            "\nfollowedEvents: " + self.followedEventsCSV

class Event:
    def __init__(self, eventUrl):
        self.eventUrl = eventUrl
        self.eventName = ""
        self.eventDesc = ""
        self.followersList = []

    def getFollowersCSV(self):
        toreturn = ""
        for event in self.followersList:
            toreturn = toreturn + ","
        return toreturn

    def insertString(self):
        # toreturn = "INSERT INTO Event values('" + self.eventUrl + "', '" + self.eventName + "', '" + self.eventDesc + "','')"
        toreturn = "INSERT INTO Event values('" + self.eventUrl + "', '" + self.eventName + "', '" + self.eventDesc + "','" + self.getFollowersCSV() + "')"
        return toreturn

    def updateString(self, attribute, value):
        toreturn = "UPDATE Event SET " + attribute + "='" + value + ",' WHERE eventUrl='" + self.eventUrl + "'"
        return toreturn

    def selectString(self, attribute):
        toreturn = "SELECT " + attribute + " from Event WHERE eventUrl='" + self.eventUrl "'"























#
