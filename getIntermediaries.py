from flask import jsonify
import json
import sqlite3
import os
import bananopy.banano as ban
import timeit
import math
import datetime
import time

# Function to retrieve transaction history for a given address
def get_history(address, noTrans=3000):
    # Number of transactions to retrieve per page
    pagesize = 10000

    # Get account information and set head to the last block that was processed
    # If this is the first time running the function, set head to the open block
    accountInfo = ban.account_info(address)
    head = getLastRun(address)
    if head is None:
        head = accountInfo["open_block"]
    # Set frontier to the current head block for the account
    frontier = accountInfo["frontier"]
    # If head is already the frontier block, do nothing
    if head == frontier:
        pass
    # Get the total number of blocks in the account
    accountHeight = accountInfo["block_count"]

    #noTrans = get_remaining(accountHeight, head)
    # Calculate the number of pages needed to retrieve all the transactions
    pages = math.ceil(noTrans / pagesize)
    # Counter for while loop
    count = 0
    # List to store all transactions
    full_history = []

    # Loop through transactions by page
    while count < pages:
        # Calculate the number of transactions needed to reach the desired total
        transactions_needed = noTrans - len(full_history)
        # Calculate the number of transactions to retrieve on this iteration
        transactions_per_page = math.ceil(transactions_needed / (pages - count))
        # Print message to show progress
        print("Downloading history for {}: Page {}/{}".format(address, count + 1, pages))
        # Get transactions for this page
        history = ban.account_history(address, transactions_per_page, head=head, reverse=True)
        # Increment counter
        count += 1
        # Add transactions to full_history
        full_history += history["history"]
        try:
            # Update head to the next batch of transactions
            head = history["next"]
            # Save the next head block in a database
            writeLastRun(address, head)
        except Exception as e:
            # If there are no more transactions, set head to the account's frontier block
            # and break out of the loop
            print(e)
            print("Reached end of transaction history")
            head = frontier
            writeLastRun(address, head)
            break

    # Return all transactions
    return full_history


def get_remaining(accountHeight, head):
    # Get information for the current head block
    info = ban.block_info(head,True)
    # Get the height of the current head block
    headHeight = info["height"]
    # Return the difference between the total number of blocks in the account and the current head block
    return accountHeight - headHeight


# Function to convert rows from the database to dictionaries
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


# Function to read service addresses from the database
def readServices():
    # Connect to the database
    with sqlite3.connect(os.getcwd() + "/addresses.sqlite") as conn:
        # List of types to include in the query
        types = ["Exchange", "Gambling"]
        # List of aliases to include in the query
        aliases = ["Tip[.]cc"]
        # List of addresses to exclude from the query because they don't use intermediaries
        excludeadd = ["ban_1wu6rxojhgjwy1mzci1jmkm7az7nntf31h6ptuoqmetwp64j3sxo7het6e3m",
                   "ban_1eub1ezmefs1im56oomprzddwhp5s9c6brhx755ftjfjz45uytputarmcwto",
                      "ban_15sxnajaaztcbeewrs7yyih4teiz4jsxur1j393yi8xhytuza5jty6emdogo",
                      "ban_3sprts3a8hzysquk4mcy4ct4f6izp1mxtbnybiyrriprtjrn9da9cbd859qf",
                      "ban_1pd6agpcfiweyhcyyej7cwpb9gymhsnftr6nyihrqtib51zqps8har57wyur",
                      "ban_1swapdwa9wwaxh38htsrupc6zfrcojtqz4kd6jssrat6cec1ggfjnnm6hypz",
                      "ban_1t8hyu6taczfq3gmdqkwcxc6z4pt3sfwg5m7op488hxjmne55r16tebaoztb",
                      "ban_3r7xjnq4ywn1sf387xzpgbytwuaa6hgfurd11mx7qagkx1hiuq73ka63hbxz", #banlotto
                      "ban_1kwin96znfqopi7be3shxcxn8qeruirob885oaya4ix5pkrnpsou4u5qbeaa", #banslots
                      "ban_3k76rawffjm79qedoc54nhk3edkq5makoyp73b1t6q6j9yjeq633q1xck9g8"
                      ]
        # Combine the three lists into one for use in the query
        params = []
        [params.extend(l) for l in (types,aliases,excludeadd)]

        # Set the row factory to use the dict_factory function
        conn.row_factory = dict_factory
        # Create a cursor
        cur = conn.cursor()

        # Construct the SELECT query with placeholders for the lists of types, aliases, and excluded addresses
        query = 'SELECT address FROM addresses'
        query += ' WHERE (type IN ({}) OR alias IN ({}))'.format(', '.join('?' * len(types)),
                                                                 ', '.join('?' * len(aliases)))
        query += ' AND address NOT IN ({})'.format(', '.join('?' * len(excludeadd)))



        all_addresses = cur.execute(query, params).fetchall()
        #all_addresses = cur.execute('SELECT * FROM addresses WHERE type=\'Exchange\' OR type=\'Gambling\' OR alias=\'Tip[.]cc\';').fetchall()

    return json.dumps(all_addresses)

def writeIntermediaries(newintermediaries):
    with sqlite3.connect(os.getcwd() + "/addresses.sqlite") as conn:
        cur = conn.cursor()
        # Create the intermediaries table if it doesn't already exist
        cur.execute("CREATE TABLE IF NOT EXISTS intermediaries (address TEXT PRIMARY KEY, service TEXT)")

        for service, addresses in newintermediaries.items():
            for address in addresses:
                try:
                    cur.execute("INSERT INTO intermediaries (address, service) VALUES (?, ?)", (address, service))
                except sqlite3.IntegrityError:
                    # ignore errors when inserting non-unique values
                    pass
        # Save the changes to the table
        conn.commit()


def getLastRun(address):
    with sqlite3.connect(os.getcwd() + "/addresses.sqlite") as conn:
        # Set the row factory to return a dictionary for each row
        conn.row_factory = dict_factory
        cur = conn.cursor()
        # Create the 'last_run' table if it doesn't exist
        cur.execute("CREATE TABLE IF NOT EXISTS last_run (address TEXT PRIMARY KEY, date_time TEXT, head TEXT)")
        # Save the changes to the database
        conn.commit()
        # Select the 'head' column for the row with the specified 'address' in the 'last_run' table
        query = 'SELECT head FROM last_run WHERE address=?'
        try:
            # Execute the query and fetch the first row
            head = cur.execute(query, (address,)).fetchone()

            if head is not None:
                # Return the 'head' value if a row was found
                return head['head']
            # Return None if no row was found
            return None
        except Exception as e:
            # Print the error message and return None if an exception occurs
            print("AAAA")
            print(e)
            return None

def writeLastRun(address, head):
    # Connect to the database
    with sqlite3.connect(os.getcwd() + "/addresses.sqlite") as conn:
        # Create a cursor
        cur = conn.cursor()
        # Create the 'last_run' table if it doesn't exist
        cur.execute("CREATE TABLE IF NOT EXISTS last_run (address TEXT PRIMARY KEY, date_time TEXT, head TEXT)")
        # Get the current date and time
        date_time = str(datetime.datetime.now())
        try:
            # Insert the new address, head, and date/time into the 'last_run' table
            cur.execute("INSERT INTO last_run (date_time, head, address) VALUES (?, ?, ?)", (date_time, head, address))

        except Exception as e:
            # If an error occurs, print a message and update the existing entry for this address with the new head and date/time
            print("Service already included. Updating run time")
            print(e)
            cur.execute("UPDATE last_run SET date_time=?, head=? WHERE address=?", (date_time, head, address))
        # Save the changes to the database
        conn.commit()


def main():
    # Get list of main addresses from the database
    mainAddresses = readServices()
    # Convert the list from a JSON string to a Python object
    mainAddresses = json.loads(mainAddresses)
    # Create an empty dictionary to store intermediary addresses for each main address
    newintermediaries = {}
    # Create an empty dictionary to store intermediary addresses for each main address
    for record in mainAddresses:
        print(record["address"])
        mainaddress = record["address"]
        # Initialize an empty list to store intermediaries for the current main address
        intermediaries = []
        # Get the transaction history for the main address
        history = get_history(record["address"], noTrans=70000)
        # Iterate through the transaction history
        for transaction in history:
            # If the transaction is a receive transaction and the account receiving the transaction is not already in the list of intermediaries, add it to the list
            if transaction["type"] == "receive" and transaction["account"] not in intermediaries:
                # Add the list of intermediaries for the current main address to the dictionary
                intermediaries.append(transaction["account"])
        newintermediaries[record["address"]] = intermediaries
        # Write the intermediaries to the database
        writeIntermediaries(newintermediaries)




main()