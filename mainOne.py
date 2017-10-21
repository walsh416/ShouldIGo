
from flask import Flask, render_template, request, redirect, url_for, make_response
from flaskext.mysql import MySQL
from datetime import datetime, timedelta
import hashlib, os

app = Flask(__name__)

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

def get_x_daysFromNow(x):
	return datetime.today() + timedelta(days=x)

def get_salt():
	return str(hashlib.md5(os.urandom(64).encode("base-64")).hexdigest())

def hash_pass(rawpassword):
	h = hashlib.md5(rawpassword.encode())
	return str(h.hexdigest())

@app.route("/", methods=["GET","POST"])
def splashScreen():
	_username = request.cookies.get('username')
	if _username:
		cursor = mysql.connect().cursor()
		cursor.execute("SELECT * from User where username='" + _username + "'")
		data = cursor.fetchone()
		if data is None:
			return render_template('login.html', badUser=True, badPass=False)
		print data
		_firstname = data[0]
		_lastname = data[1]
		_ownedEvents=data[5]
		_ownsEvents=(_ownedEvents == None)

		resp = make_response(render_template('userHome.html', username=_username, firstname=_firstname, lastname=_lastname, ownedevents=_ownedEvents, ownsevents=_ownedEvents))
		resp.set_cookie('username', _username, expires=get_x_daysFromNow(90))
		return resp
	else:
		return render_template('splashScreen.html')

@app.route("/logout")
def logout():
	resp = make_response(redirect(url_for("splashScreen")))
	resp.set_cookie('username', '', expires=0)
	return resp

@app.route("/login", methods = ["GET","POST"])
def login():
	if request.method == "POST":
		_username = request.form.get('username')

		cursor = mysql.connect().cursor()
		cursor.execute("SELECT * from User where username='" + _username + "'")
		data = cursor.fetchone()
		if data is None:
			return render_template('login.html', badUser=True, badPass=False)
		_firstname = data[0]
		_lastname = data[1]
		_hashPassOut = data[3]
		_saltOut = data[4]
		_ownedEvents=data[5]

		_hashPassIn = hash_pass(request.form.get('password') + _saltOut)
		if _hashPassIn != _hashPassOut:
			return render_template('login.html', badUser=False, badPass=True)
		# return render_template('userHome.html', username=_username, firstname=_firstname, lastname=_lastname, ownedEvents=_ownedEvents)

		# resp = make_response(render_template('userHome.html', username=_username, firstname=_firstname, lastname=_lastname, ownedEvents=_ownedEvents))
		# resp = make_response(redirect(url_for('splashScreen', username=_username, firstname=_firstname, lastname=_lastname, ownedEvents=_ownedEvents)))
		resp = make_response(redirect(url_for('splashScreen')))
		resp.set_cookie('username', _username, expires=get_x_daysFromNow(90))
		return resp
	else:
	    return render_template('login.html', badlogin=False)

@app.route("/register", methods=["GET","POST"])
def register():
	if request.method == "POST":
		if request.form.get('password') != request.form.get('passwordconfirm'):
			# return redirect("/registerfail")
			return render_template('register.html', diffPasswords=True, duplicateUser=False)
		else:
			try:
				connection = mysql.connect()
				cursor = connection.cursor()
				_userFirstname = request.form.get('firstname')
				_userLastname = request.form.get('lastname')
				_userUsername = request.form.get('username')
				_userSalt = get_salt()
				_userPassword = hash_pass(request.form.get('password') + _userSalt)
				out = "INSERT INTO User values(\'" + _userFirstname + "\',\'" + _userLastname + "\',\'" + _userUsername + "\',\'" + _userPassword + "\',\'" + _userSalt + "\',\'\')"
				cursor.execute(out)
				connection.commit()
				# return render_template('userHome.html', username=_userUsername, firstname=_userFirstname, lastname=_userLastname)

				# 			resp = make_response(render_template('userHome.html', username=_userUsername, firstname=_userFirstname, lastname=_userLastname))
				resp = make_response(redirect(url_for('splashScreen')))
				resp.set_cookie('username', _userUsername, expires=get_x_daysFromNow(90))
				return resp
			except Exception as e:
				print e;
				# TODO: make sure Exception e is 1062 duplicate entry?
				return render_template('register.html', diffPasswords=False, duplicateUser=True)
	else:
	    return render_template('register.html', diffPasswords=False, duplicateUser=False)

@app.route("/createEvent", methods=["GET","POST"])
def createEvent():
	_username = request.cookies.get('username')
	if not _username:
		return redirect(url_for('splashScreen'))
	connection = mysql.connect()
	cursor = connection.cursor()
	cursor.execute("SELECT * from User where username='" + _username + "'")
	data = cursor.fetchone()
	if data is None:
		return redirect(url_for('login'))
	_firstname = data[0]
	_lastname = data[1]
	_ownedEvents=data[5]

	if request.method == "POST":
		# if doesn't have value for eventName, then still trying to pick a URL
		if not request.form.get('eventName'):
			eventUrl=request.form.get('eventURL')
			# cursor = mysql.connect().cursor()
			cursor.execute("SELECT * from Event where eventURL='" + eventUrl + "'")
			data = cursor.fetchone()
			if data is None:
				# move on to second stage of creation, picking name and stuff
				# set cookie with eventURL, temporary, will be destroyed in stage two
				resp = make_response(render_template('createEvent.html', firstname=_firstname, urlInUse=False, eventURL=eventUrl))
				resp.set_cookie('eventURL',eventUrl, expires=get_x_daysFromNow(2))
				return resp
				# return render_template('createEvent.html', firstname=_firstname, urlInUse=False, eventURL=request.form.get('eventURL'))
			else:
				return render_template('createEvent.html', firstname=_firstname, urlInUse=True)
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
	else:
		return render_template('createEvent.html', firstname=_firstname, firstTime=True)

# @app.route("/user", methods=["GET","POST"])
# def helloUser():
#     return render_template('helloUser.html', )

if __name__ == "__main__":
    app.run(debug=True)
