# Base code initially from https://programminghistorian.org/en/lessons/creating-apis-with-python-and-flask

import os
import flask
from flask import request, jsonify
from flask_cors import CORS
import sqlite3

app = flask.Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config["DEBUG"] = True

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


@app.route('/', methods=['GET'])
def home():
    return '''<h1>Banano address API</h1>
<p>Banano address API by Kirby. Work in progress</p>
<a href="/api/v1/resources/addresses?address=ban_31dhbgirwzd3ce7naor6o94woefws9hpxu4q8uxm1bz98w89zqpfks5rk3ad">/api/v1/resources/addresses?address=ban_31dhbgirwzd3ce7naor6o94woefws9hpxu4q8uxm1bz98w89zqpfks5rk3ad</a>
<br>
<a href="/api/v1/resources/addresses?type=Distribution">/api/v1/resources/addresses?type=Distribution</a>
<br>
<a href="/api/v1/resources/addresses?type=Exchange">/api/v1/resources/addresses?type=Exchange</a>
<br>
<a href="/api/v1/resources/addresses?type=Gambling">/api/v1/resources/addresses?type=Gambling</a>
<br>
<a href="/api/v1/resources/addresses/all">/api/v1/resources/addresses/all</a>
<br>
<a href="/api/v1/resources/addresses?illicit=1">/api/v1/resources/addresses?illicit=1</a>
<br>
<br>
<a href="https://github.com/Kirby1997/BananoAddressAPI">Source on Github</a>
'''


@app.route('/api/v1/resources/addresses/all', methods=['GET'])
def api_all():
    conn = sqlite3.connect(os.getcwd() + "/addresses.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_addresses = cur.execute('SELECT * FROM addresses;').fetchall()

    return jsonify(all_addresses)



@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


@app.route('/api/v1/resources/addresses', methods=['GET'])
def api_filter():
    query_parameters = request.args

    address = query_parameters.get('address')
    adtype = query_parameters.get('type')
    owner = query_parameters.get('owner')
    illicit = query_parameters.get('illicit')
    query = "SELECT * FROM addresses WHERE"
    to_filter = []

    if address:
        query += ' address=? AND'
        to_filter.append(address)
    if adtype:
        query += ' type=? AND'
        to_filter.append(adtype)
    if owner:
        query += ' owner=? AND'
        to_filter.append(owner)
    if illicit:
        query += ' illicit=? AND'
        to_filter.append(illicit)

    if not (address or adtype or owner or illicit):
        return page_not_found(404)

    query = query[:-4] + ';'

    conn = sqlite3.connect(os.getcwd() + "/addresses.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()

    results = cur.execute(query, to_filter).fetchall()

    return jsonify(results)


if __name__ == '__main__':
    app.run()