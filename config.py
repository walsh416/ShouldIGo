DEBUG = True

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

MYSQL_DATABASE_USER = "root"
MYSQL_DATABASE_PASSWORD = ""
MYSQL_DATABASE_DB = "userDb"
MYSQL_DATABASE_HOST = "localhost"

# URI format: mysql://username:password@server/dbname
SQLALCHEMY_DATABASE_URI = "mysql://root:@localhost/userDb"
# This line stops it from yelling at you, since it's removing the capability in the next release:
SQLALCHEMY_TRACK_MODIFICATIONS = False

MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT="465"
MAIL_USE_SSL=True
MAIL_USE_TLS=False
# MAIL_PORT=587,
# MAIL_USE_SSL=False,
# MAIL_USE_TSL=True,
MAIL_USERNAME = 'timsemailforlols@gmail.com'
MAIL_PASSWORD = 'vqlavnjpsmsytbtx'
