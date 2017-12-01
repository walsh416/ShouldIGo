
from flask import Flask, render_template, request, redirect, url_for, make_response, send_from_directory, session, escape
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_sslify import SSLify
from datetime import datetime, timedelta
from threading import Thread
import hashlib, os, re, cgi
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


# NOTE: 11/27/17: changed what template this renders, now it just goes to login.html or userhome.html,
#           and splashScreen.html is never touched.  I think.
# default/index page
@application.route("/", methods=["GET","POST"])
def splashScreen():
    # TODO: if they don't follow or own any events, but have validated their email, then this
    #           screen is just blank with the navbar at the top.  That's sad.
    #           Instead, it'd be dope to at least have
    resentValidationEmail=False
    if request.args.get('resentValidationEmail') is not None:
        resentValidationEmail = request.args.get('resentValidationEmail')
    if 'username' in session:
        _username = session['username']
    else:
        _username = request.cookies.get('rememberme')
    # if there was a cookie with the key "username":
    if _username:
        usr = db_h.User_alch.query.filter_by(username=_username).first()
        if usr.verifiedEmail!="0":
            session['username'] = usr.username
            # resp = make_response(render_template('mustVerify.html', username=usr.username, firstname=usr.firstname, lastname=usr.lastname, verified=False, resentValidationEmail=str(resentValidationEmail)))
            resp = make_response(render_template('userHome.html', username=usr.username, firstname=usr.firstname, lastname=usr.lastname, verified=False, resentValidationEmail=str(resentValidationEmail)))
            return resp
        # retrieve list of names of events based on their URLs
        _ownedEventsList = usr.getListOfOwnedEventNames()
        # split CSV of urls into a list
        _ownedEventsUrlsList = usr.ownedEventsCSV.split(",")
        # prepend a slash to each URL, so it can be given straight to the userHome.html template
        for url in _ownedEventsUrlsList:
            url = '/'+url
        # zip both lists together: creates an equal length list of tuples
        _ownedEventsZipped = zip(_ownedEventsList,_ownedEventsUrlsList)

        _followedEventsList = usr.getListOfFollowedEventNames()
        _followedEventsUrlsList = usr.followedEventsCSV.split(",")
        for url in _followedEventsUrlsList:
            url = '/'+url
        _followedEventsZipped = zip(_followedEventsList,_followedEventsUrlsList)

        session['username'] = usr.username
        # send user to userHome with appropriate arguments
        resp = make_response(render_template('userHome.html', username=usr.username, firstname=usr.firstname, lastname=usr.lastname, ownedeventszipped=_ownedEventsZipped, followedeventszipped=_followedEventsZipped, verified=True, resentValidationEmail=resentValidationEmail))
        # (re)set cookie with username to expire 90 days from now
        # resp.set_cookie('username', _username, expires=get_x_daysFromNow(90))
        return resp
    # POST method means script was sent login data by user:
    if request.method == "POST":
        usr = db_h.User_alch.query.filter_by(username=request.form.get('username')).first()
        # print usr
        if usr is None:
            session.pop('username', None)
            return render_template('login.html', badUser=True)
        if not usr.checkHashPass(request.form.get('password')):
            session.pop('username', None)
            # keep user at login screen, with "bad password!" shown to user
            return render_template('login.html', badPass=True)
        session['username'] = usr.username

        # Can't see home screen unless they have verified their email address
        if usr.verifiedEmail!="0":
            # resentValidationEmail didn't work in the UserHome template unless it was a string variable, not sure why...
            session['username'] = usr.username
            resp = make_response(render_template('mustVerify.html', username=usr.username, firstname=usr.firstname, lastname=usr.lastname, verified=False, resentValidationEmail=str(resentValidationEmail)))
            return resp
        # otherwise, password was good, so user can log in and redirect to welcome screen:
        resp = make_response(redirect(url_for('splashScreen')))
        # if user checked "remember me" box, set a cookie with their username to expire in 90 days
        if request.form.get('rememberme'):
            print "Setting rememberme cookie"
            resp.set_cookie('rememberme', usr.username, expires=get_x_daysFromNow(90))
        return resp
    # GET method means user is logging in for the first time:
    else:
        session.pop('username', None)
        return render_template('login.html', badlogin=False)

@application.route("/logout")
def logout():
    session.pop('username', None)
    # redirect to index and call function splashScreen
    resp = make_response(redirect(url_for("splashScreen")))
    # delete rememberme cookie
    resp.set_cookie('rememberme', '', expires=0)
    return resp

@application.route("/register", methods=["GET","POST"])
def register():
    # POST method means data was sent by user
    if request.method == "POST":
        print "in POST method of /register"
        # check if first password matches second password
        if request.form.get('password') != request.form.get('passwordconfirm'):
            print "Bad pass"
            # if not, then have them reenter info
            return render_template('register.html', diffPasswords=True)
        # if passwords do match:
        else:
            # try opening connection to database:
            _userUsername = request.form.get('username')
            print "Passwords match, username is: "+_userUsername
            if not db_h.usernameAvail(_userUsername):
                print _userUsername + " is not available"
                return render_template('register.html', diffPasswords=False, duplicateUser=True)

            # checking valid email against regexp for it
            _userEmail = request.form.get('email')
            validEmailBool = re.match('^[_a-z0-9-\+]+(\.[_a-z0-9-\+]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', _userEmail)
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

            session['username'] = usr.username
            # redirect user to splashScreen
            resp = make_response(redirect(url_for('splashScreen')))
            return resp
    # GET method means user is here for the first time or is confirming email address:
    else:
        print "in GET method of /register"
        # try pulling username and validation code out of GET method
        # TODO: make sure this all works right on initial registration (maybe surround in try/except or something?)
        # TODO: what happens if user clicks to verify email twice?  Goes through properly the first time, and then...?
        #                 Maybe check if username already has validation==1 or not?
        username=request.args.get('username')
        validation=request.args.get('validation')
        if not username:
            print "returning render_template(register.html) with no username arg"
            return render_template('register.html', diffPasswords=False, duplicateUser=False)
        if db_h.usernameAvail(username):
            print "returning redirect for 'register' since username is avail"
            return redirect(url_for('register'))

        # TODO: what if the following query returns a NoneType?
        usr = db_h.User_alch.query.filter_by(username=username).first()

        if usr.verifiedEmail == validation:
            # Validation code was good!!  Reset code in table to 0
            usr.verifiedEmail="0"
            db_h.alch_db.session.commit()

            session['username'] = username
            # redirect user to splashScreen
            resp = make_response(redirect(url_for('splashScreen')))
            print "Returning to splashScreen with verifiedEmail"
            return resp
        print "returning bottom render_template(register.html)"
        return render_template('register.html', diffPasswords=False, duplicateUser=False)

@application.route("/createEvent", methods=["GET","POST"])
def createEvent():
    # confirm user is logged in
    if 'username' in session:
        _username = session['username']
    else:
        _username = None
    # if they are not, redirect to the splashScreen
    if not _username:
        return redirect(url_for('splashScreen'))
    # otherwise, pull user data from database:
    if db_h.usernameAvail(_username):
        session.pop('username', None)
        return redirect(url_for('splashScreen'))
    usr = db_h.User_alch.query.filter_by(username=_username).first()

    if usr.verifiedEmail!="0":
        # resentValidationEmail didn't work in the UserHome template unless it was a string variable, not sure why...
        session['username'] = usr.username
        resp = make_response(render_template('mustVerify.html', username=usr.username, firstname=usr.firstname, lastname=usr.lastname, verified=False))
        return resp

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

                # TODO: change this cookie to a session variable so the site still works without cookies?
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
            dateFilter = request.form.get('datefilter')
            # TODO: force input in eventName and eventDesc
            # TODO: do something with this... duh.
            print("Printing Date Filter")
            print(dateFilter)
            print "print repr(eventDesc) : "+repr(eventDesc)

            if eventName is None or eventDesc is None:
                # return "Please fill in all fields!"
                # TODO: should actually be done in javascript, because here it's buried in a post method and yeah.
                pass

            event = db_h.Event_alch(url=eventUrl, name=eventName, desc=eventDesc)
            db_h.alch_db.session.add(event)
            db_h.alch_db.session.commit()

            usr.ownedEventsCSV += (eventUrl+",")
            db_h.alch_db.session.commit()

            # resp = make_response(redirect(url_for('splashScreen')))
            resp = make_response(redirect(url_for('showEvent', eventUrl=eventUrl)))
            resp.set_cookie('eventUrl', '', expires=0)
            return resp
    # GET method means user is here for first time, allow to check Url availability:
    else:
        return render_template('createEvent.html', firstname=usr.firstname, firstTime=True)

@application.route('/validateEmail')
def resendValidationEmail():
    username=request.args.get('username')
    validation=request.args.get('validation')
    # here for first time, so send them an email:
    if username is None:
        # confirm user is logged in
        if 'username' in session:
            _username = session['username']
        else:
            _username = None
        # if they are not, redirect to the splashScreen
        if not _username:
            return redirect(url_for('splashScreen'))
        if db_h.usernameAvail(_username):
            session.pop('username', None)
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
        session['username'] = usr.username
        resp = make_response(redirect(url_for('splashScreen', resentValidationEmail=True)))
        return resp
    if db_h.usernameAvail(username):
        return redirect(url_for('register'))
    usr = db_h.User_alch.query.filter_by(username=username).first()
    if usr.verifiedEmail == validation:
        # Validation code was good!!  Reset code in table to 0
        usr.verifiedEmail="0"
        db_h.alch_db.session.commit()
        # redirect user to splashScreen
        session['username'] = usr.username
        resp = make_response(redirect(url_for('splashScreen')))
        return resp

    # Allow users to delete their accounts.
    #
    # Remove their name from all followersCSV lists for events that they follow, remove their events from all followedEventsCSV lists for users that used to follow their events, delete their events, and then delete their account.

@application.route('/editUser', methods=["GET","POST"])
def editUser():
    # confirm user is logged in
    if 'username' in session:
        _username = session['username']
    else:
        _username = None
    # if they are not, redirect to the splashScreen
    if not _username:
        return redirect(url_for('splashScreen'))
    # otherwise, pull user data from database:
    if db_h.usernameAvail(_username):
        return redirect(url_for('splashScreen'))
    usr = db_h.User_alch.query.filter_by(username=_username).first()
    # GET means that this is the first time here, so show page allowing user to edit their info
    if request.method=="GET":
        deleteUser = request.args.get('wantsToDelete')
        if bool(deleteUser):
            # unfollow all events:
            for eventUrl in usr.followedEventsCSV.split(","):
                event = db_h.Event_alch.query.filter_by(eventUrl=eventUrl).first()
                if event is not None:
                    event.unfollowUser(usr.username)
            # Remove owned events from other people's followedEventsCSV:
            for eventUrl in usr.ownedEventsCSV.split(","):
                event = db_h.Event_alch.query.filter_by(eventUrl=eventUrl).first()
                if event is not None:
                    for username in event.followers.split(","):
                        user = db_h.User_alch.query.filter_by(username=username).first()
                        if user is not None:
                            user.unfollowEvent(eventUrl)
                    db_h.alch_db.session.delete(event)
            # Delete actual user entry
            db_h.alch_db.session.delete(usr)
            db_h.alch_db.session.commit()
            return redirect(url_for('logout'))
        return render_template('editUser.html', firstname=usr.firstname, lastname=usr.lastname, email=usr.email)
    # POST means that the form has already been submitted, time to execute it
    new_firstname=request.form.get('firstname')
    new_lastname=request.form.get('lastname')
    new_email=request.form.get('email')
    usr.firstname=new_firstname
    usr.lastname=new_lastname

    if usr.email != new_email:
        usr.email=new_email
        usr.assignVerifiedEmail()
        session['username'] = usr.username
        db_h.alch_db.session.commit()
        resp = make_response(redirect(url_for('resendValidationEmail')))
        return resp
    db_h.alch_db.session.commit()
    # Throw user back to "/" and view the splashScreen/userHome.
    return make_response(redirect(url_for('splashScreen')))

@application.route('/userEvents')
def userEvents():
    # TODO: make this not terrible, duh.  (probably pull old code with "zip"ing the CSVs together from the old userHome stuff)
    if 'username' in session:
        _username = session['username']
    else:
        _username = None
    if not _username:
        return redirect(url_for('splashScreen'))
    # otherwise, pull user data from database:
    if db_h.usernameAvail(_username):
        return redirect(url_for('splashScreen'))
    usr = db_h.User_alch.query.filter_by(username=_username).first()
    if usr.verifiedEmail!="0":
        session['username'] = usr.username
        resp = make_response(render_template('mustVerify.html', username=usr.username, firstname=usr.firstname, lastname=usr.lastname, verified=False))
        return resp
    return render_template('userEvents.html')

# <eventUrl> is a variable that matches with any other URL to check if it's a valid eventUrl
@application.route("/<eventUrl>", methods=["GET","POST"])
def showEvent(eventUrl):
    # RSVP-ing: Each event has CSVs of usernames that are going, maybe going, and not going.
    # CSVs are wiped clean when an event is updated (manually or by schedule)
    # Adding your name to one CSV removes it from the others (can't be both going and not going, ex)

    # TODO: only have one user object and one event object in here, instead of 18 nested ugly ones because Tim got lazy
    # eventUrl is avail, so event does not exist.  Redirect to splashScreen
    #EVENTURLHADNLING
    if db_h.eventUrlAvail(eventUrl):
        #return redirect(url_for('splashScreen'))
        return abort(404)

    # confirm user is logged in
    if 'username' in session:
        _username = session['username']
    else:
        _username = None

    # TODO: any way to reach here without being logged in?  If so, what then?
    # POST method means user clicked the "follow" button, since it's just a blank form
    if request.method == "POST":
        usr = db_h.User_alch.query.filter_by(username=_username).first()
        evnt = db_h.Event_alch.query.filter_by(eventUrl=eventUrl).first()
        if request.form.get('save'):
            new_eventName = request.form.get('eventName')
            new_eventDesc = request.form.get('eventDesc')
            evnt = db_h.Event_alch.query.filter_by(eventUrl=eventUrl).first()
            evnt.eventName=new_eventName
            evnt.eventDesc=new_eventDesc
            db_h.alch_db.session.commit()
            evnt.sendEmailToFollowers()
        if request.form.get('unfollow') and usr.followsEventUrl(eventUrl):
            usr.unfollowEvent(eventUrl)
            evnt.unfollowUser(_username)
            db_h.alch_db.session.commit()
        elif request.form.get('follow') and not usr.followsEventUrl(eventUrl):
            usr.followedEventsCSV += (eventUrl+",")
            evnt.followers += (_username+",")
            db_h.alch_db.session.commit()
        return redirect(url_for('showEvent', eventUrl=eventUrl))
    userLoggedIn = False
    subscribed = False
    owner = False
    # if they are logged in, show event page with "follow" button
    if _username:
        if db_h.usernameAvail(_username):
            return redirect(url_for('splashScreen'))
        usr = db_h.User_alch.query.filter_by(username=_username).first()
        event = db_h.Event_alch.query.filter_by(eventUrl=eventUrl).first()
        userLoggedIn = True
        owner = usr.ownsEventUrl(eventUrl)
        subscribed = db_h.is_EventUrl_in_EventUrlCSV(eventUrl, usr.followedEventsCSV)
        # If owner, and if they hit "edit" button, comes back with GET method for editing, and allows owner to edit it.
        wantsToEdit=request.args.get('wantsToEdit')
        wantsToDelete=request.args.get('wantsToDelete')
        goingReq=request.args.get('going')
        if goingReq is not None:
            # if goingReq=="yes":
            #     event.rsvp(usr.username, "yes")
            # elif goingReq=="maybe":
            #     event.rsvp(usr.username, "maybe")
            # elif goingReq=="no":
            #     event.rsvp(usr.username, "no")
            print "goingReq = "+goingReq
            event.rsvp(usr.username, goingReq)
            db_h.alch_db.session.commit()
        if owner and bool(wantsToEdit):
            return render_template('editEvent.html', eventUrl=eventUrl, eventName=event.eventName, eventDesc=event.eventDesc, userLoggedIn=userLoggedIn, subscribed=subscribed, owner=owner)
        if owner and bool(wantsToDelete):
            # TODO: some sort of javascript pop-up, either confirming they want to delete it or notifying them that they did?

            # remove event from all users' followedEventsCSV list, and from owner's ownedEventsCSV list:
            followersList=event.followers.split(',')
            for follower in followersList:
                followerUser = db_h.User_alch.query.filter_by(username=follower).first()
                if followerUser is not None:
                    followerUser.unfollowEvent(eventUrl)
                    # followerUser.unownEvent(eventUrl)
                    db_h.alch_db.session.commit()
            usr.unownEvent(eventUrl)
            # delete event itself
            db_h.alch_db.session.delete(event)
            db_h.alch_db.session.commit()
            return redirect(url_for('splashScreen'))
        going = event.getUsersRSVP(usr.username)
        yesUsers=[]
        for username in event.yesGoingCSV.split(","):
            if username is not None and username != "":
                user = db_h.User_alch.query.filter_by(username=username).first()
                yesUsers.append(user.firstname+" "+user.lastname)
        maybeUsers=[]
        for username in event.maybeGoingCSV.split(","):
            if username is not None and username != "":
                user = db_h.User_alch.query.filter_by(username=username).first()
                maybeUsers.append(user.firstname+" "+user.lastname)
        noUsers=[]
        for username in event.noGoingCSV.split(","):
            if username is not None and username != "":
                user = db_h.User_alch.query.filter_by(username=username).first()
                noUsers.append(user.firstname+" "+user.lastname)

        return render_template('showEvent.html', eventUrl=eventUrl, eventName=event.eventName, eventDesc=event.eventDesc, userLoggedIn=userLoggedIn, subscribed=subscribed, owner=owner, going=going, yesUsers=yesUsers, maybeUsers=maybeUsers, noUsers=noUsers)


    # eventUrl is avail, so event does not exist.  Redirect to splashScreen
    event = db_h.Event_alch.query.filter_by(eventUrl=eventUrl).first()
    # print "print repr(eventDesc) : "+repr(event.eventDesc)
    # TODO: make sure display works nicely for new lines, &, <, >, etc (shitty html stuff)
    #           But keep \n and whatnot safe in database so can display properly on "edit event"
    #       ----> pretty sure flask does this all automatically, just need to worry about
    #           newlines, which 'style="white-space: pre-wrap;"' takes care of in the HTML
    # prettyEventDesc = event.eventDesc.replace("\r\n","<br>\n")
    # print "print repr(prettyEventDesc) : "+repr(prettyEventDesc)
    return render_template('showEvent.html', eventUrl=eventUrl, eventName=event.eventName, eventDesc=event.eventDesc, userLoggedIn=userLoggedIn, subscribed=subscribed, owner=owner)
    # return render_template('showEvent.html', eventUrl=eventUrl, eventName=event.eventName, eventDesc=prettyEventDesc, userLoggedIn=userLoggedIn, subscribed=subscribed, owner=owner)


@application.errorhandler(404)
def page_not_found(e):
    # TODO: what about like "shouldigo.today/VALID_EVENT_NAME/foo" where it starts off
    #       validly but then wants a sub-directory or something?
    #       I don't know what it should do here, but it's something to think about --Tim 11/20
    if 'username' in session:
        _username = session['username']
    else:
        _username = None
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

    session.pop('username', None)
    resp = make_response(redirect(url_for('splashScreen')))
    return resp

@application.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(application.root_path, 'static'),'favicon.ico')
