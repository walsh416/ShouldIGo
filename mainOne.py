
from flask import Flask, render_template, request
from flaskext.mysql import MySQL
from flask_restful import Resource, Api, reqparse
app = Flask(__name__)

mysql = MySQL()
app = Flask(__name__)
api = Api(app)

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'userDb'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

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

@app.route("/Authenticate")
def Authenticate():
    username = request.args.get('UserName')
    password = request.args.get('Password')
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT * from User where Username='" + username + "' and Password='" + password + "'")
    data = cursor.fetchone()
    if data is None:
     return "Username or Password is wrong"
    else:
     return "Logged in successfully"

class HandleRegister(Resource):
	def post(self):
		try:
			parser = reqparse.RequestParser()
            		parser.add_argument('email', type=str, help='Email address to create user')
            		parser.add_argument('password', type=str, help='Password to create user')
            		args = parser.parse_args()

            		_userEmail = args['email']
            		_userPassword = args['password']

            		conn = mysql.connect()
            		cursor = conn.cursor()
            		cursor.callproc('spCreateUser',(_userEmail,_userPassword))
            		data = cursor.fetchall()

            		if len(data) is 0:
                		conn.commit()
                		return {'StatusCode':'200','Message': 'User creation success'}
            		else:
            			return {'StatusCode':'1000','Message': str(data[0])}

        	except Exception as e:
            		return {'error': str(e)}

api.add_resource(HandleRegister, '/HandleRegister')

# @app.route("/handleregister", methods=["GET","POST"])
# def handle_reg():
# 	return request.form["firstname"] request.form['lastname'] + request.form['username']

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

if __name__ == "__main__":
    app.run(debug=True)
