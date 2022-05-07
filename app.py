import os

from cs50 import SQL
from flask import Flask, send_file, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, format_number
from markupsafe import Markup
import urllib.parse
import requests
import sqlite3
import pandas as pd
import time

# Configure application.
app = Flask(__name__)

# Ensure templates are auto-reloaded.
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter.
app.jinja_env.filters["format_number"] = format_number

# Configure session to use filesystem (instead of signed cookies).
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database.
db = SQL("sqlite:///financials.db")

# After Request
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Select Company
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Select a company"""

    # Get the user_id for the current session.
    user_id = session["user_id"]
    print(user_id)

    # Get user's first name, last name, and email address.
    rows = db.execute("SELECT * FROM Users WHERE id = ?", user_id)
    first_name = rows[0]["first_name"]
    last_name = rows[0]["last_name"]
    email = rows[0]["email"]
    user_details = first_name + last_name + "(" + email + ")"

    # User reached route via POST (as by submitting a form via POST).
    if request.method == "POST":

        cik = request.form.get("cik")

        # Return error if no ticker is provided somehow.
        if not request.form.get("cik"):
            return apology("Please select a company.")

        # This function is used to recursively extract all keys in the JSON file obtained from
        # the SEC.
        # Function taken from:
        #   https://stackoverflow.com/questions/43752962/how-to-iterate-through-a-nested-dict
        def get_all_keys(data):
            # List out all keys that should be ignored. These are not keys that we care about.
            # Rather, we care about keys representing account identifiers (e.g. Revenues).
            keys_to_ignore = ['dei', 'USD', 'label', 'description', 'units', 'shares']
            for key, value in data.items():
                if key not in keys_to_ignore:
                    yield key
            if isinstance(value, dict):
                if key not in keys_to_ignore:
                    yield from get_all_keys(value)

        # Call the SEC Edgar API. If successful, a JSON file will be obtained.
        try:
            # This is the URL used to get the JSON data.
            sec_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
            # The SEC requires basic header information, which is the user's name and email.
            headers = {"user-agent": user_details}
            # Get the data.
            response = requests.get(sec_url, headers=headers)
            # Sleep briefly (as the SEC limits the amount of requests per second).
            time.sleep(.1)
            # Define a variable called "data" that contains JSON-formatted info under the standard
            # "us-gaap" key.
            data = response.json()['facts']['us-gaap']
        except:
            # If the data cannot be obtained from the SEC, return an apology, telling the user to
            # select another company.
            return apology(Markup("Sorry, looks like this company information is not available. \
                                   Please <span id='select-company'><a href='/'>select another company</a></span>."))

        # Store CIK as a variable in the format as obtained from EDGAR (with no leading zeroes).
        cik = response.json()['cik']

        # Store the company name in a variable.
        entity_name = response.json()['entityName']

        # Create a blank list that will hold the "account_ids"
        account_ids = []

        # Create a list of dictionary items to ignore.
        # Ignore certain hard-coded words that appear in all JSON files.
        items_to_ignore = ['cik', 'entityName', 'facts', 'dei']

        # Ignore all keys nested directly under the "dei" key, as this information is not needed.
        for key in response.json()['facts']['dei'].keys():
                items_to_ignore.append(key)

        # Ignore all keys nested directly under the "facts" key, as this information is not needed.
        for key in response.json()['facts'].keys():
                items_to_ignore.append(key)

        # Loop through the JSON and append the remaining keys to account_ids list.
        for x in get_all_keys(data):
            if(x not in items_to_ignore):
                account_ids.append(x)

        # Create a blank dictionary of account_ids (e.g. "Assets") and units (e.g. "USD").
        unit_keys = {}

        # Update the dictionary of account_ids and units.
        for x in account_ids:
            try:
                edgar_units = [key for key in data[x]['units'].keys()][0]
                unit_keys[x] = edgar_units
            # If there is a key error, ignore and continue looping to get as much financial
            # information as possible.
            except KeyError:
                continue

        # Create an empty data frame containing all needed fields.
        combined_df = pd.DataFrame(columns=['start','end','val','accn','fy','fp','form','filed','frame','units','account_id','cik','entity_name'])

        # Create a temporary data frame (df) for each account_id and then append it to the combined
        # data frame (combined_df).
        for key, value in unit_keys.items():
            try:
                df = pd.DataFrame(data[key]['units'][value])
                df['cik'] = cik
                df['entity_name'] = entity_name
                df['account_id'] = key
                df['units'] = value
                combined_df = pd.concat([combined_df, df])
            # If there is a key error, ignore and continue looping to get as much financial
            # information as possible.
            except KeyError:
                continue

        # Insert the combined data frame (combined_df) into a SQL table.
        conn = sqlite3.connect('financials.db')
        # This will overwrite any previously-existing table for any given user.
        combined_df.to_sql(f'RawFinancials_{user_id}', conn, if_exists='replace', index=False)

        # Create an empty data frame with all fields.
        combined_df = pd.DataFrame(columns=['label','description','units','account_id','cik','entity_name'])

        # Create a temporary data frame (df) for each account_id and then append it to the combined
        # data frame (combined_df).
        for account in account_ids:
            try:
                df = pd.DataFrame(data[account])
                df['account_id'] = account
                df['cik'] = cik
                df['entity_name'] = entity_name
                combined_df = pd.concat([combined_df, df])
            # If there is a key error, ignore and continue looping to get as much information as
            # possible.
            except KeyError:
                continue

        # Drop the "units" column in the account_ids dataframe, as it is not needed.
        combined_df = combined_df.drop('units', axis=1)

        # Insert the combined data frame (combined_df) into a SQL table.
        conn = sqlite3.connect('financials.db')
        # This will overwrite any previously-existing table for any given user.
        combined_df.to_sql(f'AccountAttributes_{user_id}', conn, if_exists='replace', index=False)

        # Export financials to CSV so users can download if desired.
        conn = sqlite3.connect('financials.db', isolation_level=None, detect_types=sqlite3.PARSE_COLNAMES)
        db_df = pd.read_sql_query(f"SELECT RF.cik, RF.entity_name, RF.start, RF.end, RF.fy, RF.fp, RF.account_id, AA.label AS account, RF.units, CAST(RF.val AS REAL) AS val, RF.form FROM RawFinancials_{user_id} AS RF LEFT JOIN AccountAttributes_{user_id} AS AA ON RF.account_id = AA.account_id ORDER BY account, end, start, fy, fp", conn)
        db_df.to_csv(f'csv_files/user_{user_id}_export.csv', index=False)

        # Redirect user to the financials page.
        return render_template("thanks.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Get a full list of ticker symbols and CIKs from the SEC.
        url = "https://www.sec.gov/include/ticker.txt"
        file = urllib.request.urlopen(url)

        # Create a blank list which will contain dictionaries of tickers and CIKs.
        ticker_list = []

        # Loop through the SEC's text file, appending the dictionaries to the ticker_list.
        for line in file:
            dicti = {}
            decoded_line = line.decode("utf-8")
            (ticker, cik) = decoded_line.split()
            dicti["Ticker"] = ticker.upper()
            dicti["CIK"] = cik.zfill(10)
            ticker_list.append(dicti)

        # Define a function usd to help sort the list of tickers.
        def sorter_helper(e):
            return e['Ticker']

        # Sort the list of tickers so users can easily find tickers.
        ticker_list.sort(key=sorter_helper)

        # Direct user to the index page to select a company.
        return render_template("index.html", ticker_list=ticker_list)

# Export to CSV
@app.route("/export", methods=["GET","POST"])
@login_required
def export():
    """Export data to CSV"""

    # Get the user_id for the current session.
    user_id = session["user_id"]

    # Export the file to CSV. Note that file names are unique to each individual user.
    # From https://stackoverflow.com/questions/70416656/how-to-download-a-file-from-flask-with-send-from-directory
    try:
       path = f'csv_files/user_{user_id}_export.csv'
       return send_file(path,mimetype='text/csv', attachment_filename=f'user_{user_id}_export.csv', as_attachment=True)
    except Exception as e:
        return str(e)

# About
@app.route("/about", methods=["GET", "POST"])
def about():
    """Provides high-level information about the project"""

    # Direct user to the About page.
    return render_template("about.html")

# View Financials
@app.route("/financials", methods=["GET", "POST"])
@login_required
def financials():
    """Show the financial information requested"""

    # Get the user_id for the current session.
    user_id = session["user_id"]

    try:
        # Get company financial information from the financials database.
        financials = db.execute(f"SELECT RF.cik, RF.entity_name, RF.start, RF.end, RF.fy, RF.fp, RF.account_id, AA.label AS account, RF.units, CAST(RF.val AS REAL) AS val, RF.form FROM RawFinancials_{user_id} AS RF LEFT JOIN AccountAttributes_{user_id} AS AA ON RF.account_id = AA.account_id WHERE AA.label IS NOT NULL ORDER BY account, end, start, fy, fp")

        # Bring the user to the financials page with details provided.
        return render_template("financials.html", financials=financials, format_number=format_number)

    except:
        # If the tables do not yet exist, an error will occur; thus, ask the user to select a
        # company.
        return apology(Markup("Please <span id='select_company'><a href='/'>select a company</a></span>."))

# Log In
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id.
    session.clear()

    # User reached route via POST (as by submitting a form via POST).
    if request.method == "POST":

        # Ensure username was submitted.
        if not request.form.get("username"):
            return apology("Please provide a username.")

        # Ensure password was submitted.
        elif not request.form.get("password"):
            return apology("Please provide a username.")

        # Query database for username.
        rows = db.execute("SELECT * FROM Users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct.
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("Invalid username and/or password. Please try again.")

        # Remember which user has logged in.
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page.
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect).
    else:
        # Bring the user to the login page.
        return render_template("login.html")

# Log Out
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id.
    session.clear()

    # Redirect user to login form.
    return redirect("/")

# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id.
    session.clear()

    # User reached route via POST (as by submitting a form via POST).
    if request.method == "POST":

        # Ensure new username was submitted.
        if not request.form.get("username"):
            return apology("Please provide a username.")

        # Ensure first name was submitted.
        if not request.form.get("first_name"):
            return apology("Please provide a first name.")

        # Ensure last name was submitted.
        if not request.form.get("last_name"):
            return apology("Please provide a last name.")

        # Ensure new email was submitted.
        if not request.form.get("email"):
            return apology("Please provide an email address.")

        # Ensure password was submitted.
        elif not request.form.get("password"):
            return apology("Please provide a password.")

        # Ensure password confirmation was submitted.
        elif not request.form.get("confirmation"):
            return apology("Please provide a password confirmation.")

        # Ensure password matches password confirmation.
        if not request.form.get("password") == request.form.get("confirmation"):
            return apology("Password does not match password confirmation. Please try again.")

        # Query database for username
        rows = db.execute("SELECT * FROM Users WHERE username = ?", request.form.get("username"))

        # Return an error if the username already exists.
        if len(rows) > 0:
            return apology("username already exists")

        # Register user.
        db.execute(
            "INSERT INTO Users (first_name, last_name, email, username, hash) VALUES (?, ?, ?, ?, ?)", request.form.get("first_name"), request.form.get("last_name"), request.form.get("email"), request.form.get("username"), generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8))

        # Query database for username.
        rows = db.execute("SELECT * FROM Users WHERE username = ?", request.form.get("username"))

        # Remember which user has logged in.
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page.
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect).
    else:
        # Bring the user to the register page.
        return render_template("register.html")