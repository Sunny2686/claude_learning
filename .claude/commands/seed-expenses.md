---
description: Seed realistic dummy expenses for a specific user
argument-hint: "<user_id> <count> <months>"
allowed-tools: Read, Bash(python3:*)
---

Read database/db.py to understand the expenses table
schema, the db connection pattern, and the database
file name.

User Inputs: $ARGUMENTS

## Step 1 - Parse Arguments

Extract from $ARGUMENTS:

- user_id - integer
- count - integer, number of expenses to create
- months - integer, interval to spread the expenses

If any argument is missing or not valid data type, sto and say:
"Usages: /seed-expenses <user_id> <count> <months>
Example: /seed-expenses 2 40 6"

## Step 2 - Verify user exist

    Before generating anything, confirm user_id exists in the user table if not available stop and say: "No user found with id <user_id>"

## Step 3 - Generate and insert expenses

1. Spread expenses randomly across the past <months> months
2. Use these categories with realistic Indian demands and expenses (in Rupee):
   - Food: 50–800
   - Transport: 20–500
   - Bills: 200–3000
   - Health: 100–2000
   - Entertainment: 100–1500
   - Shopping: 200–5000
   - Other: 50–1000

3. Use the database connection pattern from db.py - never hardcode database filename
4. Use parametarised queries only no string formatting in SQL
5. Insert all expenses in single transaction - roll back everything if any one insert failed

## Step 4 - Confirm

Print:

- how many expenses inserted
- the data range they span
- sample of 5 inserted records
