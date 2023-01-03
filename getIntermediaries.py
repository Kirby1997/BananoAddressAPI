from flask import jsonify
import json
import sqlite3
import os
import bananopy.banano as ban
import timeit
import math
import datetime


def get_history(address, noTrans=20, pagesize=3000):

    if pagesize > 3000:
        pagesize = 3000

    accountInfo = ban.account_info(address)
    head = getLastRun(address)
    if head is None:
        head = accountInfo["open_block"]
    frontier = accountInfo["frontier"]
    if head == frontier:
        pass
    blockHeight = accountInfo["block_count"]

    pages = math.ceil(noTrans / pagesize)
    count = 0
    full_history = []

    while count < pages:
        transactions_needed = noTrans - len(full_history)
        transactions_per_page = math.ceil(transactions_needed / (pages - count))
        print("Downloading history for {}: Page {}/{}".format(address, count + 1, pages))
        history = ban.account_history(address, transactions_per_page, head=head, reverse=True)
        count += 1
        full_history += history["history"]
        try:
            head = history["next"]
        except Exception as e:
            print(e)
            head = frontier

        writeLastRun(address, head)

    return full_history


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d



def readServices():
    with sqlite3.connect(os.getcwd() + "/addresses.sqlite") as conn:
        types = ["Exchange", "Gambling"]
        aliases = ["Tip[.]cc"]
        excludeadd = ["ban_1wu6rxojhgjwy1mzci1jmkm7az7nntf31h6ptuoqmetwp64j3sxo7het6e3m",
                   "ban_1eub1ezmefs1im56oomprzddwhp5s9c6brhx755ftjfjz45uytputarmcwto",
                      "ban_15sxnajaaztcbeewrs7yyih4teiz4jsxur1j393yi8xhytuza5jty6emdogo",
                      "ban_3sprts3a8hzysquk4mcy4ct4f6izp1mxtbnybiyrriprtjrn9da9cbd859qf",
                      "ban_1pd6agpcfiweyhcyyej7cwpb9gymhsnftr6nyihrqtib51zqps8har57wyur",
                      "ban_1swapdwa9wwaxh38htsrupc6zfrcojtqz4kd6jssrat6cec1ggfjnnm6hypz",
                      "ban_1t8hyu6taczfq3gmdqkwcxc6z4pt3sfwg5m7op488hxjmne55r16tebaoztb",
                      "ban_3r7xjnq4ywn1sf387xzpgbytwuaa6hgfurd11mx7qagkx1hiuq73ka63hbxz", #banlotto
                      "ban_1kwin96znfqopi7be3shxcxn8qeruirob885oaya4ix5pkrnpsou4u5qbeaa" #banslots
                      ]

        params = []
        [params.extend(l) for l in (types,aliases,excludeadd)]


        conn.row_factory = dict_factory
        cur = conn.cursor()

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
        cur.execute("CREATE TABLE IF NOT EXISTS intermediaries (address TEXT, service TEXT)")

        for service, addresses in newintermediaries.items():
            for address in addresses:
                try:
                    cur.execute("INSERT INTO intermediaries (address, service) VALUES (?, ?)", (address, service))
                except sqlite3.IntegrityError:
                    # ignore errors when inserting non-unique values
                    pass

        conn.commit()


def getLastRun(address):
    with sqlite3.connect(os.getcwd() + "/addresses.sqlite") as conn:
        conn.row_factory = dict_factory
        cur = conn.cursor()
        query = 'SELECT head FROM last_run WHERE address=?'
        head = cur.execute(query, (address,)).fetchone()
        if head is not None:
            return head['head']
        return None

def writeLastRun(address, head):
    with sqlite3.connect(os.getcwd() + "/addresses.sqlite") as conn:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS last_run (address TEXT PRIMARY KEY, date_time TEXT, head TEXT)")

        date_time = str(datetime.datetime.now())
        cur.execute("UPDATE last_run SET date_time=?, head=? WHERE address=?", (date_time, head, address))

        conn.commit()


def main():
    mainAddresses = readServices()
    mainAddresses = json.loads(mainAddresses)
    newintermediaries = {}
    for record in mainAddresses:
        print(record["address"])
        mainaddress = record["address"]
        intermediaries = []
        history = get_history(record["address"], noTrans=20)
        for transaction in history:
            if transaction["account"] not in intermediaries:
                intermediaries.append(transaction["account"])
        newintermediaries[record["address"]] = intermediaries
    writeIntermediaries(newintermediaries)



main()