
from flask import Flask, render_template, request, redirect, url_for, make_response
from flaskext.mysql import MySQL
from datetime import datetime, timedelta
import hashlib, os

# Open MySQL connection:
mysql = MySQL()
app = Flask(__name__)
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'userDb'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# commented out all the stuff to create a new database each time:
######################################
# connectionTemp = mysql.connect()
# cursorTemp = connectionTemp.cursor()
# out = '''DROP database IF EXISTS userDb;
# CREATE DATABASE userDb;
# USE userDb;
# CREATE TABLE User(
# firstname VARCHAR(50) NOT NULL,
# lastname VARCHAR(50) NOT NULL,
# username VARCHAR(50) NOT NULL,
# password VARCHAR(80) NOT NULL,
# salt VARCHAR(80) NOT NULL,
# ownedEventsCSV VARCHAR(200),
# primary key(username)
# );
# CREATE TABLE Event(
# eventURL VARCHAR(50) NOT NULL,
# ownersCSV VARCHAR(200) NOT NULL,
# primary key(eventURL)
# );'''
# cursorTemp.execute(out)
# connectionTemp.commit()
# connectionTemp.close()
######################################

# TODO: change column names in Event, add event attributes, etc
# TODO: allow deletion of events, user accounts, etc
# TODO: make events... do something

# returns datetime object for x days from now (for cookie expiration dates)
def get_x_daysFromNow(x):
	return datetime.today() + timedelta(days=x)

# return random string for a salt for a user
def get_salt():
	return str(hashlib.md5(os.urandom(64).encode("base-64")).hexdigest())

# take in raw password, return it hashed
def hash_pass(rawpassword):
	h = hashlib.md5(rawpassword.encode())
	return str(h.hexdigest())

# take in CSV of event URLs, use to parse into MySQL to return list of event names
def eventUrlCSV_to_eventNameStrList(csvIn):
	urlList = csvIn.split(",")
	nameList = []
	cursor = mysql.connect().cursor()
	for url in urlList:
		# TODO: fix this, obviously
		cursor.execute("SELECT * from Event where eventURL='" + url + "'")
		data = cursor.fetchone()
		if data is not None:
			eventName = data[1]
			nameList.append(eventName)
	return nameList

# default/index page
@app.route("/", methods=["GET","POST"])
def splashScreen():
	_username = request.cookies.get('username')
	# if there was a cookie with the key "username":
	if _username:
		# get user data from User table
		cursor = mysql.connect().cursor()
		cursor.execute("SELECT * from User where username='" + _username + "'")
		data = cursor.fetchone()
		# if there was no data, there was an error somewhere, so have the user log in again:
		if data is None:
			return render_template('login.html', badUser=True, badPass=False)
		print data
		_firstname = data[0]
		_lastname = data[1]
		_ownedEvents=data[5]
		_ownedEventsList = eventUrlCSV_to_eventNameStrList(_ownedEvents)

		# send user to userHome with appropriate arguments
		resp = make_response(render_template('userHome.html', username=_username, firstname=_firstname, lastname=_lastname, ownedevents=_ownedEventsList))
		# (re)set cookie with username to expire 90 days from now
		resp.set_cookie('username', _username, expires=get_x_daysFromNow(90))
		return resp
	# if there wasn't a cookie named "username":
	else:
		# show the default "Welcome! Login or Register below!"
		return render_template('splashScreen.html')

@app.route("/logout")
def logout():
	# redirect to index and call function splashScreen
	resp = make_response(redirect(url_for("splashScreen")))
	# delete username cookie
	resp.set_cookie('username', '', expires=0)
	return resp

@app.route("/login", methods = ["GET","POST"])
def login():
	# POST method means script was sent login data by user:
	if request.method == "POST":
		# pull user's username:
		_username = request.form.get('username')
		# find user in database
		cursor = mysql.connect().cursor()
		cursor.execute("SELECT * from User where username='" + _username + "'")
		data = cursor.fetchone()
		# if no user was found:
		if data is None:
			# try logging in again, with "bad username!" shown to user
			return render_template('login.html', badUser=True, badPass=False)
		# otherwise, get rest of user info from database response
		_firstname = data[0]
		_lastname = data[1]
		_hashPassOut = data[3]
		_saltOut = data[4]
		_ownedEvents=data[5]

		# hashPassIn is the raw password entered by the user plus the salt from the database
		_hashPassIn = hash_pass(request.form.get('password') + _saltOut)
		# if the password the user entered doesn't match the password in the database:
		if _hashPassIn != _hashPassOut:
			# keep user at login screen, with "bad password!" shown to user
			return render_template('login.html', badUser=False, badPass=True)
		# otherwise, password was good, so user can log in and redirect to welcome screen:
		resp = make_response(redirect(url_for('splashScreen')))
		# reset username cookie to expire 90 days from now
		resp.set_cookie('username', _username, expires=get_x_daysFromNow(90))
		return resp
	# GET method means user is logging in for the first time:
	else:
	    return render_template('login.html', badlogin=False)

@app.route("/register", methods=["GET","POST"])
def register():
	# POST method means data was sent by user
	if request.method == "POST":
		# check if first password matches second password
		if request.form.get('password') != request.form.get('passwordconfirm'):
			# if not, then have them reenter info
			return render_template('register.html', diffPasswords=True, duplicateUser=False)
		# if passwords do match:
		else:
			# try opening connection to database:
			try:
				connection = mysql.connect()
				cursor = connection.cursor()
				_userFirstname = request.form.get('firstname')
				_userLastname = request.form.get('lastname')
				_userUsername = request.form.get('username')
				# get a random salt:
				_userSalt = get_salt()
				_userPassword = hash_pass(request.form.get('password') + _userSalt)
				# add user to database:
				out = "INSERT INTO User values(\'" + _userFirstname + "\',\'" + _userLastname + "\',\'" + _userUsername + "\',\'" + _userPassword + "\',\'" + _userSalt + "\',\'\')"
				cursor.execute(out)
				connection.commit()

				# redirect user to splashScreen
				resp = make_response(redirect(url_for('splashScreen')))
				# add cookie with username to expire in 90 days
				resp.set_cookie('username', _userUsername, expires=get_x_daysFromNow(90))
				return resp
			except Exception as e:
				print e;
				# TODO: make sure Exception e is 1062 duplicate entry?
				# TODO: query database for someone with the username already.  If
				# 	returned is not None, then there is someone with that username
				return render_template('register.html', diffPasswords=False, duplicateUser=True)
	# GET method means user is here for the first time:
	else:
	    return render_template('register.html', diffPasswords=False, duplicateUser=False)

@app.route("/createEvent", methods=["GET","POST"])
def createEvent():
	# confirm user is logged in
	_username = request.cookies.get('username')
	# if they are not, redirect to the splashScreen
	if not _username:
		return redirect(url_for('splashScreen'))
	# otherwise, pull user data from database:
	connection = mysql.connect()
	cursor = connection.cursor()
	cursor.execute("SELECT * from User where username='" + _username + "'")
	data = cursor.fetchone()
	# if no user data in table, have user log in again:
	if data is None:
		return redirect(url_for('login'))
	_firstname = data[0]
	_lastname = data[1]
	_ownedEvents=data[5]

	# POST method implies data being passed, trying to create event:
	if request.method == "POST":
		# if doesn't have value for eventName, then still trying to pick a URL
		if not request.form.get('eventName'):
			eventUrl=request.form.get('eventURL')
			# cursor = mysql.connect().cursor()
			cursor.execute("SELECT * from Event where eventURL='" + eventUrl + "'")
			data = cursor.fetchone()
			# if eventURL is not already in the database:
			if data is None:
				# move on to second stage of creation, picking name and stuff
				# set cookie with eventURL, temporary, will be destroyed in stage two
				resp = make_response(render_template('createEvent.html', firstname=_firstname, urlInUse=False, eventURL=eventUrl))
				resp.set_cookie('eventURL',eventUrl, expires=get_x_daysFromNow(2))
				return resp
			# if event URL is in database, have user select a different one:
			else:
				return render_template('createEvent.html', firstname=_firstname, urlInUse=True)
		# if have form value for eventName, then already have cookie stored with eventUrl
		else:
			eventUrl = request.cookies.get('eventURL')
			eventName = request.form.get('eventName')

			# add event to Event table
			# connection = mysql.connect()
			# cursor = connection.cursor()
			out = "INSERT INTO Event values('" + eventUrl + "', '" + eventName + "')"
			cursor.execute(out)
			connection.commit()

			# get old list of ownedEvents from User table
			cursor.execute("SELECT ownedEventsCSV from User where username='" + _username + "'")
			data = cursor.fetchone()
			# append new event to list of old events:
			out = "UPDATE User SET ownedEventsCSV='" + data[0] + eventUrl + ",' WHERE username='" + _username + "'"
			cursor.execute(out)
			connection.commit()
			# print ("URL: "+eventUrl+", name: "+request.form.get('eventName'))

			resp = make_response(redirect(url_for('splashScreen')))
			resp.set_cookie('eventUrl', '', expires=0)
			return resp
	# GET method means user is here for first time, allow to check URL availability:
	else:
		return render_template('createEvent.html', firstname=_firstname, firstTime=True)

# @app.route("/user", methods=["GET","POST"])
# def helloUser():
#     return render_template('helloUser.html', )

# debug=True reloads the webpage whenver changes are made
if __name__ == "__main__":
    app.run(debug=True)
