import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

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
# Random one-off passphrase from Google
MAIL_PASSWORD = 'vqlavnjpsmsytbtx'



################## DATABASE INSTRUCTIONS ####################
#### URI format: mysql://username:password@server/dbname ####
####                                                     ####
#### Use the localhost one to run it.. locally           ####
#### Use the crazy long one to run it on AWS/RDS         ####
#############################################################

### SSLify doesn't run if DEBUG = True, which is good because it doesn't work on localhost
################### IF RUNNING LOCALLY: ################
DEBUG = True
SQLALCHEMY_DATABASE_URI = "mysql://root:@localhost/userDb"
#####################################################

################### IF RUNNING ON AWS: #################
# DEBUG = False
# SQLALCHEMY_DATABASE_URI = "mysql+pymysql://walsh416:walsh416pass@walsh416dbinstance.cuo7hfdlcl5g.us-east-2.rds.amazonaws.com/thedatabase"
#####################################################
