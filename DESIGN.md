# Hermès | Design Document

## TL;DR

* Flask is the (Python) module used as the application's framework
* HTML files are used to contain the rendered content
    * The user interface (UI) is accessible via a web browser
* Bootstrap and CSS are used to style the UI
* Jinja is used to dynamically update HTML information
* A SQLite3 database is used to store financial records

## Libraries Used
* The following Python libraries / modules / tools were used to create this application:
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

* Importantly, Python libraries such as [python-edgar](https://pypi.org/project/python-edgar/) already exist and could have made the project easier to implement
* However, for learning purposes, these libraries were not used
* Only commonly-used libraries (such as [pandas](https://pandas.pydata.org/)) were used to build the core features of the app

## Database Design
A relational database is needed in this project in order to accomplish two things:

1. Maintain a table of users (including user password hash keys for login validation)
1. Store tables of requested financial information that has been transformed into tabular formats

The financials.db database setup is as follows:

* A `Users` table stores user information, including:
    * ID - an auto-generated integer that is unique to each user
    * First Name - this must be sent to the SEC
    * Last Name - this must be sent to the SEC
    * Email - this must be sent to the SEC
    * username - this is used for users to log in
    * hash - this is a hash key of passwords entered (and is cross-checked when users log in)
* Tables containing Raw Financial information are created on an as-needed basis
    * These are the tables which store financial information pulled via the SEC EDGAR API
    * Multiple versions of this table can be created - one for each user
        * The reason for doing this is to ensure one user's activity (e.g. request to see financial information of a company) are not conflicting with activity of other users
    * The naming convention of these tables is: `RawFinancials_{user_id}`, where `{user_id}` represents a user's unique ID from the Users table in financials.db
    * To see the table schema, please refer to the `queries.sql` file (specifically, the statement used to create `RawFinancials`)
    * This table created or replaced each time a user requests company financial information
* Tables containing Account Attributes are created on an as-needed basis
    * Multiple versions of this table can be created - one for each user
        * The reason for doing this is to ensure one user's activity (e.g. request to see financial information of a company) are not conflicting with activity of other users
    * The naming convention of these tables is: `AccountAttributes_{user_id}`, where `{user_id}` represents a user's unique ID from the Users table in financials.db
    * To see the table schema, please refer to the `queries.sql` file (specifically, the statement used to create `AccountAttributes`)
    * This table created or replaced each time a user requests company financial information

## User Interface Design
The UI is built using the languages / frameworks listed below. Additionally, explanations for the purposes of each HTML file are outlined.

* HTML
    * layout.html
        * Forms the main layout of the UI which is applied to all other HTML files
        * It contains HTML for the `<head>` tag information, navigation menu, etc.
        * The following pages are available via the navigation menu:
            * about.html (when logged in or logged out)
            * financials.html (when logged in)
            * index.html (when logged in)
            * login.html (when not logged in)
            * logout.html (when logged in)
            * register.html (when not logged in)
    * about.html
        * Lets users know - at a high level - what the application is for
    * apology.html
        * Used to present users with error messages if and when they arise
        * This page is returned to end users when the `apology()` function is used in the main application (app.py)
    * financials.html
        * Presents a table of financial information after it is requested via the form in index.html
        * It also allows users to export financial information to CSV
    * index.html
        * Enables users to select a ticker symbol and request financial information (via a form)
    * login.html
        * Enables users to log into the application
    * logout.html
        * Enables users to log out of the application
    * register.html
        * Enables users to register (which is required in order to use the app)
    * thanks.html
        * The page that appears immediately after a user clicks the Get Financials button from index.html
        * It serves as a buffer page between requesting financial information in index.html and seeing the financial information in financials.html
        * When this page appears, the request was successful and information will be returned to the user in financials.html
* Bootstrap
    * [Bootstrap](https://getbootstrap.com) is leveraged to quickly and efficiently style the website
        * This framework is more than enough from a style perspective, given that the key focus of this app is to obtain raw data
        * The relevant code can be found in the `<head>` tag in the layout.html file
* CSS
    * CSS (via styles.css) is used sparingly to make small adjustments to the bootstrap-driven UI styling conventions
        * Fonts in the output tables (showing financial information) are slightly reduced
        * Hyperlink colors are changed to orange (for purely aesthetic reasons)
        * The project name (Hermès, at the top-left corner of the app) is adjusted (again, for aesthetics)


Overall, the UI is meant to be simple, straightforward, and easy to navigate.

## Getting Financial Information
The most important aspect of the application is quickly retrieving and transforming the financial information in a way that is easy for users to consume (i.e. CSV format). This is done via the app.py script.

Below are a few highlights of the design details.

### Showing the List of Companies
* When users load index.html (the home page), they are presented with a drop-down menu that shows all tickers available
* This was implemented as follows:
    * A text file at https://www.sec.gov/include/ticker.txt is read
    * For each line in that text file:
        * A dictionary containing ticker symbols and CIKs (which are numbers representing individual companies) is created
        * Each dictionary is appended to a list (called `ticker_list`)
        * The `ticker_list` is then sorted so end users can easily find a company from the drop-down list
        * In index.html, a form containing a select control is used with this Jinja loop to present all ticker symbols to the users:
            ```
            {% for ticker in ticker_list %}
                <option value="{{ ticker['CIK'] }}">{{ ticker["Ticker"] }}</option>
            {% endfor %}
            ```
        * When a user selects a ticker symbol, a corresponding CIK is selected as the `cik` value that is used to make an API call to the SEC

### Requesting the Data (API Call)
* When the user selects a ticker and submits the request in index.html, the `cik` value in the form is passed to the `index()` function in app.py
* The `cik` placed in the URL used for the API call (https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json)
    * Note that the `cik` values in the URL must be 10 characters long, so leading zeros must be used
* The API call is made using `requests.get(sec_url, headers=headers)`, where `headers` represents a concatenation of the user's first name, last name, and email address (the latter of which is in parentheses)
    * This header information is required by the SEC in order for users to make API calls
    * If for some reason the CIK does not provide any data, an error message appears (showing apology.html, rendered via the `apology()` function in app.py)
    * A JSON file is then returned from the SEC
        * This file contains all the information needed to create the final output (financial data in a tabular format)

### Parsing the JSON File
(Note that parsing the JSON file was the most difficult part of the project.)

* The JSON file described above must be parsed into data frames
* The JSON files returned from the SEC look roughly like this:
    ```
    {
        "cik": 1783879,
        "entityName": "Robinhood Markets, Inc.",
        "facts": {
            "us-gaap": {
                "AccountsPayableAndAccruedLiabilitiesCurrent": {
                    "label": "Accounts Payable and Accrued Liabilities, Current",
                    "description": "Sum of the carrying values as of the balance sheet date of obligations incurred through that date and due within one year (or the operating cycle, if longer), including liabilities incurred (and for which invoices have typically been received) and payable to vendors for goods and services received, taxes, interest, rent and utilities, accrued salaries and bonuses, payroll taxes and fringe benefits.",
                    "units": {
                        "USD": [
                            {
                                "end": "2020-12-31",
                                "val": 104649000,
                                "accn": "0001783879-21-000029",
                                "fy": 2021,
                                "fp": "Q2",
                                "form": "10-Q",
                                "filed": "2021-08-18"
                            },
                            {
                                "end": "2020-12-31",
                                "val": 104649000,
                                "accn": "0001783879-21-000054",
                                "fy": 2021,
                                "fp": "Q3",
                                "form": "10-Q",
                                "filed": "2021-10-29"
                            },
                            {
                                "end": "2020-12-31",
                                "val": 104649000,
                                "accn": "0001783879-22-000044",
                                "fy": 2021,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2022-02-24",
                                "frame": "CY2020Q4I"
                            },
    ```
* Specifically, the dictionaries nested in the `us-gaap` key of the JSON file is the relevant information needed
    * This is the actual financial information that users will eventually be able to see and export
* Directly under the `us-gaap` key, the Account ID (`AccountsPayableAndAccruedLiabilitiesCurrent`) is presented
    * For each Account ID, there is a dictionary containing `label`, `description`, and `units` keys
        * The values associated with the `label` and `description` keys, as well as the values associated with the `cik`, `entityName` and Account ID (e.g. `AccountsPayableAndAccruedLiabilitiesCurrent` keys (that are higher up in the JSON file), will ultimately be inserted into the `Accountattributes_{user_id}` table
* Additionally, for each key within the `us-gaap` dictionary (e.g. `AccountsPayableAndAccruedLiabilitiesCurrent`), there is a `units` key
    * The value of the `units` key depends on the value of the Account ID key (e.g. `AccountsPayableAndAccruedLiabilitiesCurrent`)
    * Thus, a dictionary (called `unit_keys`) that maps an Account ID to corresponding `units` values must also be created
        * This dictionary is created by first creating a list of Account IDs (called `account_ids`) and then using the following loop:
            ```
            # Update the dictionary of account_ids and units.
            for x in account_ids:
                try:
                    edgar_units = [key for key in data[x]['units'].keys()][0]
                    unit_keys[x] = edgar_units
                # If there is a key error, ignore and continue looping to get as much financial
                # information as possible.
                except KeyError:
                    continue
            ```
* A shell dataframe (`combined_df`) is created which will contain the raw financial information (that eventually goes into the `RawFinancials_{user_id}` table)
* To add data to the shell dataframe, the following loop is done to 1) create data frames (`df`) for each Account ID (`AccountsPayableAndAccruedLiabilitiesCurrent`), and 2) append the smaller data frames (`df`) to the combined data frame (`combined_df`)
    ```
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
    ```

### Updating the SQL Database
* After the data frame is created, a SQL table is created (or replaced) in financials.db, using this code:
    ```
    # Insert the combined data frame (combined_df) into a SQL table.
    conn = sqlite3.connect('financials.db')
    # This will overwrite any previously-existing table for any given user.
    combined_df.to_sql(f'RawFinancials_{user_id}', conn, if_exists='replace', index=False)
    ```
* Additionally, the same approach used to create `RawFinancials_{user_id}` is also used to create `AccountAttributes_{user_id}`
* Once these tables are created, the following SQL is used to render the table in financials.html:
    ```
    SELECT
      RF.cik,
      RF.entity_name,
      RF.start,
      RF.end,
      RF.fy,
      RF.fp,
      RF.account_id,
      AA.label AS account,
      RF.units,
      CAST(RF.val AS REAL) AS val,
      RF.form
    FROM
      RawFinancials_{user_id} AS RF
    LEFT JOIN
      AccountAttributes_{user_id} AS AA
      ON RF.account_id = AA.account_id
    WHERE
      AA.label IS NOT NULL
    ORDER BY
      account,
      end,
      start,
      fy,
      fp;
    ```

### Presenting the Data
* A Jinja loop is used in financials.html in order to present each line item returned from the above SQL query, as follows:
```
<table class="table table-sm">
    <thead>
        <tr>
            <th>CIK</th>
            <th>Company</th>
            <th>Start Date</th>
            <th>End Date</th>
            <th>Fiscal Year</th>
            <th>Fiscal Period</th>
            <th>Form</th>
            <th>Account</th>
            <th>Units</th>
            <th>Value</th>
        </tr>
    </thead>
    <tbody>
        {% for financial in financials %}
        <tr>
            <td>{{ financial["cik"] }}</td>
            <td>{{ financial["entity_name"] }}</td>
            <td>{{ financial["start"] }}</td>
            <td>{{ financial["end"] }}</td>
            <td>{{ financial["fy"] }}</td>
            <td>{{ financial["fp"] }}</td>
            <td>{{ financial["form"] }}</td>
            <td>{{ financial["account"] }}</td>
            <td>{{ financial["units"] }}</td>
            <td>{{ format_number(financial["val"]) }}</td>
        </tr>
    {% endfor %}
    </tbody>
</table>
```

## Exporting to CSV
* When a user requests financial information, not only is the information available to view on the financials.html web page, but it is also available to export to CSV
    * This is critical for users, as the will want to transform the data in various ways
* The following code is used to generate the CSV file (immediately when financial information is requested)
    ```
    # Export financials to CSV so users can download if desired.
    conn = sqlite3.connect('financials.db', isolation_level=None, detect_types=sqlite3.PARSE_COLNAMES)
    db_df = pd.read_sql_query(f"SELECT RF.cik, RF.entity_name, RF.start, RF.end, RF.fy, RF.fp, RF.account_id, AA.label AS account, RF.units, CAST(RF.val AS REAL) AS val, RF.form FROM RawFinancials_{user_id} AS RF LEFT JOIN AccountAttributes_{user_id} AS AA ON RF.account_id = AA.account_id ORDER BY account, end, start, fy, fp", conn)
    db_df.to_csv(f'csv_files/user_{user_id}_export.csv', index=False)
    ```
* Why generate a CSV immediately upon request?
    * In this way, the CSV is simply already available and does not have to be generated upon clicking the Export to CSV button (i.e. this implementation would seem to be faster than creating a CSV on-the-fly)
* When a new request is made, the CSV file is overwritten with new company information
* The CSV files include User IDs (i.e. files are named `user_{user_id}_export.csv`) so that one user's activity does not impact other users' activities

## Registering, Logging In, and Logging Out
* The implementation of the login, log out, and register functionalities follows that of the Finance Problem Set found in Week 9, but with some minor differences
    * Upon registering, users must also include their names and email addresses, as that information must be sent to the SEC when executing API calls
    * Additional validations are performed in app.py to ensure these form fields are populated
* These features are not central to the project, but are useful in order to ensure multiple users can leverage the app on a stand-alone basis

## Helper Functions
* Note that essentially the same helper functions in the Finance Problem Set found in Week 9 were leveraged in this project, with minor tweaks
    * No meme is being generated, so no special characters are being replaced in the apology messages
    * Not all numbers are presented in USD, so the `usd()` function has been generalized to `format_number()`