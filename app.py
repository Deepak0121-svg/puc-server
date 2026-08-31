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

    </head>

    <body>

        <h1>PUC Pollution Data Server</h1>

        <p>Server is running successfully.</p>

        <h3>API Endpoint</h3>

        <p>/api/v1/puc/results</p>

        <h3>View Results</h3>

        <p>/view</p>

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

    print("\n")
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
    print("\n")


    # ----------------------------------------------
    # RESPONSE
    # ----------------------------------------------

    return jsonify({

        "status": "success",

        "message": "Pollution data received successfully",

        "machine_id": machine_id,

        "vehicle_no": vehicle_no

    })


# ==================================================
# VIEW DATA
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


    # ----------------------------------------------
    # HTML
    # ----------------------------------------------

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

                <th>Vehicle No</th>

                <th>CO</th>

                <th>HC</th>

                <th>CO2</th>

                <th>O2</th>

                <th>Result</th>

            </tr>

    """


    # ----------------------------------------------
    # TABLE ROWS
    # ----------------------------------------------

    for row in rows:

        html += f"""

            <tr>

                <td>{row['id']}</td>

                <td>{row['received_at']}</td>

                <td>{row['machine_id']}</td>

                <td>{row['vehicle_no']}</td>

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
# START SERVER
# ==================================================

# Initialize database when application starts
init_db()


if __name__ == "__main__":

    print("\n")
    print("==============================================")
    print("       PUC POLLUTION SERVER STARTED")
    print("==============================================")

    print("Local URL:")
    print("http://127.0.0.1:5000")

    print("\nAPI URL:")
    print("http://127.0.0.1:5000/api/v1/puc/results")

    print("\nVIEW URL:")
    print("http://127.0.0.1:5000/view")

    print("==============================================")
    print("\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )