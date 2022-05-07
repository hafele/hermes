-- Create table of users information, usernames, and password hash keys.
-- Note that this must be created before the application can be used.
CREATE TABLE Users (
  id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  username TEXT NOT NULL,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT NOT NULL,
  hash TEXT NOT NULL
);

-- Create table of raw financial information.
-- Note that this is just for illustration purposes. This table will be created and replaced
-- when for each user (when requested, via selecting a company).
CREATE TABLE RawFinancials (
  id INTEGER NOT NULL, -- Auto-ID
  cik INTEGER NOT NULL, -- 0001652044
  entity_name TEXT NOT NULL, -- Alphabet Inc.
  account_id TEXT, -- AccountsPayableCurrent
  start_period TEXT, -- "start": "2014-12-31",
  end_period TEXT, -- "end": "2014-12-31",
  amount REAL, -- "val": 1715000000,
  accn TEXT, -- "accn": "0001652044-15-000005",
  fiscal_year TEXT, -- "fy": 2015,
  fiscal_period TEXT, -- "fp": "Q3",
  form TEXT, -- "form": "10-Q",
  filing_date TEXT, -- "filed": "2015-10-29"
  frame TEXT,
  PRIMARY KEY(id)
);

-- Create table of raw account attributes.
-- Note that this is just for illustration purposes. This table will be created and replaced
-- when for each user (when requested, via selecting a company).
CREATE TABLE IF NOT EXISTS AccountAttributes (
  label TEXT,
  description TEXT,
  account_id TEXT,
  cik INTEGER,
  entity_name TEXT
);

-- This is an example of a query used to get financial information from the tables created.
SELECT
  RF.cik,
  RF.entity_name,
  RF.start,
  RF.end,
  RF.fy,
  RF.fp,
  AA.label AS account,
  RF.units,
  RF.val,
  RF.form
FROM
  RawFinancials AS RF
LEFT JOIN
  AccountAttributes AS AA
  ON RF.account_id = AA.account_id;

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