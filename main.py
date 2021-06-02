# Base code initially from https://programminghistorian.org/en/lessons/creating-apis-with-python-and-flask

import flask
from flask import request, jsonify
import sqlite3

app = flask.Flask(__name__)
app.config["DEBUG"] = True

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


@app.route('/', methods=['GET'])
def home():
    return '''<h1>Banano address API</h1>
<p>Banano address API by Kirby. Work in progress</p>'''


@app.route('/api/v1/resources/addresses/all', methods=['GET'])
def api_all():
    conn = sqlite3.connect('addresses.sqlite')
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

    conn = sqlite3.connect('addresses.sqlite')
    conn.row_factory = dict_factory
    cur = conn.cursor()

    results = cur.execute(query, to_filter).fetchall()

    return jsonify(results)

app.run()