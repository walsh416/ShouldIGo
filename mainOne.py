
from flask import Flask, render_template, request, redirect, url_for
from flaskext.mysql import MySQL
<<<<<<< HEAD
=======

>>>>>>> jacob-branch
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

<<<<<<< HEAD
def hash(rawpassword):
	salt = "5gz"
	db_password = rawpassword+salt
	h = hashlib.md5(db_password.encode())
	return h.hexdigest()

@app.route("/", methods=["GET","POST"])
def hello():
    return render_template('splashScreen.html')
=======

@app.route("/", methods=["GET","POST"])
def hello():
    return '''
<head>
        <link rel= "stylesheet" type= "text/css" href= "{{ url_for('static',filename='styles/style.css') }}" />
</head>
<h1>Welcome to isThere.today!</h1>
Click below to register or login.<br>
<a href="/register">Register</a><br>
<a href="/login">Login</a>
'''

>>>>>>> jacob-branch

@app.route("/HandleRegister", methods=["GET","POST"])
def handle_reg():
    if request.form['password'] != request.form['passwordconfirm']:
        # return redirect("/registerfail")
        return render_template('register.html', diffPasswords=True, duplicateUser=False)
    else:
<<<<<<< HEAD
        try:
            connection = mysql.connect()
            cursor = connection.cursor()

            _userFirstname = request.form['firstname']
            _userLastname = request.form['lastname']
            _userUsername = request.form['username']
            _userPassword = hash(request.form['password'])
=======
        connection = mysql.connect()
        cursor = connection.cursor()
>>>>>>> jacob-branch

            out = "INSERT INTO User values(\'" + _userFirstname + "\',\'" + _userLastname + "\',\'" + _userUsername + "\',\'" + _userPassword + "\')"
            cursor.execute(out)
            connection.commit()

<<<<<<< HEAD
<<<<<<< HEAD
        out = "INSERT INTO User values(\'" + _userFirstname + "\',\'" + _userLastname + "\',\'" + _userUsername + "\',\'" + _userPassword + "\')"
        cursor.execute(out)
        connection.commit()

=======
        out = "INSERT INTO User values(\'" + _userFirstname + "\',\'" + _userLastname + "\',\'" + _userUsername + "\',\'" + _userPassword + "\')"
        cursor.execute(out)
        connection.commit()
>>>>>>> jacob-branch
        return redirect("/login")
=======
            # return redirect("/login")
            return render_template('userHome.html', username=_userUsername, firstname=_userFirstname, lastname=_userLastname)
        except Exception as e:
            # print e;
            # TODO: make sure Exception e is 1062 duplicate entry?
            return render_template('register.html', diffPasswords=False, duplicateUser=True)
>>>>>>> Tim

<<<<<<< HEAD
=======
@app.route("/registerfail", methods = ["GET","POST"])
def registerfail():
    return render_template('registerwrong.html')

@app.route("/loginCheck", methods = ["GET", "POST"])
def loginCheck():
    username = request.form['username']
    password = request.form['password']
    
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT * from user where username='" + username + "' and password='" + password + "'")
    data = cursor.fetchone()
    if data is None:
        return "Username or Password is wrong"
    else:
        return "Logged in successfully"
    return render_template('login.html')
    
>>>>>>> jacob-branch
@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/register", methods=["GET","POST"])
def register():
    return render_template('register.html', diffPasswords=False, duplicateUser=False)

<<<<<<< HEAD
# @app.route("/user", methods=["GET","POST"])
# def helloUser():
#     return render_template('helloUser.html', )
=======
# @app.route("/<username>")
# def bar(username):
#         return render_template('userTemplate.html',
#                                 name=username)
# foo
>>>>>>> jacob-branch

if __name__ == "__main__":
    app.run(debug=True)

<<<<<<< HEAD
=======

>>>>>>> jacob-branch
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
