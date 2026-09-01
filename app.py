from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import html

app = Flask(__name__)

DATABASE = "data.db"


# ============================================================
# DATABASE
# ============================================================

def init_db():

    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS machine_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            received_at TEXT,
            machine_id TEXT,
            raw_data TEXT,
            content_type TEXT
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# SAVE DATA
# ============================================================

def save_data(machine_id, raw_data, content_type):

    received_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        INSERT INTO machine_data
        (
            received_at,
            machine_id,
            raw_data,
            content_type
        )
        VALUES (?, ?, ?, ?)
    """, (
        received_at,
        machine_id,
        raw_data,
        content_type
    ))

    conn.commit()
    conn.close()

    return received_at


# ============================================================
# HOME
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return """
    <!DOCTYPE html>

    <html>

    <head>

        <title>PUC GSM Server</title>

        <style>

            body {
                font-family: Arial;
                margin: 40px;
                background: #f5f5f5;
            }

            .box {
                background: white;
                padding: 25px;
                margin-bottom: 20px;
                border-radius: 10px;
            }

            a {
                font-size: 18px;
            }

        </style>

    </head>

    <body>

        <div class="box">

            <h1>PUC GSM Data Server</h1>

            <p>
                Server is running successfully.
            </p>

        </div>

        <div class="box">

            <h2>API Endpoint</h2>

            <p>
                POST:
                <b>/api/v1/puc/raw</b>
            </p>

        </div>

        <div class="box">

            <h2>View Received Data</h2>

            <p>
                <a href="/view">
                    View Data
                </a>
            </p>

        </div>

    </body>

    </html>
    """


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "online",
        "message": "PUC GSM server is running"
    }), 200


# ============================================================
# RAW DATA API
# ============================================================

@app.route(
    "/api/v1/puc/raw",
    methods=["POST"]
)
def receive_raw_data():

    print()
    print("==============================================")
    print("          PUC DATA RECEIVED")
    print("==============================================")

    # --------------------------------------------------------
    # CONTENT TYPE
    # --------------------------------------------------------

    content_type = request.content_type or ""

    print("Content-Type:", content_type)

    # --------------------------------------------------------
    # JSON DATA
    # --------------------------------------------------------

    if request.is_json:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({
                "status": "error",
                "message": "JSON data not received"
            }), 400

        machine_id = data.get(
            "machine_id",
            "UNKNOWN"
        )

        raw_data = data.get(
            "raw_hex",
            ""
        )

        if not raw_data:

            raw_data = str(data)

    # --------------------------------------------------------
    # FORM DATA
    # --------------------------------------------------------

    elif request.form:

        machine_id = request.form.get(
            "machine_id",
            "UNKNOWN"
        )

        raw_data = request.form.get(
            "raw_hex",
            ""
        )

        if not raw_data:

            raw_data = str(
                request.form.to_dict()
            )

    # --------------------------------------------------------
    # PLAIN TEXT / RAW BODY
    # --------------------------------------------------------

    else:

        raw_body = request.get_data(
            as_text=True
        )

        machine_id = request.args.get(
            "machine_id",
            "UNKNOWN"
        )

        raw_data = raw_body

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not raw_data:

        return jsonify({
            "status": "error",
            "message": "No data received"
        }), 400

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    received_at = save_data(
        machine_id,
        raw_data,
        content_type
    )

    # --------------------------------------------------------
    # TERMINAL
    # --------------------------------------------------------

    print("Received Time :", received_at)
    print("Machine ID    :", machine_id)
    print("Raw Data      :", raw_data)

    print("==============================================")
    print()

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return jsonify({

        "status": "success",

        "message":
        "PUC machine data received successfully",

        "machine_id":
        machine_id,

        "received_at":
        received_at,

        "raw_data":
        raw_data

    }), 200


# ============================================================
# VIEW DATA
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
        FROM machine_data
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    html_page = """

    <!DOCTYPE html>

    <html>

    <head>

        <title>PUC Machine Data</title>

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

            .raw {
                font-family: monospace;
                text-align: left;
                word-break: break-all;
            }

        </style>

    </head>

    <body>

        <h1>PUC Machine Received Data</h1>

        <table>

            <tr>

                <th>ID</th>

                <th>Received Time</th>

                <th>Machine ID</th>

                <th>Raw Data</th>

                <th>Content Type</th>

            </tr>

    """

    for row in rows:

        html_page += f"""

        <tr>

            <td>
                {row["id"]}
            </td>

            <td>
                {html.escape(
                    str(row["received_at"])
                )}
            </td>

            <td>
                {html.escape(
                    str(row["machine_id"])
                )}
            </td>

            <td class="raw">
                {html.escape(
                    str(row["raw_data"])
                )}
            </td>

            <td>
                {html.escape(
                    str(row["content_type"])
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
# START
# ============================================================

init_db()


if __name__ == "__main__":

    print()
    print("==============================================")
    print("          PUC GSM SERVER STARTED")
    print("==============================================")
    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )