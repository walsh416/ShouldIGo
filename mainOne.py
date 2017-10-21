
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
# # out = '''DROP database IF EXISTS userDb;
# out = '''USE userDb;
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
		_firstname = data[0]
		_lastname = data[1]
		_ownedEvents=data[5]

		resp = make_response(render_template('userHome.html', username=_username, firstname=_firstname, lastname=_lastname, ownedEvents=_ownedEvents))
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
		_username = request.form['username']

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

		_hashPassIn = hash_pass(request.form['password'] + _saltOut)
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
		if request.form['password'] != request.form['passwordconfirm']:
			# return redirect("/registerfail")
			return render_template('register.html', diffPasswords=True, duplicateUser=False)
		else:
			try:
				connection = mysql.connect()
				cursor = connection.cursor()
				_userFirstname = request.form['firstname']
				_userLastname = request.form['lastname']
				_userUsername = request.form['username']
				_userSalt = get_salt()
				_userPassword = hash_pass(request.form['password'] + _userSalt)
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
	# need to know username here... pass in post method from incoming page?
	_firstname = "MY FIRST NAME"
	return render_template('createEvent.html', firstname=_firstname, urlInUse=None, firstTime=True)

# @app.route("/user", methods=["GET","POST"])
# def helloUser():
#     return render_template('helloUser.html', )

if __name__ == "__main__":
    app.run(debug=True)
