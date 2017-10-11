
from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def hello():
    return '''
Hello World!
<a href="/foo">Click for foo!</a>
'''

@app.route("/<username>")
def bar(username):
	return render_template('userTemplate.html',
				name=username)

if __name__ == "__main__":
    app.run(debug=True)
