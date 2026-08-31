from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import html

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
# HEX DECODER
# ==================================================

def decode_puc_hex(raw_hex):

    """
    PUC machine HEX decoder.

    IMPORTANT:
    The actual byte mapping for CO, HC, CO2 and O2
    must be confirmed from the manufacturer's
    communication protocol.

    Until that is confirmed, this function only
    validates and displays the HEX bytes.
    """

    try:

        # Remove spaces/newlines
        clean_hex = " ".join(raw_hex.split())

        # Convert HEX -> bytes
        data = bytes.fromhex(clean_hex)

        print()
        print("========== HEX DECODER ==========")
        print("Total Bytes :", len(data))
        print()

        for i, byte in enumerate(data):

            print(
                f"BYTE[{i:02d}] = "
                f"{byte:02X}  ({byte})"
            )

        print("=================================")

        # ------------------------------------------
        # ACTUAL VALUES NOT YET MAPPED
        # ------------------------------------------

        co = None
        hc = None
        co2 = None
        o2 = None
        result = None

        return {
            "co": co,
            "hc": hc,
            "co2": co2,
            "o2": o2,
            "result": result
        }

    except ValueError as e:

        print("HEX DECODER ERROR:", e)

        return {
            "co": None,
            "hc": None,
            "co2": None,
            "o2": None,
            "result": None
        }


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
                background: #f5f5f5;
            }

            .box {
                background: white;
                padding: 25px;
                border-radius: 10px;
                margin-bottom: 20px;
            }

            a {
                font-size: 18px;
            }

        </style>

    </head>

    <body>

        <div class="box">

            <h1>PUC Pollution Data Server</h1>

            <p>
                Server is running successfully.
            </p>

        </div>


        <div class="box">

            <h2>API Endpoints</h2>

            <p>
                Pollution API:
                <b>/api/v1/puc/results</b>
            </p>

            <p>
                Raw Machine API:
                <b>/api/v1/puc/raw</b>
            </p>

        </div>


        <div class="box">

            <h2>View Data</h2>

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

        </div>

    </body>

    </html>
    """


# ==================================================
# RECEIVE NORMAL POLLUTION DATA
# ==================================================

@app.route(
    "/api/v1/puc/results",
    methods=["GET", "POST"]
)
def receive_data():

    # ==================================================
    # GET
    # ==================================================

    if request.method == "GET":

        machine_id = request.args.get("machine_id")

        vehicle_no = request.args.get("vehicle_no")

        co = request.args.get("co")

        hc = request.args.get("hc")

        co2 = request.args.get("co2")

        o2 = request.args.get("o2")

        result = request.args.get("result")


    # ==================================================
    # POST
    # ==================================================

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


    # ==================================================
    # VALIDATION
    # ==================================================

    if not machine_id:

        return jsonify({
            "status": "error",
            "message": "machine_id is required"
        }), 400


    # ==================================================
    # TIME
    # ==================================================

    received_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    # ==================================================
    # DATABASE
    # ==================================================

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


    # ==================================================
    # TERMINAL
    # ==================================================

    print()
    print("==============================================")
    print("          PUC DATA RECEIVED")
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


    return jsonify({

        "status": "success",

        "message":
        "Pollution data received successfully",

        "machine_id": machine_id,

        "vehicle_no": vehicle_no

    }), 200


# ==================================================
# RECEIVE RAW PUC MACHINE HEX
# ==================================================

@app.route(
    "/api/v1/puc/raw",
    methods=["POST"]
)
def receive_raw_data():

    # ==================================================
    # READ JSON
    # ==================================================

    data = request.get_json(silent=True)

    if not data:

        return jsonify({

            "status": "error",

            "message":
            "JSON data not received"

        }), 400


    machine_id = data.get("machine_id")

    raw_hex = data.get("raw_hex")


    # ==================================================
    # VALIDATION
    # ==================================================

    if not machine_id:

        return jsonify({

            "status": "error",

            "message":
            "machine_id is required"

        }), 400


    if not raw_hex:

        return jsonify({

            "status": "error",

            "message":
            "raw_hex is required"

        }), 400


    # ==================================================
    # CLEAN HEX
    # ==================================================

    raw_hex = " ".join(
        raw_hex.replace("\n", " ").split()
    )


    # ==================================================
    # DECODE
    # ==================================================

    decoded = decode_puc_hex(raw_hex)

    co = decoded["co"]

    hc = decoded["hc"]

    co2 = decoded["co2"]

    o2 = decoded["o2"]

    result = decoded["result"]


    # ==================================================
    # TIME
    # ==================================================

    received_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    # ==================================================
    # SAVE RAW DATA
    # ==================================================

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


    # ==================================================
    # SAVE DECODED DATA
    # ==================================================

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
        None,
        co,
        hc,
        co2,
        o2,
        result

    ))


    conn.commit()
    conn.close()


    # ==================================================
    # TERMINAL OUTPUT
    # ==================================================

    print()
    print("==============================================")
    print("       PUC MACHINE DATA RECEIVED")
    print("==============================================")

    print("Received Time :", received_at)

    print("Machine ID    :", machine_id)

    print()
    print("RAW HEX:")
    print(raw_hex)

    print()
    print("DECODED DATA:")
    print("CO  :", co)
    print("HC  :", hc)
    print("CO2 :", co2)
    print("O2  :", o2)

    print()
    print("==============================================")
    print()


    # ==================================================
    # RESPONSE
    # ==================================================

    return jsonify({

        "status": "success",

        "message":
        "Raw PUC machine data received",

        "machine_id":
        machine_id,

        "received_at":
        received_at,

        "raw_hex":
        raw_hex,

        "decoded": {

            "co": co,

            "hc": hc,

            "co2": co2,

            "o2": o2,

            "result": result

        }

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


    html_page = """

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

            .null {

                color: gray;

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


    # ==================================================
    # TABLE ROWS
    # ==================================================

    for row in rows:

        co = row["co"]
        hc = row["hc"]
        co2 = row["co2"]
        o2 = row["o2"]
        result = row["result"]

        html_page += f"""

            <tr>

                <td>{row['id']}</td>

                <td>{html.escape(
                    str(row['received_at'])
                )}</td>

                <td>{html.escape(
                    str(row['machine_id'])
                )}</td>

                <td>{co if co is not None else '<span class="null">Waiting for decoder</span>'}</td>

                <td>{hc if hc is not None else '<span class="null">Waiting for decoder</span>'}</td>

                <td>{co2 if co2 is not None else '<span class="null">Waiting for decoder</span>'}</td>

                <td>{o2 if o2 is not None else '<span class="null">Waiting for decoder</span>'}</td>

                <td>{result if result is not None else '<span class="null">-</span>'}</td>

            </tr>

        """


    html_page += """

        </table>

    </body>

    </html>

    """


    return html_page


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


    html_page = """

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

        html_page += f"""

            <tr>

                <td>{row['id']}</td>

                <td>{html.escape(
                    str(row['received_at'])
                )}</td>

                <td>{html.escape(
                    str(row['machine_id'])
                )}</td>

                <td class="hex">
                    {html.escape(
                        str(row['raw_hex'])
                    )}
                </td>

            </tr>

        """


    html_page += """

        </table>

    </body>

    </html>

    """


    return html_page


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