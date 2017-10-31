
from flask import Flask, render_template, request, redirect, url_for, make_response
from flaskext.mysql import MySQL
from datetime import datetime, timedelta
from flask_mail import Mail, Message
from threading import Thread
import hashlib, os, re

# Open MySQL connection:
mysql = MySQL()
app = Flask(__name__)
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'userDb'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# mail=Mail(app)
# Following two lines are both(?) needed to allow initial access to new gmail account
## www.google.com/settings/security/lesssecureapps
## accounts.google.com/DisplayUnlockCaptcha
app.config.update(
	DEBUG=True,
	# MAIL_SERVER='smtp.googlemail.com',
	MAIL_SERVER = 'smtp.gmail.com',
	# MAIL_PORT=587,
	# MAIL_USE_SSL=False,
	# MAIL_USE_TSL=True,
	MAIL_PORT=465,
	MAIL_USE_SSL=True,
	MAIL_USE_TLS=False,
	MAIL_USERNAME = 'timsemailforlols@gmail.com',
	MAIL_PASSWORD = 'vqlavnjpsmsytbtx'
	# MAIL_PASSWORD = 'thisisthepassword'
	)
mail=Mail(app)

# TODO: allow deletion of events, user accounts, etc
# TODO: send email to subscribers when an event is updated (given an event,
# 			figuring out who is subscribed to it is gonna be ugly (searching
# 			through each users CSV or something... ugh))
# TODO: additional col in User for "verifiedEmail", just a boolean 1 or 0.
# 			if it's a 0, then cripple splashScreen until they update or confirm email.
# 			How to confirm... Need link back from email, but should be random-ish,
# 			hopefully temporary... ugh.

# returns datetime object for x days from now (for cookie expiration dates)
def get_x_daysFromNow(x):
	return datetime.today() + timedelta(days=x)

# return random string for a salt for a user
def get_x_randoms(x):
	return str(hashlib.md5(os.urandom(64).encode("base-64")).hexdigest())[:x]

# take in raw password, return it hashed
def hash_pass(rawpassword):
	h = hashlib.md5(rawpassword.encode())
	return str(h.hexdigest())

# take in CSV of event Urls, use to parse into MySQL to return list of event names
def eventUrlCSV_to_eventNameStrList(csvIn):
	UrlList = csvIn.split(",")
	nameList = []
	cursor = mysql.connect().cursor()
	for Url in UrlList:
		# TODO: fix this, obviously
		cursor.execute("SELECT * from Event where eventUrl='" + Url + "'")
		data = cursor.fetchone()
		if data is not None:
			eventName = data[1]
			nameList.append(eventName)
	return nameList

# take in a CSV list and a string, and return boolean val of whether the string is in the list
def is_EventUrl_in_EventUrlCSV(urlIn, csvIn):
	# print "looking for url: " + urlIn + " in CSV: " + csvIn
	UrlList = csvIn.split(",")
	for url in UrlList:
		if urlIn==url:
			return True
	return False

# takes in an email message to send, and sends it on a separate thread so main process doesn't hang
def send_async_email(app, msg):
	with app.app_context():
		# print "about to send email"
		mail.send(msg)
		# print "sent email"

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
		# print data
		_firstname = data[0]
		_lastname = data[1]
		_ownedEventsUrls=data[5]
		_isVerified=data[8]
		print _isVerified
		if _isVerified!="0":
			resp = make_response(render_template('userHome.html', username=_username, firstname=_firstname, lastname=_lastname, verified=False))
			# (re)set cookie with username to expire 90 days from now
			resp.set_cookie('username', _username, expires=get_x_daysFromNow(90))
			return resp

		# retrieve list of names of events based on their URLs
		_ownedEventsList = eventUrlCSV_to_eventNameStrList(_ownedEventsUrls)
		# split CSV of urls into a list
		_ownedEventsUrlsList = _ownedEventsUrls.split(",")
		# prepend a slash to each URL, so it can be given straight to the userHome.html template
		for url in _ownedEventsUrlsList:
			# url = '"/'+url+'"'
			url = '/'+url

		# zip both lists together: creates an equal length list of tuples
		_ownedEventsZipped = zip(_ownedEventsList,_ownedEventsUrlsList)

		# send user to userHome with appropriate arguments
		resp = make_response(render_template('userHome.html', username=_username, firstname=_firstname, lastname=_lastname, ownedeventszipped=_ownedEventsZipped, verified=True))
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
				# TODO: there should be some sweet maker pattern to implement to add stuff to the database
				# 			ex: createUser(username).addFirstname(foo).addLastname(bar).... etc.
				connection = mysql.connect()
				cursor = connection.cursor()
				_userFirstname = request.form.get('firstname')
				_userLastname = request.form.get('lastname')
				_userUsername = request.form.get('username')
				_userEmail = request.form.get('email')
				# get a random salt:
				_userSalt = get_x_randoms(64)
				_userPassword = hash_pass(request.form.get('password') + _userSalt)
				_userEmailValidation = get_x_randoms(16)
				print _userEmailValidation

				# checking valid email against regexp for it
				validEmail = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', _userEmail)
				if validEmail == None:
					return render_template('register.html', badEmail=True)
				# TODO: still need to actually send the user an email and have them confirm it

				# add user to database:
				out = "INSERT INTO User values(\'" + _userFirstname + "\',\'" + _userLastname + "\',\'" + _userUsername + "\',\'" + _userPassword + "\',\'" + _userSalt + "\',\'\',\'" + _userEmail + "\',\'\',\'" + _userEmailValidation + "\')"

				cursor.execute(out)
				connection.commit()

				msg = Message(
						'Hello, %s!' % _userFirstname,
						sender='timsemailforlols@google.com',
						recipients=[_userEmail]
						)
				msg.body = render_template("registerEmail.txt", firstname=_userFirstname, username=_userUsername, validation=_userEmailValidation)
				msg.html = render_template("registerEmail.html", firstname=_userFirstname, username=_userUsername, validation=_userEmailValidation)
				# mail.send(msg)
				thr = Thread(target=send_async_email, args=[app, msg])
				thr.start()
				# TODO: should anything happen if bogus email is given?  Some sort of two stage
				# 		"now go verify your email" type of deal that forces the user to show it's legit?

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
	# GET method means user is here for the first time or is confirming email address:
	else:
		# try pulling username and validation code out of GET method
		# TODO: make sure this all works right on initial registration (maybe surround in try/except or something?)
		# TODO: what happens if user clicks to verify email twice?  Goes through properly the first time, and then...?
		# 				Maybe check if username already has validation==1 or not?
		username=request.args.get('username')
		validation=request.args.get('validation')
		if not username:
			return render_template('register.html', diffPasswords=False, duplicateUser=False)
		connection = mysql.connect()
		cursor = connection.cursor()
		cursor.execute("SELECT verifiedEmail from User where username='" + username + "'")
		data = cursor.fetchone()
		# if no user data in table, have user register again:
		if data is None:
			return redirect(url_for('register'))
		dbValidation = data[0]
		if dbValidation == validation:
			# Validation code was good!!  Reset code in table to 1
			out = "UPDATE User SET verifiedEmail='0' WHERE username='" + username + "'"
			cursor.execute(out)
			connection.commit()
			# redirect user to splashScreen
			resp = make_response(redirect(url_for('splashScreen')))
			# add cookie with username to expire in 90 days
			resp.set_cookie('username', username, expires=get_x_daysFromNow(90))
			return resp
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
	# otherwise, pull rest of user data
	_firstname = data[0]
	_lastname = data[1]
	_ownedEvents=data[5]

	# POST method implies data being passed, trying to create event:
	if request.method == "POST":
		# if doesn't have value for eventName, then still trying to pick a Url
		if not request.form.get('eventName'):
			eventUrl=request.form.get('eventUrl')
			# cursor = mysql.connect().cursor()
			cursor.execute("SELECT * from Event where eventUrl='" + eventUrl + "'")
			data = cursor.fetchone()
			# if eventUrl is not already in the database:
			if data is None:
				# move on to second stage of creation, picking name and stuff
				# set cookie with eventUrl, temporary, will be destroyed in stage two
				resp = make_response(render_template('createEvent.html', firstname=_firstname, UrlInUse=False, eventUrl=eventUrl))
				resp.set_cookie('eventUrl',eventUrl, expires=get_x_daysFromNow(2))
				return resp
			# if event Url is in database, have user select a different one:
			else:
				return render_template('createEvent.html', firstname=_firstname, UrlInUse=True)
		# if have form value for eventName, then already have cookie stored with eventUrl
		else:
			eventUrl = request.cookies.get('eventUrl')
			eventName = request.form.get('eventName')
			eventDesc = request.form.get('eventDesc')

			# add event to Event table
			# connection = mysql.connect()
			# cursor = connection.cursor()
			out = "INSERT INTO Event values('" + eventUrl + "', '" + eventName + "', '" + eventDesc + "','')"
			cursor.execute(out)
			connection.commit()

			# get old list of ownedEvents from User table
			cursor.execute("SELECT ownedEventsCSV from User where username='" + _username + "'")
			data = cursor.fetchone()
			# append new event to list of old events:
			out = "UPDATE User SET ownedEventsCSV='" + data[0] + eventUrl + ",' WHERE username='" + _username + "'"
			cursor.execute(out)
			connection.commit()
			# print ("Url: "+eventUrl+", name: "+request.form.get('eventName'))

			resp = make_response(redirect(url_for('splashScreen')))
			resp.set_cookie('eventUrl', '', expires=0)
			return resp
	# GET method means user is here for first time, allow to check Url availability:
	else:
		return render_template('createEvent.html', firstname=_firstname, firstTime=True)


#in progress
@app.route("/deleteEvent", methods=["DELETE"])
def deleteEvent():
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

	# DELETE method implies data is in table, trying to delete event:
	if request.method == "DELETE":
		# if doesn't have value for eventName, then still trying to pick a Url
			eventUrl = request.cookies.get('eventUrl')
			eventName = request.form.get('eventName')
			eventDesc = request.form.get('eventDesc')

			# add event to Event table
			# connection = mysql.connect()
			# cursor = connection.cursor()
			out = "DELETE FROM Event values('" + eventUrl + "', '" + eventName + "', '" + eventDesc + "')"
			cursor.execute(out)
			connection.commit()

			# get old list of ownedEvents from User table
			cursor.execute("SELECT ownedEventsCSV from User where username='" + _username + "'")
			data = cursor.fetchone()
			# append new event to list of old events:
			out = "UPDATE User SET ownedEventsCSV='" + data[0] + eventUrl + ",' WHERE username='" + _username + "'"
			cursor.execute(out)
			connection.commit()
			# print ("Url: "+eventUrl+", name: "+request.form.get('eventName'))

			resp = make_response(redirect(url_for('splashScreen')))
			resp.set_cookie('eventUrl', '', expires=0)
			return resp
	# GET method means user is here for first time, allow to check Url availability:
	else:
		return render_template('deleteEvent.html', firstname=_firstname, firstTime=True)


@app.route('/validateEmail')
def resendValidationEmail():
	connection = mysql.connect()
	cursor = connection.cursor()
	# TODO: allow users to edit their email address
	username=request.args.get('username')
	validation=request.args.get('validation')
	# here for first time, so send them an email:
	print username
	if username is None:
		# confirm user is logged in
		_username = request.cookies.get('username')
		# if they are not, redirect to the splashScreen
		if not _username:
			return redirect(url_for('splashScreen'))
		# otherwise, pull user data from database:
		cursor.execute("SELECT * from User where username='" + _username + "'")
		data = cursor.fetchone()
		# if no user data in table, have user log in again:
		if data is None:
			return redirect(url_for('login'))
		_firstname = data[0]
		_lastname = data[1]
		_username = data[2]
		_email = data[6]
		_emailValidation = data[8]

		msg = Message(
				'Validating %s\'s email!' % _firstname,
				sender='timsemailforlols@google.com',
				recipients=[_email]
				)
		msg.body = render_template("registerEmail.txt", firstname=_firstname, username=_username, validation=_emailValidation)
		msg.html = render_template("registerEmail.html", firstname=_firstname, username=_username, validation=_emailValidation)
		# mail.send(msg)
		thr = Thread(target=send_async_email, args=[app, msg])
		thr.start()
		# redirect user to splashScreen
		# TODO: add argument to splashScreen to display a "sent another validation email!"
		resp = make_response(redirect(url_for('splashScreen')))
		# add cookie with username to expire in 90 days
		resp.set_cookie('username', _username, expires=get_x_daysFromNow(90))
		return resp
	cursor.execute("SELECT verifiedEmail from User where username='" + username + "'")
	data = cursor.fetchone()
	# if no user data in table, have user register again:
	if data is None:
		return redirect(url_for('register'))
	dbValidation = data[0]
	if dbValidation == validation:
		# Validation code was good!!  Reset code in table to 1
		out = "UPDATE User SET verifiedEmail='0' WHERE username='" + username + "'"
		cursor.execute(out)
		connection.commit()
		# redirect user to splashScreen
		resp = make_response(redirect(url_for('splashScreen')))
		# add cookie with username to expire in 90 days
		resp.set_cookie('username', username, expires=get_x_daysFromNow(90))
		return resp


# TODO: resend verification email if a new email is entered
@app.route('/editUser', methods=["GET","POST"])
def editUser():
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
	_email = data[6]
	# GET means that this is the first time here, so show page allowing user to edit their info
	if request.method=="GET":
		return render_template('editUser.html', firstname=_firstname, lastname=_lastname, email=_email)
	# POST means that the form has already been submitted, time to execute it
	new_firstname=request.form.get('firstname')
	new_lastname=request.form.get('lastname')
	new_email=request.form.get('email')
	# Two different MySQL commands to update first and last name.  Tried to combine into one line but kept getting errors.
	out = "UPDATE User SET firstname='" + new_firstname + "' WHERE username='" + _username + "'"
	cursor.execute(out)
	connection.commit()
	out = "UPDATE User SET lastname='" + new_lastname + "' WHERE username='" + _username + "'"
	cursor.execute(out)
	connection.commit()
	out = "UPDATE User SET email='" + new_email + "' WHERE username='" + _username + "'"
	cursor.execute(out)
	connection.commit()
	# Throw user back to "/" and view the splashScreen/userHome.
	return make_response(redirect(url_for('splashScreen')))

# <eventUrl> is a variable that matches with any other URL to check if it's a valid eventUrl
@app.route("/<eventUrl>", methods=["GET","POST"])
def showEvent(eventUrl):
	connection = mysql.connect()
	cursor = connection.cursor()
	# confirm user is logged in
	_username = request.cookies.get('username')
	if request.method == "POST":
		# get old list of ownedEvents from User table
		cursor.execute("SELECT followedEventsCSV from User where username='" + _username + "'")
		data = cursor.fetchone()
		# append new event to list of old events:
		out = "UPDATE User SET followedEventsCSV='" + data[0] + eventUrl + ",' WHERE username='" + _username + "'"
		# print "executing mysql: " + out
		cursor.execute(out)
		connection.commit()
		# return render_template('showEvent.html', eventUrl=eventUrl, eventName=_eventName, eventDesc=_eventDesc, userLoggedIn=userLoggedIn, subscribed=subscribed)
		return redirect(url_for('showEvent', eventUrl=eventUrl))
	# currUserIsOwner = False
	userLoggedIn = False
	subscribed = False
	# if they are, show event page with "follow" button
	if _username:
		# pull user data from database:
		# connection = mysql.connect()
		# cursor = connection.cursor()
		cursor.execute("SELECT * from User where username='" + _username + "'")
		data = cursor.fetchone()
		# if no user data in table, have user log in again:
		if data is None:
			return redirect(url_for('login'))
		# otherwise, pull rest of user data
		# print data
		_firstname = data[0]
		_lastname = data[1]
		_followedEvents=data[7]
		userLoggedIn = True
		subscribed = is_EventUrl_in_EventUrlCSV(eventUrl, _followedEvents)
	# connection = mysql.connect()
	# cursor = connection.cursor()
	cursor.execute("SELECT * from Event where eventURL='" + eventUrl + "'")
	data = cursor.fetchone()
	# TODO: does this actually work?  Or does it need to be redone to catch errors?
	# if no event data in table, redirect to splashScreen:
	if data is None:
		return redirect(url_for('splashScreen'))
	_eventName = data[1]
	_eventDesc = data[2]
	return render_template('showEvent.html', eventUrl=eventUrl, eventName=_eventName, eventDesc=_eventDesc, userLoggedIn=userLoggedIn, subscribed=subscribed)

# Hidden URL never shown to user, for testing only and to be removed before production
# Gives ability to call MySQL code to reset the databases without logging into MySQL
@app.route('/KILL_DB')
def killDb():
	connectionTemp = mysql.connect()
	cursorTemp = connectionTemp.cursor()
	##########################################################
	###### Database notes:
	###### verifiedEmail is initially a 16 character random string.
	######		Once the user has verified their email, it is updated to "0"
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
	print "################ DB killed ################"
	resp = make_response(redirect(url_for('splashScreen')))
	resp.set_cookie('username', '', expires=0)
	return resp

# debug=True reloads the webpage whenver changes are made
if __name__ == "__main__":
    app.run(debug=True)










#
