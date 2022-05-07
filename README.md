# Hermès | User Manual

## Video
* [CS50 Final Project - Hermès](https://www.youtube.com/watch?v=TYdS3NpOD9Y)

## Background and Purpose
To obtain financial information of US publicly traded companies, financial analysts, researchers, and investors have historically resorted to doing one of two things:

1. Extracting (often modified) data from third-party sources such as Yahoo! Finance or Bloomberg
1. Extracting (raw) data directly from individual SEC filings that are in PDF, HTML, or Excel format

Often, neither of these approaches are ideal. Users often want to quickly obtain unmodified financial information across multiple filings that can be easily transformed, and without paying a lot of money to do so.

Hermès is a simple application that allows anyone to extract unmodified company financial information from the SEC's EDGAR database via their [RESTful API](https://www.sec.gov/edgar/sec-api-documentation).

## Tools Used
The following tools and languages are needed to use the application.

1. HTML
1. CSS
1. Python (Flask)
1. SQL (SQLite3)

## Configuration
Configuring this application is fairly straightforward. The steps (to run the code via a GitHub codespace) are as follows:

1. Add all code to the machine that will be running the program
    * The root-level folder can be named "final"
    * All folders should be nested as shown in this repository
1. Ensure all necessary Python libraries / modules / tools are installed, including:
    * cs50
    * flask
    * flask_session
    * functools
    * markupsafe
    * os
    * pandas
    * requests
    * sqlite3
    * time
    * urllib
    * werkzeug.security
1. Set up SQLite3 database
    * The database name should be: financials.db
        * If it needs to be created from scratch, execute the following in the command line:
            * `sqlite3 financials.db`
            * Confirm the creation of the database by typing `y` then `Enter`
    * Create the Users table in the database
        * To do this, copy/paste the first SQL statement in the queries.sql file
1. Run Flask via the command line
    * Navigate to the root directory (e.g. `cd final`)
    * Run flask using `flask run`
1. Open the GitHub preview URL in a browser
    * Recommended: Use Safari or Chrome


## Application Usage
The next steps can be followed once the GitHub preview URL is entered into a browser.

### Step 1: About
* Navigate to the About page and read the information

### Step 2: Register
* Navigate to the Register page and register an account
    * Fill out all fields in the form:
        * First Name
        * Last Name
        * Email
        * username
        * password
        * password confirmation
    * After successfully registering, users will be redirected to the home page where they can select a company

### Step 3: Select A Company
* Select a company
    * Use the drop-down box to select a company's ticker
    * Click Get Financials
    * After a few seconds (and if successful), a message (in a green banner) will appear telling you to navigate to the View Financials page.

### Step 4: View Financial Information
* View the company financial information that was requested in the previous step
    * Click the hyperlink in the green banner (or select View Financials from the navigation bar)
    * On the View Financials page, users will see a table of all unmodified historical company information

### Step 5: Export to CSV
* Export the company financials to CSV
    * On the View Financials page (at the top-left), click Export to CSV
    * A CSV file will be downloaded to users' machines, where it can be used in whatever way is needed

### Step 6: Log Out
* Log out of the application when necessary
    * Click the Log Out link at the top-right side of the page

### Step 7: Log In
* Log back in to use the application again
    * Click the Log In link at the top-right side of the page
    * Enter a username and password
    * Click the Log In (form) button