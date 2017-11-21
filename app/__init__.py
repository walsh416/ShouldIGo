
from flask import Flask, render_template, request, redirect, url_for, make_response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_sslify import SSLify
from datetime import datetime, timedelta
from threading import Thread
import hashlib, os, re
import database_handling as db_h
from database_handling import alch_db
from flask import abort

application = Flask(__name__)

application.config.from_object('config')

alch_db.init_app(application)

mail = Mail(application)

# Only forces HTTPS if DEBUG=False, which should be used on AWS
# When running locally, trying to force HTTPS breaks it, so set DEBUG=True
sslify = SSLify(application)

# TODO: allow deletion of events, user accounts, etc
# TODO: send email to subscribers when an event is updated (given an event,
#             figuring out who is subscribed to it is gonna be ugly (searching
#             through each users CSV or something... ugh))
# TODO: validate event URLs (no slashes, no periods, etc)

# TODO: can still follow event if email not verified by navigating to its URL
#           But in user home doesn't show list of followed, shows "sorry, please verify"
#           Change around event templating to hide follow button until verified

# returns datetime object for x days from now (for cookie expiration dates)
def get_x_daysFromNow(x):
    return datetime.today() + timedelta(days=x)

# takes in an email message to send, and sends it on a separate thread so main process doesn't hang
def send_async_email(application, msg):
    with application.app_context():
        # print "about to send email"
        mail.send(msg)
        # print "sent email"


# default/index page
@application.route("/", methods=["GET","POST"])
def splashScreen():
    resentValidationEmail=False
    if request.args.get('resentValidationEmail') is not None:
        resentValidationEmail = request.args.get('resentValidationEmail')
    _username = request.cookies.get('username')
    # if there was a cookie with the key "username":
    if _username:
        usr = db_h.User_alch.query.filter_by(username=_username).first()
        if usr.verifiedEmail!="0":
            # resentValidationEmail didn't work in the UserHome template unless it was a string variable, not sure why...
            resp = make_response(render_template('userHome.html', username=usr.username, firstname=usr.firstname, lastname=usr.lastname, verified=False, resentValidationEmail=str(resentValidationEmail)))
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

        _followedEventsList = usr.getListOfFollowedEventNames()
        _followedEventsUrlsList = usr.followedEventsCSV.split(",")
        for url in _followedEventsUrlsList:
            url = '/'+url
        _followedEventsZipped = zip(_followedEventsList,_followedEventsUrlsList)

        # send user to userHome with appropriate arguments
        resp = make_response(render_template('userHome.html', username=usr.username, firstname=usr.firstname, lastname=usr.lastname, ownedeventszipped=_ownedEventsZipped, followedeventszipped=_followedEventsZipped, verified=True, resentValidationEmail=resentValidationEmail))
        # (re)set cookie with username to expire 90 days from now
        resp.set_cookie('username', _username, expires=get_x_daysFromNow(90))
        return resp
    # POST method means script was sent login data by user:
    if request.method == "POST":
        usr = db_h.User_alch.query.filter_by(username=request.form.get('username')).first()
        print usr
        if usr is None:
            return render_template('login.html', badUser=True)
        if not usr.checkHashPass(request.form.get('password')):
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

@application.route("/logout")
def logout():
    # redirect to index and call function splashScreen
    resp = make_response(redirect(url_for("splashScreen")))
    # delete username cookie
    resp.set_cookie('username', '', expires=0)
    return resp

@application.route("/register", methods=["GET","POST"])
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
            _userUsername = request.form.get('username')

            if not db_h.usernameAvail(_userUsername):
                print _userUsername + " is not available"
                return render_template('register.html', diffPasswords=False, duplicateUser=True)

            # checking valid email against regexp for it
            _userEmail = request.form.get('email')
            validEmailBool = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', _userEmail)
            if validEmailBool == None:
                return render_template('register.html', badEmail=True)

            usr = db_h.User_alch(firstname=request.form.get('firstname'), lastname=request.form.get('lastname'), username=request.form.get('username'), email=request.form.get('email'), rawpassword=(request.form.get('password')))
            db_h.alch_db.session.add(usr)
            db_h.alch_db.session.commit()

            msg = Message(
                    'Hello, %s!' % usr.firstname,
                    sender='timsemailforlols@google.com',
                    recipients=[usr.email]
                    )
            msg.body = render_template("registerEmail.txt", firstname=usr.firstname, username=usr.username, validation=usr.verifiedEmail)
            msg.html = render_template("registerEmail.html", firstname=usr.firstname, username=usr.username, validation=usr.verifiedEmail)
            thr = Thread(target=send_async_email, args=[application, msg])
            thr.start()
            # redirect user to splashScreen
            resp = make_response(redirect(url_for('splashScreen')))
            # add cookie with username to expire in 90 days
            resp.set_cookie('username', usr.username, expires=get_x_daysFromNow(90))
            return resp
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
        if db_h.usernameAvail(username):
            return redirect(url_for('register'))

        # TODO: what if the following query returns a NoneType?
        usr = db_h.User_alch.query.filter_by(username=username).first()

        if usr.verifiedEmail == validation:
            # Validation code was good!!  Reset code in table to 0
            usr.verifiedEmail="0"
            db_h.alch_db.session.commit()

            # redirect user to splashScreen
            resp = make_response(redirect(url_for('splashScreen')))
            # add cookie with username to expire in 90 days
            resp.set_cookie('username', username, expires=get_x_daysFromNow(90))
            return resp
        return render_template('register.html', diffPasswords=False, duplicateUser=False)

@application.route("/createEvent", methods=["GET","POST"])
def createEvent():
    # confirm user is logged in
    _username = request.cookies.get('username')
    # if they are not, redirect to the splashScreen
    if not _username:
        return redirect(url_for('splashScreen'))
    # otherwise, pull user data from database:
    if db_h.usernameAvail(_username):
        return redirect(url_for('splashScreen'))
    usr = db_h.User_alch.query.filter_by(username=_username).first()

    # POST method implies data being passed, trying to create event:
    if request.method == "POST":
        # if doesn't have value for eventName, then still trying to pick a Url
        if not request.form.get('eventName'):
            eventUrl=request.form.get('eventUrl')
            # checking valid url against regexp for it (start of string, one or more letters numbers underscores or dashes, end of string)
            validUrlBool = re.match('^[a-zA-Z0-9_\-]+$', eventUrl)
            if validUrlBool == None:
                # url is not valid (per the regexp), so force them to repick.
                return render_template('createEvent.html', firstname=usr.firstname, badUrl=True)
            elif db_h.eventUrlAvail(eventUrl):
                # move on to second stage of creation, picking name and stuff
                # set cookie with eventUrl, temporary, will be destroyed in stage two
                resp = make_response(render_template('createEvent.html', firstname=usr.firstname, UrlInUse=False, eventUrl=eventUrl))
                resp.set_cookie('eventUrl',eventUrl, expires=get_x_daysFromNow(2))
                return resp
            # if event Url is in database, have user select a different one:
            else:
                return render_template('createEvent.html', firstname=usr.firstname, UrlInUse=True)
        # if have form value for eventName, then already have cookie stored with eventUrl
        else:
            eventUrl = request.cookies.get('eventUrl')
            eventName = request.form.get('eventName')
            eventDesc = request.form.get('eventDesc')

            event = db_h.Event_alch(url=eventUrl, name=eventName, desc=eventDesc)
            db_h.alch_db.session.add(event)
            db_h.alch_db.session.commit()

            usr.ownedEventsCSV += (eventUrl+",")
            db_h.alch_db.session.commit()

            resp = make_response(redirect(url_for('splashScreen')))
            resp.set_cookie('eventUrl', '', expires=0)
            return resp
    # GET method means user is here for first time, allow to check Url availability:
    else:
        return render_template('createEvent.html', firstname=usr.firstname, firstTime=True)

@application.route('/validateEmail')
def resendValidationEmail():
    # TODO: revalidate email address after user edits it
    username=request.args.get('username')
    validation=request.args.get('validation')
    # here for first time, so send them an email:
    if username is None:
        # confirm user is logged in
        _username = request.cookies.get('username')
        # if they are not, redirect to the splashScreen
        if not _username:
            return redirect(url_for('splashScreen'))
        if db_h.usernameAvail(_username):
            return redirect(url_for('splashScreen'))
        # otherwise, pull user data from database:
        usr = db_h.User_alch.query.filter_by(username=_username).first()
        msg = Message(
                'Validating %s\'s email!' % usr.firstname,
                sender='timsemailforlols@google.com',
                recipients=[usr.email]
        )
        msg.body = render_template("registerEmail.txt", firstname=usr.firstname, username=usr.username, validation=usr.verifiedEmail)
        msg.html = render_template("registerEmail.html", firstname=usr.firstname, username=usr.username, validation=usr.verifiedEmail)
        thr = Thread(target=send_async_email, args=[application, msg])
        thr.start()
        # redirect user to splashScreen
        # TODO: add argument to splashScreen to display a "sent another validation email!"
        resp = make_response(redirect(url_for('splashScreen', resentValidationEmail=True)))
        # add cookie with username to expire in 90 days
        resp.set_cookie('username', usr.username, expires=get_x_daysFromNow(90))
        return resp
    if db_h.usernameAvail(username):
        return redirect(url_for('register'))
    usr = db_h.User_alch.query.filter_by(username=username).first()
    if usr.verifiedEmail == validation:
        # Validation code was good!!  Reset code in table to 1
        usr.verifiedEmail="0"
        db_h.alch_db.session.commit()
        # redirect user to splashScreen
        resp = make_response(redirect(url_for('splashScreen')))
        # add cookie with username to expire in 90 days
        resp.set_cookie('username', usr.username, expires=get_x_daysFromNow(90))
        return resp

# TODO: resend verification email if a new email is entered
@application.route('/editUser', methods=["GET","POST"])
def editUser():
    # confirm user is logged in
    _username = request.cookies.get('username')
    # if they are not, redirect to the splashScreen
    if not _username:
        return redirect(url_for('splashScreen'))
    # otherwise, pull user data from database:
    if db_h.usernameAvail(_username):
        return redirect(url_for('splashScreen'))
    usr = db_h.User_alch.query.filter_by(username=_username).first()
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
    db_h.alch_db.session.commit()
    # Throw user back to "/" and view the splashScreen/userHome.
    return make_response(redirect(url_for('splashScreen')))

# <eventUrl> is a variable that matches with any other URL to check if it's a valid eventUrl
@application.route("/<eventUrl>", methods=["GET","POST"])
def showEvent(eventUrl):
    # confirm user is logged in
    _username = request.cookies.get('username')
    # POST method means user clicked the "follow" button, since it's just a blank form
    if request.method == "POST":
        usr = db_h.User_alch.query.filter_by(username=_username).first()
        usr.followedEventsCSV += (eventUrl+",")
        db_h.alch_db.session.commit()
        return redirect(url_for('showEvent', eventUrl=eventUrl))
    userLoggedIn = False
    subscribed = False
    # if they are, show event page with "follow" button
    if _username:
        if db_h.usernameAvail(_username):
            return redirect(url_for('splashScreen'))
        usr = db_h.User_alch.query.filter_by(username=_username).first()
        userLoggedIn = True
        subscribed = db_h.is_EventUrl_in_EventUrlCSV(eventUrl, usr.followedEventsCSV)

    # eventUrl is avail, so event does not exist.  Redirect to splashScreen
    #EVENTURLHADNLING
    if db_h.eventUrlAvail(eventUrl):
        #return redirect(url_for('splashScreen'))
        return abort(404)
    event = db_h.Event_alch.query.filter_by(eventUrl=eventUrl).first()
    return render_template('showEvent.html', eventUrl=eventUrl, eventName=event.eventName, eventDesc=event.eventDesc, userLoggedIn=userLoggedIn, subscribed=subscribed)


@application.errorhandler(404)
def page_not_found(e):
    # TODO: what about like "shouldigo.today/VALID_EVENT_NAME/foo" where it starts off
    #       validly but then wants a sub-directory or something?
    #       I don't know what it should do here, but it's something to think about --Tim 11/20
    _username = request.cookies.get('username')
    # TODO: it'd be dope if both of these had some way to remember the URL, so that when the
    #       user goes to create an event with that URL, it's already auto-filled
    if not _username:
        return render_template('404page_login.html')
    else:
        return render_template('404page_create.html'),404

# Hidden URL never shown to user, for testing only and to be removed before production
# Gives ability to call MySQL code to reset the databases without logging into MySQL
@application.route('/KILL_DB')
def killDb():
    db_h.killDb()
    print "################ DB killed ################"

    resp = make_response(redirect(url_for('splashScreen')))
    resp.set_cookie('username', '', expires=0)
    return resp

@application.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(application.root_path, 'static'),'favicon.ico')
