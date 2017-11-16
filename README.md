# term-project-bdb-collective
term-project-bdb-collective created by GitHub Classroom

GitHub Classroom repo created by Timothy Walsh, Robert Gerami, Brendan Chin, Aslan Bakri, and Won Kuk (Jacob) Lee.

RUN WITH "python application.py"

11/15/2017 Update from Tim:
It's up on Amazon!  Used AWS-RDS to host the database, Elastic Beanstalk to host the Flask server, and Route53 to handle the DNS stuff.  Changed around the names of Python files and whatnot, now it's all run out of application.py instead of run.py ...it's a long story that involves how Amazon handles WSGI stuff and yeah.  Also created requirements.txt, which lists out all the python packages that are needed.  Elastic Beanstalk finds that and makes sure everything is installed.
To update the code on Amazon: zip up the .elasticbeanstalk directory, the app directory, requirements.txt, application.py, and config.py.  Upload that zip file to the elastic beanstalk console, and relaunch.
