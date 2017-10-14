
from flask import Flask, render_template, request, redirect, url_for
from flaskext.mysql import MySQL
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
            _userPassword = request.form['password']

            out = "INSERT INTO User values(\'" + _userFirstname + "\',\'" + _userLastname + "\',\'" + _userUsername + "\',\'" + _userPassword + "\')"
            cursor.execute(out)
            connection.commit()

<<<<<<< HEAD
        out = "INSERT INTO User values(\'" + _userFirstname + "\',\'" + _userLastname + "\',\'" + _userUsername + "\',\'" + _userPassword + "\')"
        cursor.execute(out)
        connection.commit()

        return redirect("/login")
=======
            # return redirect("/login")
            return render_template('userHome.html', username=_userUsername, firstname=_userFirstname, lastname=_userLastname)
        except Exception as e:
            # print e;
            # TODO: make sure Exception e is 1062 duplicate entry?
            return render_template('register.html', diffPasswords=False, duplicateUser=True)
>>>>>>> Tim

@app.route("/login")
def login():
    return render_template('login.html')

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
