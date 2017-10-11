
from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def hello():
    return '''
<h1>Welcome to isThere.today!</h1>
Click below to register or login.<br>
<a href="/register">Register</a><br>
<a href="/login">Login</a> 
'''

@app.route("/login")
def login():
        return render_template('login.html')

@app.route("/register")
def register():
        return render_template('register.html')

@app.route("/<username>")
def bar(username):
        return render_template('userTemplate.html',
                                name=username)

if __name__ == "__main__":
    app.run(debug=True)
