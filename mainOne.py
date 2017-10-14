
from flask import Flask, render_template, request, redirect, url_for
from flaskext.mysql import MySQL
#from flask_restful import Resource, Api, reqparse
app = Flask(__name__)

mysql = MySQL()
app = Flask(__name__)
#api = Api(app)

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

# @app.route("/Authenticate")
# def Authenticate():
#     username = request.args.get('UserName')
#     password = request.args.get('Password')
#     cursor = mysql.connect().cursor()
#     cursor.execute("SELECT * from User where Username='" + username + "' and Password='" + password + "'")
#     data = cursor.fetchone()
#     if data is None:
#      return "Username or Password is wrong"
#     else:
#      return "Logged in successfully"

@app.route("/HandleRegister", methods=["GET","POST"])
def handle_reg():
    if request.form['password'] != request.form['passwordconfirm']:
        return redirect("/registerfail")
    else:
        # connection = mysql.get_db()
        connection = mysql.connect()
        cursor = connection.cursor()

        _userFirstname = request.form['firstname']
        _userLastname = request.form['lastname']
        _userUsername = request.form['username']
        _userPassword = request.form['password']

        # print _userUsername

    # #set up string in SQL request form
        # out = "INSERT INTO User values(" + "\'\',\'" + request.form['firstname'] + "\',\'" + request.form['lastname'] + "\',\'" + request.form['password'] + "\')"
        out = "INSERT INTO User values(\'" + _userFirstname + "\',\'" + _userLastname + "\',\'" + _userUsername + "\',\'" + _userPassword + "\')"
        cursor.execute(out)
        connection.commit()
        return redirect("/login")

@app.route("/registerfail", methods = ["GET","POST"])
def registerfail():
        return render_template('registerwrong.html')

@app.route("/login")
def login():
        return render_template('login.html')

@app.route("/register", methods=["GET","POST"])
def register():
        return render_template('register.html')

# @app.route("/<username>")
# def bar(username):
#         return render_template('userTemplate.html',
#                                 name=username)
# foo

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
