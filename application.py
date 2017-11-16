from app import application
from flask import Flask
# app.run(host='localhost', port=5000, debug=True)
# application.run(debug=True)
if __name__ == "__main__":
    application.run(debug=True)

# from flask import Flask
#
# app = Flask(__name__)
#
# # run the app.
# if __name__ == "__main__":
#     app.run(debug=True)
