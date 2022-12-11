import os
import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///bulldogbrain.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Sets the homepage of the website to the tasks displayed in the urgent view
@app.route("/")
@login_required
def home():
    return redirect("/urgent")

# Form for users to add classes
@app.route("/makingClasses", methods=["GET", "POST"])
@login_required
def makingClasses():
    # if statement to check for a submission
    if request.method == "POST":
       
        # sets the value of title to the inputted course title
        title = request.form.get("title")

        # SQL syntax that inserts the title of a users course into the courses database
        db.execute("INSERT INTO courses (title, user_id) VALUES(?, ?)",
            title,
            session["user_id"])

        # returns user to list page
        return redirect("/list")
        
    else:
        # returns the original page if no submission was made
        return render_template("makingClasses.html")

# Form for users to add assignments
@app.route("/assignmentsform", methods=["GET", "POST"])
@login_required
def assignmentsform():
    
    # sets the value of courseTitle to one of the users courses from a dropdown list
    courseTitle = db.execute("SELECT title FROM courses WHERE user_id = ?", session["user_id"])
    
    # if statement to check for a submission
    if request.method == "POST":

        # sets values of each variable to that of the form input equivilant
        title = request.form.get("title")
        course = request.form.get("course")
        deadline = request.form.get("deadline")
        importance = request.form.get("importance")
        notes = request.form.get("notes")

        # populates the assignments table with the info inputted by the user
        db.execute("INSERT INTO assignments (title, course, deadline, importance, notes, user_id) VALUES(?, ?, ?, ?, ?, ?)",
                        title,
                        course,
                        deadline,
                        importance,
                        notes,
                        session["user_id"])
        
        # returns user to list page
        return redirect("/list")
        
    else:
        # returns the original page if no submission was made
        return render_template("assignmentsform.html", courseTitle=courseTitle)

@app.route("/eventsform", methods=["GET", "POST"])
@login_required
def eventsform():
    
    # if statement to check for a submission
    if request.method == "POST":

        # sets values of each variable to that of the form input equivilant
        title = request.form.get("title")
        location = request.form.get("location")
        start_date = request.form.get("start_date")
        start_time = request.form.get("start_time")
        end_date = request.form.get("end_date")
        end_time = request.form.get("end_time")
        importance = request.form.get("importance")
        notes = request.form.get("notes")

        # populates the events table with the info inputted by the user
        db.execute("INSERT INTO events (title, location, start_date, start_time, end_date, end_time, importance, notes, user_id) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        title,
                        location,
                        start_date,
                        start_time,
                        end_date,
                        end_time,
                        importance,
                        notes,
                        session["user_id"])
        
        # returns user to list page
        return redirect("/list")
    else:
        # returns the original page if no submission was made
        return render_template("eventsform.html")

#
@app.route("/today", methods=["GET", "POST"])
@login_required
def dayChronoligical():

    # sets variable to the current date and time of the user's timezone
    current = datetime.datetime.now()
    # pulls only the date from the current variable
    localdate = current.strftime("%Y-%m-%d")
        
    """List view of assignments and events"""
    # query that populates assignments table if the assignments are not compeleted and where the assignment's deadline = today's date
    assignments = db.execute(
            "SELECT id, title, course, date(deadline) as date, CASE WHEN StrFTime('%H', deadline) % 12 = 0 THEN 12 ELSE StrFTime('%H', deadline) % 12 END || ':' || StrFTime('%M', deadline) || ' ' || CASE WHEN CAST(StrFTime('%H', deadline) AS INTEGER) > 12 THEN 'PM' ELSE 'AM' END 'time', importance, notes FROM assignments WHERE user_id = ? AND completed != 1 AND date(deadline) = ? ORDER BY deadline ASC", session["user_id"], localdate)
    # query that populates events table if the events are not compeleted and where the events's end date = today's date
    events = db.execute(
            "SELECT event_id, title, location, start_date, CASE WHEN StrFTime('%H', start_time) % 12 = 0 THEN 12 ELSE StrFTime('%H', start_time) % 12 END || ':' || StrFTime('%M', start_time) || ' ' || CASE WHEN CAST(StrFTime('%H', start_time) AS INTEGER) > 12 THEN 'PM' ELSE 'AM' END 'start_time', end_date, CASE WHEN StrFTime('%H', end_time) % 12 = 0 THEN 12 ELSE StrFTime('%H', end_time) % 12 END || ':' || StrFTime('%M', end_time) || ' ' || CASE WHEN CAST(StrFTime('%H', end_time) AS INTEGER) > 12 THEN 'PM' ELSE 'AM' END 'end_time', importance, notes FROM events WHERE user_id = ? AND completed != 1 AND end_date = ? ORDER BY start_date ASC, start_time ASC", session["user_id"], localdate)
    
    # if statement to check for a submission
    if request.method == "POST":

        # updates table when assignments or events are checked off
        assignment_id = request.form.get("assignment_id")
        db.execute("UPDATE assignments SET completed = '1' WHERE id = ?", assignment_id)
        event_id = request.form.get("event_id")
        db.execute("UPDATE events SET completed = '1' WHERE event_id = ?", event_id)

        # returns user to today page
        return redirect("/today")
    else:
        # returns the original page if no submission was made
        return render_template("/dayChronoligical.html", assignments=assignments, events=events)


@app.route("/urgent", methods=["GET", "POST"])
@login_required
def dayImportance():

    current = datetime.datetime.now()
    localdate = current.strftime("%Y-%m-%d")

    """List view of assignments and events"""
    assignments = db.execute(
            "SELECT id, title, course, date(deadline) as date, CASE WHEN StrFTime('%H', deadline) % 12 = 0 THEN 12 ELSE StrFTime('%H', deadline) % 12 END || ':' || StrFTime('%M', deadline) || ' ' || CASE WHEN CAST(StrFTime('%H', deadline) AS INTEGER) > 12 THEN 'PM' ELSE 'AM' END 'time', importance, notes FROM assignments WHERE user_id = ? AND completed != 1 AND date(deadline) = ? ORDER BY importance DESC", session["user_id"], localdate)
    events = db.execute(
            "SELECT event_id, title, location, start_date, CASE WHEN StrFTime('%H', start_time) % 12 = 0 THEN 12 ELSE StrFTime('%H', start_time) % 12 END || ':' || StrFTime('%M', start_time) || ' ' || CASE WHEN CAST(StrFTime('%H', start_time) AS INTEGER) > 12 THEN 'PM' ELSE 'AM' END 'start_time', end_date, CASE WHEN StrFTime('%H', end_time) % 12 = 0 THEN 12 ELSE StrFTime('%H', end_time) % 12 END || ':' || StrFTime('%M', end_time) || ' ' || CASE WHEN CAST(StrFTime('%H', end_time) AS INTEGER) > 12 THEN 'PM' ELSE 'AM' END 'end_time', importance, notes FROM events WHERE user_id = ? AND completed != 1 AND end_date = ? ORDER BY importance DESC", session["user_id"], localdate)
    
    if request.method == "POST":

        assignment_id = request.form.get("assignment_id")
        db.execute("UPDATE assignments SET completed = '1' WHERE id = ?", assignment_id)
        event_id = request.form.get("event_id")
        db.execute("UPDATE events SET completed = '1' WHERE event_id = ?", event_id)

        return redirect("/urgent")
    else:
        return render_template("/dayImportance.html", assignments=assignments, events=events)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password was retyped
        elif not request.form.get("confirmation"):
            return apology("must retype password", 400)

        # Establishes variables for the returned values of the register form
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure retyped password matches password
        if confirmation != password:
            return apology("passwords must match", 400)

        # Makes sure user inputs a unique username
        users = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(users) > 0:
            return apology("Unique username required", 400)

        # Query database for username
        id = db.execute("INSERT INTO users (username, hash) VALUES(?, ?)",
                        username,
                        generate_password_hash(password))
        session["user_id"] = id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/archive", methods=["GET", "POST"])
def archive():
    """List view of assignments and events"""
    # Populates the list html table
    assignments = db.execute(
        "SELECT id, title, course, date(deadline) as date, CASE WHEN StrFTime('%H', deadline) % 12 = 0 THEN 12 ELSE StrFTime('%H', deadline) % 12 END || ':' || StrFTime('%M', deadline) || ' ' || CASE WHEN CAST(StrFTime('%H', deadline) AS INTEGER) > 12 THEN 'PM' ELSE 'AM' END 'time', importance, notes FROM assignments WHERE user_id = ? AND completed = 1 ORDER BY deadline ASC", session["user_id"])
    events = db.execute(
        "SELECT event_id, title, location, start_date, CASE WHEN StrFTime('%H', start_time) % 12 = 0 THEN 12 ELSE StrFTime('%H', start_time) % 12 END || ':' || StrFTime('%M', start_time) || ' ' || CASE WHEN CAST(StrFTime('%H', start_time) AS INTEGER) > 12 THEN 'PM' ELSE 'AM' END 'start_time', end_date, CASE WHEN StrFTime('%H', end_time) % 12 = 0 THEN 12 ELSE StrFTime('%H', end_time) % 12 END || ':' || StrFTime('%M', end_time) || ' ' || CASE WHEN CAST(StrFTime('%H', end_time) AS INTEGER) > 12 THEN 'PM' ELSE 'AM' END 'end_time', importance, notes FROM events WHERE user_id = ? AND completed = 1 ORDER BY start_date ASC, start_time ASC", session["user_id"])
    
    if request.method == "POST":
        assignment_id = request.form.get("assignment_id")
        db.execute("UPDATE assignments SET completed = '0' WHERE id = ?", assignment_id)
        event_id = request.form.get("event_id")
        db.execute("UPDATE events SET completed = '0' WHERE event_id = ?", event_id)

        return redirect("/archive")
    else:
        return render_template("archive.html", assignments=assignments, events=events)


@app.route("/list", methods=["GET", "POST"])
def list():
    
    """List view of assignments and events"""
    assignments = db.execute(
            "SELECT id, title, course, date(deadline) as date, CASE WHEN StrFTime('%H', deadline) % 12 = 0 THEN 12 ELSE StrFTime('%H', deadline) % 12 END || ':' || StrFTime('%M', deadline) || ' ' || CASE WHEN CAST(StrFTime('%H', deadline) AS INTEGER) > 12 THEN 'PM' ELSE 'AM' END 'time', importance, notes FROM assignments WHERE user_id = ? AND completed != 1 ORDER BY deadline ASC", session["user_id"])
    events = db.execute(
            "SELECT event_id, title, location, start_date, CASE WHEN StrFTime('%H', start_time) % 12 = 0 THEN 12 ELSE StrFTime('%H', start_time) % 12 END || ':' || StrFTime('%M', start_time) || ' ' || CASE WHEN CAST(StrFTime('%H', start_time) AS INTEGER) > 12 THEN 'PM' ELSE 'AM' END 'start_time', end_date, CASE WHEN StrFTime('%H', end_time) % 12 = 0 THEN 12 ELSE StrFTime('%H', end_time) % 12 END || ':' || StrFTime('%M', end_time) || ' ' || CASE WHEN CAST(StrFTime('%H', end_time) AS INTEGER) > 12 THEN 'PM' ELSE 'AM' END 'end_time', importance, notes FROM events WHERE user_id = ? AND completed != 1 ORDER BY start_date ASC, start_time ASC", session["user_id"])
    
    if request.method == "POST":
        assignment_id = request.form.get("assignment_id")
        db.execute("UPDATE assignments SET completed = '1' WHERE id = ?", assignment_id)
        event_id = request.form.get("event_id")
        db.execute("UPDATE events SET completed = '1' WHERE event_id = ?", event_id)

        return redirect("/list")
    else:
        return render_template("list.html", assignments=assignments, events=events)