
from flask import Flask, render_template, request, redirect, url_for
from flaskext.mysql import MySQL
import hashlib

app = Flask(__name__)

mysql = MySQL()
app = Flask(__name__)

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'userDb'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

connectionTemp = mysql.connect()
cursorTemp = connectionTemp.cursor()
out = '''DROP database IF EXISTS userDb;
CREATE DATABASE userDb;
USE userDb;
CREATE TABLE User(
firstname VARCHAR(50) NOT NULL,
lastname VARCHAR(50) NOT NULL,
username VARCHAR(50) NOT NULL,
password VARCHAR(40) NOT NULL,
primary key(username)
);'''
cursorTemp.execute(out)
connectionTemp.commit()
connectionTemp.close()

def hash(rawpassword):
	salt = "5gz"
	db_password = rawpassword+salt
	h = hashlib.md5(db_password.encode())
	return str(h.hexdigest())

@app.route("/", methods=["GET","POST"])
def hello():
    return render_template('splashScreen.html')

@app.route("/HandleRegister", methods=["GET","POST"])
def handle_reg():
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
			_userPassword = hash(request.form['password'])
			out = "INSERT INTO User values(\'" + _userFirstname + "\',\'" + _userLastname + "\',\'" + _userUsername + "\',\'" + _userPassword + "\')"
			cursor.execute(out)
			connection.commit()
			return render_template('userHome.html', username=_userUsername, firstname=_userFirstname, lastname=_userLastname)
        except Exception as e:
            print e;
            # TODO: make sure Exception e is 1062 duplicate entry?
            return render_template('register.html', diffPasswords=False, duplicateUser=True)


# @app.route("/registerfail", methods = ["GET","POST"])
# def registerfail():
#     return render_template('registerwrong.html')

@app.route("/loginCheck", methods = ["GET", "POST"])
def loginCheck():
	_username = request.form['username']
	_hashPassIn = hash(request.form['password'])

	# TODO: get first, last name, etc from DB

	cursor = mysql.connect().cursor()
	cursor.execute("SELECT * from User where username='" + _username + "'")
	data = cursor.fetchone()
	# print "Hash pass in: " + _hashPassIn
	# print "Hash pass out: " + data[3]
	# print "data out: %s" % (data,)
	if data is None:
		return render_template('login.html', badUser=True, badPass=False)
	_firstname = data[0]
	_lastname = data[1]
	_hashPassOut = data[3]
	if _hashPassIn != _hashPassOut:
		return render_template('login.html', badUser=False, badPass=True)
	return render_template('userHome.html', username=_username, firstname=_firstname, lastname=_lastname)

@app.route("/login")
def login():
    return render_template('login.html', badlogin=False)

@app.route("/register", methods=["GET","POST"])
def register():
    return render_template('register.html', diffPasswords=False, duplicateUser=False)

# @app.route("/user", methods=["GET","POST"])
# def helloUser():
#     return render_template('helloUser.html', )

if __name__ == "__main__":
    app.run(debug=True)

#####################
## mySql commands: ##
#####################
# DROP database IF EXISTS userDb;
# CREATE DATABASE userDb;
# USE userDb;
# CREATE TABLE User(
# firstname VARCHAR(50) NOT NULL,
# lastname VARCHAR(50) NOT NULL,
# username VARCHAR(50) NOT NULL,
# password VARCHAR(40) NOT NULL,
# primary key(username)
# );
