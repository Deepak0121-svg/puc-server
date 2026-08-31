from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import html

from decoder import decode_puc_hex


app = Flask(__name__)

DATABASE = "data.db"


# ============================================================
# DATABASE
# ============================================================

def init_db():

    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS pollution_results (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            received_at TEXT,

            machine_id TEXT,

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


# ============================================================
# HOME
# ============================================================

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


# ============================================================
# NORMAL POLLUTION API
# ============================================================

@app.route(
    "/api/v1/puc/results",
    methods=["GET", "POST"]
)
def receive_data():

    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        machine_id = request.args.get(
            "machine_id"
        )

        co = request.args.get(
            "co"
        )

        hc = request.args.get(
            "hc"
        )

        co2 = request.args.get(
            "co2"
        )

        o2 = request.args.get(
            "o2"
        )

        result = request.args.get(
            "result"
        )

    # ========================================================
    # POST
    # ========================================================

    else:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({

                "status": "error",

                "message":
                "JSON data not received"

            }), 400

        machine_id = data.get(
            "machine_id"
        )

        co = data.get(
            "co"
        )

        hc = data.get(
            "hc"
        )

        co2 = data.get(
            "co2"
        )

        o2 = data.get(
            "o2"
        )

        result = data.get(
            "result"
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    if not machine_id:

        return jsonify({

            "status": "error",

            "message":
            "machine_id is required"

        }), 400

    # ========================================================
    # TIME
    # ========================================================

    received_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # ========================================================
    # DATABASE
    # ========================================================

    conn = sqlite3.connect(
        DATABASE
    )

    conn.execute("""
        INSERT INTO pollution_results
        (
            received_at,
            machine_id,
            co,
            hc,
            co2,
            o2,
            result
        )

        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (

        received_at,

        machine_id,

        co,

        hc,

        co2,

        o2,

        result

    ))

    conn.commit()

    conn.close()

    # ========================================================
    # TERMINAL
    # ========================================================

    print()

    print("==============================================")

    print("          PUC DATA RECEIVED")

    print("==============================================")

    print(
        "Received Time :",
        received_at
    )

    print(
        "Machine ID    :",
        machine_id
    )

    print(
        "CO            :",
        co
    )

    print(
        "HC            :",
        hc
    )

    print(
        "CO2           :",
        co2
    )

    print(
        "O2            :",
        o2
    )

    print(
        "Result        :",
        result
    )

    print(
        "=============================================="
    )

    print()

    return jsonify({

        "status":
        "success",

        "message":
        "Pollution data received successfully",

        "machine_id":
        machine_id

    }), 200


# ============================================================
# RAW PUC MACHINE HEX API
# ============================================================

@app.route(
    "/api/v1/puc/raw",
    methods=["POST"]
)
def receive_raw_data():

    # ========================================================
    # JSON
    # ========================================================

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({

            "status":
            "error",

            "message":
            "JSON data not received"

        }), 400

    # ========================================================
    # READ DATA
    # ========================================================

    machine_id = data.get(
        "machine_id"
    )

    raw_hex = data.get(
        "raw_hex"
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    if not machine_id:

        return jsonify({

            "status":
            "error",

            "message":
            "machine_id is required"

        }), 400

    if not raw_hex:

        return jsonify({

            "status":
            "error",

            "message":
            "raw_hex is required"

        }), 400

    # ========================================================
    # DECODE
    # ========================================================

    decoded = decode_puc_hex(
        raw_hex
    )

    # ========================================================
    # CHECK DECODER ERROR
    # ========================================================

    if decoded["error"]:

        return jsonify({

            "status":
            "error",

            "message":
            decoded["error"]

        }), 400

    # ========================================================
    # VALUES
    # ========================================================

    co = decoded["co"]

    hc = decoded["hc"]

    co2 = decoded["co2"]

    o2 = decoded["o2"]

    result = decoded["result"]

    clean_hex = decoded["raw_hex"]

    # ========================================================
    # TIME
    # ========================================================

    received_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # ========================================================
    # DATABASE
    # ========================================================

    conn = sqlite3.connect(
        DATABASE
    )

    # ========================================================
    # SAVE RAW DATA
    # ========================================================

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

        clean_hex

    ))

    # ========================================================
    # SAVE DECODED DATA
    # ========================================================

    conn.execute("""
        INSERT INTO pollution_results
        (
            received_at,
            machine_id,
            co,
            hc,
            co2,
            o2,
            result
        )

        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (

        received_at,

        machine_id,

        co,

        hc,

        co2,

        o2,

        result

    ))

    conn.commit()

    conn.close()

    # ========================================================
    # TERMINAL OUTPUT
    # ========================================================

    print()

    print("==================================================")

    print("          PUC MACHINE DATA RECEIVED")

    print("==================================================")

    print()

    print(
        "Received Time :",
        received_at
    )

    print(
        "Machine ID    :",
        machine_id
    )

    print()

    print("RAW HEX:")

    print(
        clean_hex
    )

    print()

    print(
        "TOTAL BYTES :",
        decoded["total_bytes"]
    )

    print()

    print("BYTE ANALYSIS:")

    for item in decoded["bytes"]:

        print(

            f"BYTE[{item['index']:02d}] = "
            f"{item['hex']} "
            f"DEC={item['decimal']}"

        )

    print()

    print("ASCII:")

    print(
        decoded["ascii"]
    )

    print()

    print("DECODED POLLUTION VALUES:")

    print(
        "CO  :",
        co
    )

    print(
        "HC  :",
        hc
    )

    print(
        "CO2 :",
        co2
    )

    print(
        "O2  :",
        o2
    )

    print(
        "RESULT :",
        result
    )

    print()

    print(
        "=================================================="
    )

    print()

    # ========================================================
    # RESPONSE
    # ========================================================

    return jsonify({

        "status":
        "success",

        "message":
        "Raw PUC machine data received",

        "machine_id":
        machine_id,

        "received_at":
        received_at,

        "raw_hex":
        clean_hex,

        "decoded": {

            "co":
            co,

            "hc":
            hc,

            "co2":
            co2,

            "o2":
            o2,

            "result":
            result

        },

        "analysis": {

            "total_bytes":
            decoded["total_bytes"],

            "bytes":
            decoded["bytes"],

            "ascii":
            decoded["ascii"],

            "two_byte_candidates":
            decoded[
                "two_byte_candidates"
            ],

            "float_candidates":
            decoded[
                "float_candidates"
            ],

            "bcd_candidates":
            decoded[
                "bcd_candidates"
            ]

        }

    }), 200


# ============================================================
# VIEW POLLUTION RESULTS
# ============================================================

@app.route(
    "/view",
    methods=["GET"]
)
def view_data():

    conn = sqlite3.connect(
        DATABASE
    )

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

            th,
            td {

                border: 1px solid #999;

                padding: 10px;

                text-align: center;

            }

            th {

                background: #eeeeee;

            }

            .waiting {

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

    # ========================================================
    # TABLE ROWS
    # ========================================================

    for row in rows:

        co = row["co"]

        hc = row["hc"]

        co2 = row["co2"]

        o2 = row["o2"]

        result = row["result"]

        if co is not None:

            co_display = html.escape(
                str(co)
            )

        else:

            co_display = (
                '<span class="waiting">'
                'Waiting for decoder'
                '</span>'
            )

        if hc is not None:

            hc_display = html.escape(
                str(hc)
            )

        else:

            hc_display = (
                '<span class="waiting">'
                'Waiting for decoder'
                '</span>'
            )

        if co2 is not None:

            co2_display = html.escape(
                str(co2)
            )

        else:

            co2_display = (
                '<span class="waiting">'
                'Waiting for decoder'
                '</span>'
            )

        if o2 is not None:

            o2_display = html.escape(
                str(o2)
            )

        else:

            o2_display = (
                '<span class="waiting">'
                'Waiting for decoder'
                '</span>'
            )

        if result is not None:

            result_display = html.escape(
                str(result)
            )

        else:

            result_display = "-"

        html_page += f"""

            <tr>

                <td>
                    {row['id']}
                </td>

                <td>
                    {html.escape(
                        str(row['received_at'])
                    )}
                </td>

                <td>
                    {html.escape(
                        str(row['machine_id'])
                    )}
                </td>

                <td>
                    {co_display}
                </td>

                <td>
                    {hc_display}
                </td>

                <td>
                    {co2_display}
                </td>

                <td>
                    {o2_display}
                </td>

                <td>
                    {result_display}
                </td>

            </tr>

        """

    html_page += """

        </table>

    </body>

    </html>

    """

    return html_page


# ============================================================
# VIEW RAW DATA
# ============================================================

@app.route(
    "/raw",
    methods=["GET"]
)
def view_raw_data():

    conn = sqlite3.connect(
        DATABASE
    )

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

            th,
            td {

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

    # ========================================================
    # RAW ROWS
    # ========================================================

    for row in rows:

        html_page += f"""

            <tr>

                <td>
                    {row['id']}
                </td>

                <td>
                    {html.escape(
                        str(row['received_at'])
                    )}
                </td>

                <td>
                    {html.escape(
                        str(row['machine_id'])
                    )}
                </td>

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


# ============================================================
# START SERVER
# ============================================================

init_db()


if __name__ == "__main__":

    print()

    print(
        "=============================================="
    )

    print(
        "       PUC POLLUTION SERVER STARTED"
    )

    print(
        "=============================================="
    )

    print()

    print("Local URL:")

    print(
        "http://127.0.0.1:5000"
    )

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

    print(
        "=============================================="
    )

    print()

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )