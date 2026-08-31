from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = "data.db"


# ==================================================
# DATABASE
# ==================================================

def init_db():

    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS pollution_results (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            received_at TEXT,

            machine_id TEXT,

            vehicle_no TEXT,

            co REAL,

            hc REAL,

            co2 REAL,

            o2 REAL,

            result TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw_machine_data (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            received_at TEXT,

            machine_id TEXT,

            raw_hex TEXT
        )
    """)

    conn.commit()
    conn.close()


# ==================================================
# HOME PAGE
# ==================================================

@app.route("/", methods=["GET"])
def home():

    return """
    <!DOCTYPE html>

    <html>

    <head>

        <title>PUC Pollution Server</title>

        <style>

            body {
                font-family: Arial;
                margin: 40px;
            }

            a {
                font-size: 18px;
            }

        </style>

    </head>

    <body>

        <h1>PUC Pollution Data Server</h1>

        <p>Server is running successfully.</p>

        <h3>API Endpoints</h3>

        <p>
            Pollution Data:
            /api/v1/puc/results
        </p>

        <p>
            Raw Machine Data:
            /api/v1/puc/raw
        </p>

        <h3>View Data</h3>

        <p>
            <a href="/view">
                View Pollution Results
            </a>
        </p>

        <p>
            <a href="/raw">
                View Raw Machine Data
            </a>
        </p>

    </body>

    </html>
    """


# ==================================================
# RECEIVE POLLUTION DATA
# ==================================================

@app.route(
    "/api/v1/puc/results",
    methods=["GET", "POST"]
)
def receive_data():

    # ----------------------------------------------
    # GET REQUEST
    # ----------------------------------------------

    if request.method == "GET":

        machine_id = request.args.get("machine_id")

        vehicle_no = request.args.get("vehicle_no")

        co = request.args.get("co")

        hc = request.args.get("hc")

        co2 = request.args.get("co2")

        o2 = request.args.get("o2")

        result = request.args.get("result")


    # ----------------------------------------------
    # POST REQUEST
    # ----------------------------------------------

    else:

        data = request.get_json(silent=True)

        if not data:

            return jsonify({
                "status": "error",
                "message": "JSON data not received"
            }), 400

        machine_id = data.get("machine_id")

        vehicle_no = data.get("vehicle_no")

        co = data.get("co")

        hc = data.get("hc")

        co2 = data.get("co2")

        o2 = data.get("o2")

        result = data.get("result")


    # ----------------------------------------------
    # VALIDATION
    # ----------------------------------------------

    if not machine_id:

        return jsonify({
            "status": "error",
            "message": "machine_id is required"
        }), 400


    # ----------------------------------------------
    # TIME
    # ----------------------------------------------

    received_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    # ----------------------------------------------
    # DATABASE
    # ----------------------------------------------

    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        INSERT INTO pollution_results
        (
            received_at,
            machine_id,
            vehicle_no,
            co,
            hc,
            co2,
            o2,
            result
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        received_at,

        machine_id,

        vehicle_no,

        co,

        hc,

        co2,

        o2,

        result

    ))

    conn.commit()

    conn.close()


    # ----------------------------------------------
    # TERMINAL OUTPUT
    # ----------------------------------------------

    print()
    print("==============================================")
    print("         PUC DATA RECEIVED")
    print("==============================================")

    print("Received Time :", received_at)

    print("Machine ID    :", machine_id)

    print("Vehicle No    :", vehicle_no)

    print("CO            :", co)

    print("HC            :", hc)

    print("CO2           :", co2)

    print("O2            :", o2)

    print("Result        :", result)

    print("==============================================")
    print()


    # ----------------------------------------------
    # RESPONSE
    # ----------------------------------------------

    return jsonify({

        "status": "success",

        "message":
        "Pollution data received successfully",

        "machine_id": machine_id,

        "vehicle_no": vehicle_no

    }), 200


# ==================================================
# RECEIVE RAW PUC MACHINE HEX DATA
# ==================================================

@app.route(
    "/api/v1/puc/raw",
    methods=["POST"]
)
def receive_raw_data():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "status": "error",
            "message": "JSON data not received"
        }), 400


    machine_id = data.get("machine_id")

    raw_hex = data.get("raw_hex")


    # ----------------------------------------------
    # VALIDATION
    # ----------------------------------------------

    if not machine_id:

        return jsonify({
            "status": "error",
            "message": "machine_id is required"
        }), 400


    if not raw_hex:

        return jsonify({
            "status": "error",
            "message": "raw_hex is required"
        }), 400


    # ----------------------------------------------
    # TIME
    # ----------------------------------------------

    received_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    # ----------------------------------------------
    # SAVE RAW DATA
    # ----------------------------------------------

    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        INSERT INTO raw_machine_data
        (
            received_at,
            machine_id,
            raw_hex
        )

        VALUES (?, ?, ?)

    """, (

        received_at,

        machine_id,

        raw_hex

    ))

    conn.commit()

    conn.close()


    # ----------------------------------------------
    # TERMINAL OUTPUT
    # ----------------------------------------------

    print()
    print("==============================================")
    print("       RAW PUC MACHINE DATA RECEIVED")
    print("==============================================")

    print("Received Time :", received_at)

    print("Machine ID    :", machine_id)

    print()
    print("RAW HEX DATA:")
    print(raw_hex)

    print()
    print("==============================================")
    print()


    # ----------------------------------------------
    # RESPONSE
    # ----------------------------------------------

    return jsonify({

        "status": "success",

        "message":
        "Raw PUC data received successfully",

        "machine_id": machine_id,

        "received_at": received_at

    }), 200


# ==================================================
# VIEW POLLUTION DATA
# ==================================================

@app.route("/view", methods=["GET"])
def view_data():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT *

        FROM pollution_results

        ORDER BY id DESC

    """).fetchall()

    conn.close()


    html = """

    <!DOCTYPE html>

    <html>

    <head>

        <title>PUC Pollution Results</title>

        <meta
            http-equiv="refresh"
            content="5"
        >

        <style>

            body {

                font-family: Arial;

                margin: 30px;

                background: #f5f5f5;

            }

            h1 {

                text-align: center;

            }

            table {

                border-collapse: collapse;

                width: 100%;

                background: white;

            }

            th, td {

                border: 1px solid #999;

                padding: 10px;

                text-align: center;

            }

            th {

                background: #eeeeee;

            }

        </style>

    </head>


    <body>

        <h1>
            PUC Pollution Test Results
        </h1>


        <table>

            <tr>

                <th>ID</th>

                <th>Received Time</th>

                <th>Machine ID</th>

                

                <th>CO</th>

                <th>HC</th>

                <th>CO2</th>

                <th>O2</th>

                <th>Result</th>

            </tr>

    """


    for row in rows:

        html += f"""

            <tr>

                <td>{row['id']}</td>

                <td>{row['received_at']}</td>

                <td>{row['machine_id']}</td>

               

                <td>{row['co']}</td>

                <td>{row['hc']}</td>

                <td>{row['co2']}</td>

                <td>{row['o2']}</td>

                <td>{row['result']}</td>

            </tr>

        """


    html += """

        </table>

    </body>

    </html>

    """


    return html


# ==================================================
# VIEW RAW MACHINE DATA
# ==================================================

@app.route("/raw", methods=["GET"])
def view_raw_data():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT *

        FROM raw_machine_data

        ORDER BY id DESC

    """).fetchall()

    conn.close()


    html = """

    <!DOCTYPE html>

    <html>

    <head>

        <title>Raw PUC Machine Data</title>

        <meta
            http-equiv="refresh"
            content="5"
        >

        <style>

            body {

                font-family: Arial;

                margin: 30px;

                background: #f5f5f5;

            }

            table {

                border-collapse: collapse;

                width: 100%;

                background: white;

            }

            th, td {

                border: 1px solid #999;

                padding: 10px;

            }

            th {

                background: #eeeeee;

            }

            .hex {

                font-family: monospace;

                word-break: break-all;

            }

        </style>

    </head>


    <body>

        <h1>
            Raw PUC Machine Data
        </h1>


        <table>

            <tr>

                <th>ID</th>

                <th>Received Time</th>

                <th>Machine ID</th>

                <th>Raw HEX</th>

            </tr>

    """


    for row in rows:

        html += f"""

            <tr>

                <td>{row['id']}</td>

                <td>{row['received_at']}</td>

                <td>{row['machine_id']}</td>

                <td class="hex">
                    {row['raw_hex']}
                </td>

            </tr>

        """


    html += """

        </table>

    </body>

    </html>

    """


    return html


# ==================================================
# START SERVER
# ==================================================

init_db()


if __name__ == "__main__":

    print()
    print("==============================================")
    print("       PUC POLLUTION SERVER STARTED")
    print("==============================================")

    print()
    print("Local URL:")
    print("http://127.0.0.1:5000")

    print()
    print("Pollution API:")
    print(
        "http://127.0.0.1:5000/"
        "api/v1/puc/results"
    )

    print()
    print("Raw Data API:")
    print(
        "http://127.0.0.1:5000/"
        "api/v1/puc/raw"
    )

    print()
    print("View Pollution Results:")
    print(
        "http://127.0.0.1:5000/view"
    )

    print()
    print("View Raw Machine Data:")
    print(
        "http://127.0.0.1:5000/raw"
    )

    print()
    print("==============================================")
    print()


    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )