import os

import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask.scaffold import F
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import csv
from datetime import date

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Create dictionaries associating the numbers needed for each dining hall/meal for the HUDS links and their names
meals = {"Breakfast": 0, "Lunch": 1, "Dinner": 2}
dhalls = {"Cabot": 14, "Pfoho": 14, "Dunster": 14, "Mather": 14, "Quincy": "08", "Adams": 14, "Eliot": 14, "Kirkland": 14, "Lowell": 15, "Winthrop": 14, "Leverett": 14, "Fly-By": "09", "Annenberg": 30, "Currier": 14}
          

@app.route("/")
def index():

    # date code from https://www.programiz.com/python-programming/datetime/current-datetime
    # Get today's date
    today = date.today()

    # See if the user chose a dhall and meal
    if 'dhallval' and 'mealval' in session:
        dhall = session["dhallval"]
        meal = session["mealval"]
        print("DHALL ", dhall, " MEAL ", meal)
        fdate = today.strftime("%m-%d-%Y")
        # If so, access the link for their choices and today's date
        response = requests.get(f"http://www.foodpro.huds.harvard.edu/foodpro/menu_items.asp?date={fdate}&type={dhall}&meal={meal}")

        # Make sure the website loaded successfully
        print(response.status_code)
        if response:
            # code from: https://stackoverflow.com/questions/9662346/python-code-to-remove-html-tags-from-a-string
            old = response.text
            # Remove the html tags from the website text
            cleantext = BeautifulSoup(old, "lxml").text
            # Clean the text using regex by splitting it at the words before and after the menu items themselves.
            x = re.split("Qty", cleantext, 1)
            y = re.split("Create", x[1],1)
            
            mealname = ""

            # Find the meal name in the meals dictionary based on the number saved in the session variable
            # code from: https://www.geeksforgeeks.org/python-get-key-from-value-in-dictionary/
            for key, value in meals.items():
                if value == meal:
                    mealname = key
            
            # Return to home page and display the menu
            return render_template("index.html", cleantext=y[0], dhallval=session['dhallname'], mealval=mealname)

        # If the website didn't load, go back to the home page with an error message
        else:
            print("Error.")
            return render_template("index.html", cleantext="Error")
            # Return an apology of some kind

    # If there is not a dining hall/meal stored in the session variable, use Annenberg Breakfast as the default
    else:
        # Request the link for Annenberg Breakfast
        response = requests.get(f"http://www.foodpro.huds.harvard.edu/foodpro/menu_items.asp?date={fdate}&type=30&meal=0")
        print(response.status_code)
        if response:
            # code from: https://stackoverflow.com/questions/9662346/python-code-to-remove-html-tags-from-a-string
            old = response.text
            print(old)
            cleantext = BeautifulSoup(old, "lxml").text
            x = re.split("Qty", cleantext, 1)
            y = re.split("Create", x[1],1)
            
            return render_template("index.html", cleantext=y[0], dhallval = "Annenberg", mealval="Breakfast")
        
        # If the website didn't load, go back to the home page with an error message
        else:
            print("Error.")
            return render_template("index.html", cleantext="Error")
            # Return an apology of some kind
    

@app.route("/dhall", methods=["POST", "GET"])
def dhall():
    if request.method == "POST":
        # Set session variables from the dhall and meal filled out in the form, return to home page
        dhall = request.form.get("dhall")
        meal = request.form.get("meal")
        session['dhallname'] = dhall
        print("dhall ", dhall)
        session['dhallval'] = dhalls.get(dhall)
        session['mealval'] = meals.get(meal)
        return redirect('/')
    
    else:
        # Load the form with data from the dhall and meal dictionaries
        return render_template("dhall.html", dhalls=dhalls, meals=meals)

# Let user add to databases
@app.route("/submit", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        # Create database for websites, then add user input
        connection = sqlite3.connect("harv.db")
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS sites (id INTEGER PRIMARY KEY, title TEXT, url TEXT UNIQUE)")
        toadd = (request.form.get("name"), request.form.get("website"))
        cursor.execute("INSERT INTO sites (title, url) VALUES (?, ?)", toadd)
        connection.commit()
        connection.close()
        return redirect('/')

    else:
        return render_template("submit.html")

@app.route("/pages", methods=["GET"])
def pages():
    # Load database
    connection = sqlite3.connect("harv.db")
    cursor = connection.cursor()

    # code from: https://stackoverflow.com/questions/2887878/importing-a-csv-file-into-a-sqlite3-database-table-using-python
    # Open the csv file I uploaded that contains a list of websites.
    with open('Harvard Websites.csv','r', encoding="utf-8-sig") as toadd:
        # csv.DictReader uses first line in file for column headings by default
        dr = csv.DictReader(toadd) # comma is default delimiter
        print("dr ", dr)
        newsites = []
        for i in dr:
            newsites.append((i['title'], i['url']))

    # Add the sites from the csv file to the database 
    cursor.executemany("INSERT INTO sites (title, url) VALUES (?, ?);", newsites)

    added = cursor.execute("SELECT title, url FROM sites")
    
    # Add sites to buy dictionary
    buy = {}
    for i in added:
        buy[i[0]] = i[1]

    connection.commit()
    connection.close()

    # Display everything in buy on pages.html--all the sites will display
    return render_template("pages.html", buy=buy)
    
@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        connection = sqlite3.connect("harv.db")
        cursor = connection.cursor()
        purchases = cursor.execute("SELECT title, url FROM sites")

        keyword = request.form.get("site")

        list = {}

        # Search for the keyword the user inputted in the purchases database
        # Use regex "find all"--if it's not an empty list, add the results to list, the list of results.
        for i in purchases:
            x = re.findall(str(keyword), str(i[1]))
            print("x ", x)
            if x != []:
                print("ii ", i)

                list[i[0]] = i[1]
                print("ii[0] ", i[0])
                print("ii[1] ", i[1])
        
        connection.commit()
        connection.close()

        # Add the results to the results page
        return render_template("results.html", list=list)
        
    else:
        return render_template("search.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            print("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            print("must provide password")
        
        # Ensure password and confirm password match
        elif request.form.get("password") != request.form.get("confirmation"):
            print("must provide matching passwords")

        # Ensure username doesn't exist already
        connection = sqlite3.connect("harv.db")
        cursor = connection.cursor()
        table = cursor.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(table) >= 1:
            print("That username already exists")

        # Insert user into database
        toadd = (request.form.get("username"), generate_password_hash(request.form.get("password")))
        cursor.execute("INSERT INTO users (username, hash) VALUES (?, ?)", toadd)
        connection.commit()
        connection.close()

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            print("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            print("must provide password")

        # Query database for username
        connection = sqlite3.connect("harv.db")
        cursor = connection.cursor()
        rows = cursor.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            print("invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        connection.commit()
        connection.close()

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