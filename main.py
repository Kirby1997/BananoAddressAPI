# Base code initially from https://programminghistorian.org/en/lessons/creating-apis-with-python-and-flask

import os
import flask
from flask import request, jsonify, render_template
from flask_cors import CORS
import sqlite3

app = flask.Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
# app.config["DEBUG"] = True


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")

@app.route("/api/v1/resources/addresses/all", methods=["GET"])
def known_all():
    conn = sqlite3.connect(os.getcwd() + "/addresses.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_addresses = cur.execute("SELECT * FROM addresses;").fetchall()

    return jsonify(all_addresses)


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


@app.route("/query-address", methods=["GET"])
def update_address_form():
    return render_template("update_form.html")

@app.route("/manage-records", methods=["GET"])
def manage_addresses():
    return render_template("manage_records.html")

@app.route("/api/v1/resources/addresses/update", methods=["PUT"])
def update_address():
    update_password = os.environ.get("UPDATE_PASSWORD", "default_password")
    request_data = request.get_json()

    # Check password
    if request_data.get("password") != update_password:
        return jsonify({"error": "Unauthorized: Incorrect password"}), 401

    address_id = request_data.get("id")
    new_data = request_data.get("new_data")

    if not all([address_id, new_data]):
        return jsonify({"error": "Missing data"}), 400

    conn = sqlite3.connect(os.getcwd() + "/addresses.sqlite")
    cursor = conn.cursor()

    try:
        # Special handling for updating address itself
        if "address" in new_data:
            new_address = new_data.pop("address")
            cursor.execute(
                "UPDATE addresses SET address = ? WHERE address = ?",
                (new_address, address_id),
            )

        # Update other fields
        updates = ", ".join([f"{key} = ?" for key in new_data.keys()])
        parameters = list(new_data.values()) + [
            address_id if "address" not in new_data else new_address
        ]

        if updates:
            cursor.execute(
                f"UPDATE addresses SET {updates} WHERE address = ?", parameters
            )

        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"success": True}), 200


@app.route("/api/v1/resources/addresses/create", methods=["POST"])
def create_address():
    update_password = os.environ.get("UPDATE_PASSWORD", "default_password")
    request_data = request.get_json()

    # Check password
    if request_data.get("password") != update_password:
        return jsonify({"error": "Unauthorized: Incorrect password"}), 401

    new_address = request_data.get("address")
    alias = request_data.get("alias")
    owner = request_data.get("owner")
    address_type = request_data.get("type")

    if not all([new_address, alias, owner, address_type]):
        return jsonify({"error": "Missing data"}), 400

    conn = sqlite3.connect(os.getcwd() + "/addresses.sqlite")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO addresses (address, alias, owner, type) VALUES (?, ?, ?, ?)",
            (new_address, alias, owner, address_type),
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"success": True}), 200


@app.route("/api/v1/resources/addresses/delete", methods=["DELETE"])
def delete_address():
    update_password = os.environ.get("UPDATE_PASSWORD", "default_password")
    request_data = request.get_json()

    # Check password
    if request_data.get("password") != update_password:
        return jsonify({"error": "Unauthorized: Incorrect password"}), 401

    address_id = request_data.get("id")

    if not address_id:
        return jsonify({"error": "Missing data"}), 400

    conn = sqlite3.connect(os.getcwd() + "/addresses.sqlite")
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM addresses WHERE address = ?", (address_id,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"success": True}), 200

@app.route("/api/v1/resources/addresses", methods=["GET"])
def known_filter():
    query_parameters = request.args

    addresses = query_parameters.getlist("address")
    adtypes = query_parameters.getlist("type")
    owners = query_parameters.getlist("owner")
    illicit = query_parameters.get("illicit")
    query = "SELECT * FROM addresses WHERE"
    to_filter = []

    if addresses:
        query += " address IN ({}) AND".format(", ".join("?" * len(addresses)))
        to_filter.extend(addresses)
    if adtypes:
        query += " type IN ({}) AND".format(", ".join("?" * len(adtypes)))
        to_filter.extend(adtypes)
    if owners:
        query += " owner IN ({}) AND".format(", ".join("?" * len(owners)))
        to_filter.extend(owners)
    if illicit:
        query += " illicit=? AND"
        to_filter.extend(illicit)

    if not (addresses or adtypes or owners or illicit):
        return page_not_found(404)

    query = query[:-4] + ";"

    conn = sqlite3.connect(os.getcwd() + "/addresses.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()

    results = cur.execute(query, to_filter).fetchall()

    return jsonify(results)


@app.route("/api/v1/resources/intermediaries/all", methods=["GET"])
def intermediaries_all():
    conn = sqlite3.connect(os.getcwd() + "/addresses.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_addresses = cur.execute("SELECT * FROM intermediaries;").fetchall()

    return jsonify(all_addresses)


@app.route("/api/v1/resources/intermediaries", methods=["GET"])
def intermediaries_filter():
    query_parameters = request.args

    addresses = query_parameters.getlist("address")
    services = query_parameters.getlist("service")
    query = "SELECT * FROM intermediaries WHERE"
    to_filter = []

    if addresses:
        query += " address IN ({}) AND".format(", ".join("?" * len(addresses)))
        to_filter.extend(addresses)
    if services:
        query += " service IN ({}) AND".format(", ".join("?" * len(services)))
        to_filter.extend(services)

    if not (addresses or services):
        return page_not_found(404)

    query = query[:-4] + ";"

    conn = sqlite3.connect(os.getcwd() + "/addresses.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()

    results = cur.execute(query, to_filter).fetchall()

    return jsonify(results)


@app.route("/api/v1/resources/intermediaries/status", methods=["GET"])
def intermediaries_status():
    conn = sqlite3.connect(os.getcwd() + "/addresses.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_addresses = cur.execute("SELECT * FROM last_run;").fetchall()

    return jsonify(all_addresses)


if __name__ == "__main__":
    app.run()
