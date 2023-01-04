# Base code initially from https://programminghistorian.org/en/lessons/creating-apis-with-python-and-flask

import os
import flask
from flask import request, jsonify
from flask_cors import CORS
import sqlite3

app = flask.Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
#app.config["DEBUG"] = True

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
<a href="/api/v1/resources/intermediaries/all">/api/v1/resources/intermediaries/all</a>
<br>
<a href="/api/v1/resources/intermediaries?address=ban_113sf8z98qqihjis3m95gkb35z7ckfakbrtrmbtawf37hc6ixx7rtz53bq8o">/api/v1/resources/intermediaries?address=ban_113sf8z98qqihjis3m95gkb35z7ckfakbrtrmbtawf37hc6ixx7rtz53bq8o</a>
<br>
<a href="/api/v1/resources/intermediaries?address=ban_113sf8z98qqihjis3m95gkb35z7ckfakbrtrmbtawf37hc6ixx7rtz53bq8o&address=ban_111c3xcromzadabqud7yer7ptzrocecsum9d9t8feoz81zdbu7gh63hnk7n4">/api/v1/resources/intermediaries?address=ban_113sf8z98qqihjis3m95gkb35z7ckfakbrtrmbtawf37hc6ixx7rtz53bq8o&address=ban_111c3xcromzadabqud7yer7ptzrocecsum9d9t8feoz81zdbu7gh63hnk7n4</a>
<br>
<a href="/api/v1/resources/intermediaries?service=ban_1gooj14qko1u6md87aga9c53nf4iphyt1ua7x3kq1wnkdh49u5mndqygbr1q">/api/v1/resources/intermediaries?service=ban_1gooj14qko1u6md87aga9c53nf4iphyt1ua7x3kq1wnkdh49u5mndqygbr1q</a>
<br>
<a href="/api/v1/resources/intermediaries?service=ban_1gooj14qko1u6md87aga9c53nf4iphyt1ua7x3kq1wnkdh49u5mndqygbr1q&service=ban_1oaocnrcaystcdtaae6woh381wftyg4k7bespu19m5w18ze699refhyzu6bo">/api/v1/resources/intermediaries?service=ban_1gooj14qko1u6md87aga9c53nf4iphyt1ua7x3kq1wnkdh49u5mndqygbr1q&service=ban_1oaocnrcaystcdtaae6woh381wftyg4k7bespu19m5w18ze699refhyzu6bo</a>
<br>
<a href="/api/v1/resources/intermediaries?service=ban_1oaocnrcaystcdtaae6woh381wftyg4k7bespu19m5w18ze699refhyzu6bo&address=ban_3fhhttfufikxikuxj5j6gndu5dokupa7j7t7dq5qkat19fm3mo84spe8krhz">/api/v1/resources/intermediaries?service=ban_1oaocnrcaystcdtaae6woh381wftyg4k7bespu19m5w18ze699refhyzu6bo&address=ban_3fhhttfufikxikuxj5j6gndu5dokupa7j7t7dq5qkat19fm3mo84spe8krhz</a>
<br>
<a href="/api/v1/resources/intermediaries/status">/api/v1/resources/intermediaries/status</a>
<br>
<br>
<a href="https://github.com/Kirby1997/BananoAddressAPI">Source on Github</a>
'''


@app.route('/api/v1/resources/addresses/all', methods=['GET'])
def known_all():
    conn = sqlite3.connect(os.getcwd() + "/addresses.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_addresses = cur.execute('SELECT * FROM addresses;').fetchall()

    return jsonify(all_addresses)



@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


@app.route('/api/v1/resources/addresses', methods=['GET'])
def known_filter():
    query_parameters = request.args

    addresses = query_parameters.getlist('address')
    adtypes = query_parameters.getlist('type')
    owners = query_parameters.getlist('owner')
    illicit = query_parameters.get('illicit')
    query = "SELECT * FROM addresses WHERE"
    to_filter = []

    if addresses:
        query += ' address IN ({}) AND'.format(', '.join('?' * len(addresses)))
        to_filter.extend(addresses)
    if adtypes:
        query += ' type IN ({}) AND'.format(', '.join('?' * len(adtypes)))
        to_filter.extend(adtypes)
    if owners:
        query += ' owner IN ({}) AND'.format(', '.join('?' * len(owners)))
        to_filter.extend(owners)
    if illicit:
        query += ' illicit=? AND'
        to_filter.extend(illicit)

    if not (addresses or adtypes or owners or illicit):
        return page_not_found(404)

    query = query[:-4] + ';'

    conn = sqlite3.connect(os.getcwd() + "/addresses.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()

    results = cur.execute(query, to_filter).fetchall()

    return jsonify(results)

@app.route('/api/v1/resources/intermediaries/all', methods=['GET'])
def intermediaries_all():
    conn = sqlite3.connect(os.getcwd() + "/addresses.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_addresses = cur.execute('SELECT * FROM intermediaries;').fetchall()

    return jsonify(all_addresses)

@app.route('/api/v1/resources/intermediaries', methods=['GET'])
def intermediaries_filter():
    query_parameters = request.args

    addresses = query_parameters.getlist('address')
    services = query_parameters.getlist('service')
    query = "SELECT * FROM intermediaries WHERE"
    to_filter = []

    if addresses:
        query += ' address IN ({}) AND'.format(', '.join('?' * len(addresses)))
        to_filter.extend(addresses)
    if services:
        query += ' service IN ({}) AND'.format(', '.join('?' * len(services)))
        to_filter.extend(services)


    if not (addresses or services):
        return page_not_found(404)

    query = query[:-4] + ';'

    conn = sqlite3.connect(os.getcwd() + "/addresses.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()

    results = cur.execute(query, to_filter).fetchall()

    return jsonify(results)

@app.route('/api/v1/resources/intermediaries/status', methods=['GET'])
def intermediaries_status():
    conn = sqlite3.connect(os.getcwd() + "/addresses.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_addresses = cur.execute('SELECT * FROM last_run;').fetchall()

    return jsonify(all_addresses)


if __name__ == '__main__':
    app.run()