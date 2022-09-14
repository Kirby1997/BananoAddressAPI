from flask import jsonify
import json
import sqlite3
import os
import bananopy.banano as ban


def get_history(address, noTrans = 20):
    pagesize = 5000

    if noTrans <= pagesize:
        history = ban.account_history(address, noTrans)
        return history["history"]

    else:

        remainder = (noTrans % pagesize)
        pages = (noTrans - remainder) / pagesize
        count = 0
        offset = 0
        full_history = []
        accountInfo = ban.account_info(address)
        head = accountInfo["open_block"]
        frontier = accountInfo["frontier"]
        blockHeight = accountInfo["block_count"]

        while count < pages:
            print("Downloading history: Page " + str(count+1) + "/" + str(pages))
            history = ban.account_history(address, pagesize, head=head, reverse=True)

            count = count + 1
            full_history = full_history + history["history"]
            print(len(history["history"]))

            head = history["next"]

        if remainder != 0:
            history = ban.account_history(address, remainder, head=head, reverse=True)
            head = history["history"][len(history["history"]) - 1]["hash"]
            full_history = full_history + history["history"]

        print(len(full_history))
        return full_history


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def readDatabase():
    conn = sqlite3.connect(os.getcwd() + "/addresses.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_addresses = cur.execute('SELECT * FROM addresses WHERE type=\'Exchange\' OR type=\'Gambling\' OR alias=\'Tip[.]cc\';').fetchall()

    return json.dumps(all_addresses)


def main():
    mainAddresses = readDatabase()
    mainAddresses = json.loads(mainAddresses)
    #for address in mainAddresses:
    print(mainAddresses[0]["address"])
    #history = get_history(mainAddresses[0]["address"], noTrans=20)
    history = get_history("ban_31dhbgirwzd3ce7naor6o94woefws9hpxu4q8uxm1bz98w89zqpfks5rk3ad", noTrans=10000)

    print(history)
    print(len(history))


main()