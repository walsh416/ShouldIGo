
from flask import Flask, render_template, request, redirect, url_for, make_response
from flaskext.mysql import MySQL
from datetime import datetime, timedelta
from flask_mail import Mail, Message
from threading import Thread
import hashlib, os, re
import database_handling as db_h

app = Flask(__name__)

app.config.from_object('config')

mail = Mail(app)

# TODO: allow deletion of events, user accounts, etc
# TODO: send email to subscribers when an event is updated (given an event,
#             figuring out who is subscribed to it is gonna be ugly (searching
#             through each users CSV or something... ugh))
# TODO: validate event URLs (no slashes, no periods, etc)

# returns datetime object for x days from now (for cookie expiration dates)
def get_x_daysFromNow(x):
    return datetime.today() + timedelta(days=x)

# takes in an email message to send, and sends it on a separate thread so main process doesn't hang
def send_async_email(app, msg):
    with app.app_context():
        # print "about to send email"
        mail.send(msg)
        # print "sent email"

# default/index page
@app.route("/", methods=["GET","POST"])
def splashScreen():
    _username = request.cookies.get('username')
    # if there was a cookie with the key "username":
    if _username:
        usr = db_h.User(_username)
        if usr.verifiedEmail!="0":
            resp = make_response(render_template('userHome.html', username=usr.username, firstname=usr.firstname, lastname=usr.lastname, verified=False))
            resp.set_cookie('username', usr.username, expires=get_x_daysFromNow(90))
            return resp
        # retrieve list of names of events based on their URLs
        _ownedEventsList = usr.getListOfOwnedEventNames()
        # split CSV of urls into a list
        _ownedEventsUrlsList = usr.ownedEventsCSV.split(",")
        # prepend a slash to each URL, so it can be given straight to the userHome.html template
        for url in _ownedEventsUrlsList:
            # url = '"/'+url+'"'
            url = '/'+url

        # zip both lists together: creates an equal length list of tuples
        _ownedEventsZipped = zip(_ownedEventsList,_ownedEventsUrlsList)

        # send user to userHome with appropriate arguments
        resp = make_response(render_template('userHome.html', username=usr.username, firstname=usr.firstname, lastname=usr.lastname, ownedeventszipped=_ownedEventsZipped, verified=True))
        # (re)set cookie with username to expire 90 days from now
        resp.set_cookie('username', _username, expires=get_x_daysFromNow(90))
        return resp
    # POST method means script was sent login data by user:
    if request.method == "POST":
        usr = db_h.User(request.form.get('username'))
        # hashPassIn is the raw password entered by the user plus the salt from the database
        _hashPassIn = hash_pass(request.form.get('password') + usr.salt)
        # if the password the user entered doesn't match the password in the database:
        if _hashPassIn != usr.password:
            # keep user at login screen, with "bad password!" shown to user
            return render_template('login.html', badPass=True)
        # otherwise, password was good, so user can log in and redirect to welcome screen:
        resp = make_response(redirect(url_for('splashScreen')))
        # reset username cookie to expire 90 days from now
        resp.set_cookie('username', usr.username, expires=get_x_daysFromNow(90))
        return resp
    # GET method means user is logging in for the first time:
    else:
        return render_template('login.html', badlogin=False)

@app.route("/logout")
def logout():
    # redirect to index and call function splashScreen
    resp = make_response(redirect(url_for("splashScreen")))
    # delete username cookie
    resp.set_cookie('username', '', expires=0)
    return resp

@app.route("/register", methods=["GET","POST"])
def register():
    # POST method means data was sent by user
    if request.method == "POST":
        # check if first password matches second password
        if request.form.get('password') != request.form.get('passwordconfirm'):
            # if not, then have them reenter info
            return render_template('register.html', diffPasswords=True)
        # if passwords do match:
        else:
            # try opening connection to database:
            try:
                _userUsername = request.form.get('username')

                usr = db_h.User(_userUsername, False)

                usr.firstname = request.form.get('firstname')
                usr.lastname = request.form.get('lastname')
                usr.email = request.form.get('email')
                usr.assignPassAndSalt()
                usr.assignVerifiedEmail()
                # checking valid email against regexp for it
                validEmailBool = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', usr.email)
                if validEmailBool == None:
                    return render_template('register.html', badEmail=True)
                usr.email = request.form.get('email')
                usr.insert()

                msg = Message(
                        'Hello, %s!' % usr.firstname,
                        sender='timsemailforlols@google.com',
                        recipients=[usr.email]
                        )
                msg.body = render_template("registerEmail.txt", firstname=usr.firstname, username=usr.username, validation=usr.verifiedEmail)
                msg.html = render_template("registerEmail.html", firstname=usr.firstname, username=usr.username, validation=usr.verifiedEmail)
                # mail.send(msg)
                thr = Thread(target=send_async_email, args=[app, msg])
                thr.start()
                # redirect user to splashScreen
                resp = make_response(redirect(url_for('splashScreen')))
                # add cookie with username to expire in 90 days
                resp.set_cookie('username', usr.username, expires=get_x_daysFromNow(90))
                return resp
            except Exception as e:
                print e;
                # TODO: make sure Exception e is 1062 duplicate entry?
                # TODO: query database for someone with the username already.  If
                #     returned is not None, then there is someone with that username
                return render_template('register.html', diffPasswords=False, duplicateUser=True)
    # GET method means user is here for the first time or is confirming email address:
    else:
        # try pulling username and validation code out of GET method
        # TODO: make sure this all works right on initial registration (maybe surround in try/except or something?)
        # TODO: what happens if user clicks to verify email twice?  Goes through properly the first time, and then...?
        #                 Maybe check if username already has validation==1 or not?
        username=request.args.get('username')
        validation=request.args.get('validation')
        if not username:
            return render_template('register.html', diffPasswords=False, duplicateUser=False)
        if db_h.User.usernameAvail(username):
            return redirect(url_for('register'))
        usr=db_h.User(username)

        if usr.verifiedEmail == validation:
            # Validation code was good!!  Reset code in table to 0
            usr.verifiedEmail="0"
            usr.updateVerifiedemail()
            # redirect user to splashScreen
            resp = make_response(redirect(url_for('splashScreen')))
            # add cookie with username to expire in 90 days
            resp.set_cookie('username', username, expires=get_x_daysFromNow(90))
            return resp
        return render_template('register.html', diffPasswords=False, duplicateUser=False)

@app.route("/createEvent", methods=["GET","POST"])
def createEvent():
    # confirm user is logged in
    _username = request.cookies.get('username')
    # if they are not, redirect to the splashScreen
    if not _username:
        return redirect(url_for('splashScreen'))
    # otherwise, pull user data from database:
    if db_h.User.usernameAvail(_username):
        return redirect(url_for('splashScreen'))
    usr=db_h.User(_username)

    # POST method implies data being passed, trying to create event:
    if request.method == "POST":
        # if doesn't have value for eventName, then still trying to pick a Url
        if not request.form.get('eventName'):
            eventUrl=request.form.get('eventUrl')
            if db_h.Event.eventUrlAvail(eventUrl):
                # move on to second stage of creation, picking name and stuff
                # set cookie with eventUrl, temporary, will be destroyed in stage two
                resp = make_response(render_template('createEvent.html', firstname=usr.firstname, UrlInUse=False, eventUrl=eventUrl))
                resp.set_cookie('eventUrl',eventUrl, expires=get_x_daysFromNow(2))
                return resp
            # if event Url is in database, have user select a different one:
            else:
                return render_template('createEvent.html', firstname=_firstname, UrlInUse=True)
        # if have form value for eventName, then already have cookie stored with eventUrl
        else:
            eventUrl = request.cookies.get('eventUrl')
            eventName = request.form.get('eventName')
            eventDesc = request.form.get('eventDesc')

            event = db_h.Event(eventUrl, False)
            event.eventName = eventName
            event.eventDesc = eventDesc
            event.insert()

            usr.appendToOwnedEventsCSV(eventUrl)

            resp = make_response(redirect(url_for('splashScreen')))
            resp.set_cookie('eventUrl', '', expires=0)
            return resp
    # GET method means user is here for first time, allow to check Url availability:
    else:
        return render_template('createEvent.html', firstname=usr.firstname, firstTime=True)

@app.route('/validateEmail')
def resendValidationEmail():
    # TODO: allow users to edit their email address
    username=request.args.get('username')
    validation=request.args.get('validation')
    # here for first time, so send them an email:
    if username is None:
        # confirm user is logged in
        _username = request.cookies.get('username')
        # if they are not, redirect to the splashScreen
        if not _username:
            return redirect(url_for('splashScreen'))
        if db_h.User.usernameAvail(_username):
            return redirect(url_for('splashScreen'))
        # otherwise, pull user data from database:
        usr=db_h.User(_username)
        msg = Message(
                'Validating %s\'s email!' % usr.firstname,
                sender='timsemailforlols@google.com',
                recipients=[usr.email]
        )
        msg.body = render_template("registerEmail.txt", firstname=usr.firstname, username=usr.username, validation=usr.verifiedEmail)
        msg.html = render_template("registerEmail.html", firstname=usr.firstname, username=usr.username, validation=usr.verifiedEmail)
        thr = Thread(target=send_async_email, args=[app, msg])
        thr.start()
        # redirect user to splashScreen
        # TODO: add argument to splashScreen to display a "sent another validation email!"
        resp = make_response(redirect(url_for('splashScreen')))
        # add cookie with username to expire in 90 days
        resp.set_cookie('username', usr.username, expires=get_x_daysFromNow(90))
        return resp
    if db_h.User.usernameAvail(username):
        return redirect(url_for('register'))
    usr=db_h.User(username)
    if usr.verifiedEmail == validation:
        # Validation code was good!!  Reset code in table to 1
        usr.verifiedEmail="0"
        usr.updateVerifiedemail()
        # redirect user to splashScreen
        resp = make_response(redirect(url_for('splashScreen')))
        # add cookie with username to expire in 90 days
        resp.set_cookie('username', usr.username, expires=get_x_daysFromNow(90))
        return resp

# TODO: resend verification email if a new email is entered
@app.route('/editUser', methods=["GET","POST"])
def editUser():
    # confirm user is logged in
    _username = request.cookies.get('username')
    # if they are not, redirect to the splashScreen
    if not _username:
        return redirect(url_for('splashScreen'))
    # otherwise, pull user data from database:
    if db_h.User.usernameAvail(_username):
        return redirect(url_for('splashScreen'))
    usr=db_h.User(_username)
    # TODO: revalidate new email address
    # GET means that this is the first time here, so show page allowing user to edit their info
    if request.method=="GET":
        return render_template('editUser.html', firstname=usr.firstname, lastname=usr.lastname, email=usr.email)
    # POST means that the form has already been submitted, time to execute it
    new_firstname=request.form.get('firstname')
    new_lastname=request.form.get('lastname')
    new_email=request.form.get('email')
    usr.firstname=new_firstname
    usr.lastname=new_lastname
    usr.email=new_email
    usr.updateFirstname()
    usr.updateLastname()
    usr.updateEmail()
    # Throw user back to "/" and view the splashScreen/userHome.
    return make_response(redirect(url_for('splashScreen')))

# <eventUrl> is a variable that matches with any other URL to check if it's a valid eventUrl
@app.route("/<eventUrl>", methods=["GET","POST"])
def showEvent(eventUrl):
    # confirm user is logged in
    _username = request.cookies.get('username')
    # POST method means user clicked the "follow" button, since it's just a blank form
    if request.method == "POST":
        usr=db_h.User(_username)
        usr.appendToFollowedEventsCSV(eventUrl)
        return redirect(url_for('showEvent', eventUrl=eventUrl))
    userLoggedIn = False
    subscribed = False
    # if they are, show event page with "follow" button
    if _username:
        if db_h.User.usernameAvail(_username):
            return redirect(url_for('splashScreen'))
        usr=db_h.User(_username)
        userLoggedIn = True
        # TODO: put this in database_handling:
        subscribed = db_h.Event.is_EventUrl_in_EventUrlCSV(eventUrl, usr.followedEventsCSV)

    # eventUrl is avail, so event does not exist.  Redirect to splashScreen
    if db_h.Event.eventUrlAvail(eventUrl):
        return redirect(url_for('splashScreen'))
    event = db_h.Event(eventUrl)
    return render_template('showEvent.html', eventUrl=eventUrl, eventName=event.eventName, eventDesc=event.eventDesc, userLoggedIn=userLoggedIn, subscribed=subscribed)

# Hidden URL never shown to user, for testing only and to be removed before production
# Gives ability to call MySQL code to reset the databases without logging into MySQL
@app.route('/KILL_DB')
def killDb():
    db_h.killDb()
    print "################ DB killed ################"

    resp = make_response(redirect(url_for('splashScreen')))
    resp.set_cookie('username', '', expires=0)
    return resp
