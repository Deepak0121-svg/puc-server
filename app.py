from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import html
import struct
import re

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
# HEX CLEANING
# ==================================================

def clean_hex_string(raw_hex):

    """
    Accepts HEX in formats such as:

    01 02 03 04
    01020304
    01-02-03-04
    01:02:03:04
    """

    if not raw_hex:
        raise ValueError("Empty HEX data")

    clean = raw_hex.strip()

    clean = clean.replace("-", "")
    clean = clean.replace(":", "")
    clean = clean.replace(",", "")
    clean = clean.replace("\n", "")
    clean = clean.replace("\r", "")
    clean = clean.replace("\t", "")
    clean = clean.replace(" ", "")

    # Remove optional 0x
    clean = re.sub(r"0x", "", clean, flags=re.IGNORECASE)

    if len(clean) % 2 != 0:

        raise ValueError(
            "HEX data contains an odd number of characters"
        )

    if not re.fullmatch(r"[0-9A-Fa-f]+", clean):

        raise ValueError(
            "Invalid HEX characters detected"
        )

    return clean.upper()


# ==================================================
# FORMAT BYTE DATA
# ==================================================

def format_bytes(data):

    output = []

    for i, byte in enumerate(data):

        output.append({
            "index": i,
            "hex": f"{byte:02X}",
            "decimal": byte
        })

    return output


# ==================================================
# TWO BYTE CANDIDATES
# ==================================================

def get_two_byte_candidates(data):

    candidates = []

    for i in range(len(data) - 1):

        high = data[i]
        low = data[i + 1]

        # Big endian
        big_endian = (high << 8) | low

        # Little endian
        little_endian = (low << 8) | high

        candidates.append({

            "position": f"{i}-{i + 1}",

            "hex": f"{high:02X} {low:02X}",

            "big_endian": big_endian,

            "little_endian": little_endian,

            "big_div_10": round(
                big_endian / 10,
                3
            ),

            "big_div_100": round(
                big_endian / 100,
                3
            ),

            "big_div_1000": round(
                big_endian / 1000,
                3
            ),

            "little_div_10": round(
                little_endian / 10,
                3
            ),

            "little_div_100": round(
                little_endian / 100,
                3
            ),

            "little_div_1000": round(
                little_endian / 1000,
                3
            )
        })

    return candidates


# ==================================================
# FOUR BYTE FLOAT CANDIDATES
# ==================================================

def get_float_candidates(data):

    candidates = []

    for i in range(len(data) - 3):

        chunk = data[i:i + 4]

        hex_value = " ".join(
            f"{x:02X}" for x in chunk
        )

        # Big endian IEEE754
        try:

            big_float = struct.unpack(
                ">f",
                bytes(chunk)
            )[0]

        except:

            big_float = None

        # Little endian IEEE754
        try:

            little_float = struct.unpack(
                "<f",
                bytes(chunk)
            )[0]

        except:

            little_float = None

        candidates.append({

            "position": f"{i}-{i + 3}",

            "hex": hex_value,

            "big_endian_float":
                round(big_float, 6)
                if big_float is not None
                else None,

            "little_endian_float":
                round(little_float, 6)
                if little_float is not None
                else None
        })

    return candidates


# ==================================================
# ASCII DETECTION
# ==================================================

def get_ascii(data):

    result = ""

    for byte in data:

        if 32 <= byte <= 126:

            result += chr(byte)

        else:

            result += "."

    return result


# ==================================================
# POSSIBLE DECIMAL / BCD VALUES
# ==================================================

def bcd_value(byte):

    high = (byte >> 4) & 0x0F
    low = byte & 0x0F

    if high > 9 or low > 9:

        return None

    return high * 10 + low


def get_bcd_candidates(data):

    candidates = []

    for i, byte in enumerate(data):

        value = bcd_value(byte)

        if value is not None:

            candidates.append({

                "position": i,

                "hex": f"{byte:02X}",

                "bcd": value

            })

    return candidates


# ==================================================
# ACTUAL PUC DECODER
# ==================================================

def decode_puc_hex(raw_hex):

    """
    IMPORTANT:

    This function performs protocol-independent
    HEX analysis.

    It DOES NOT assume that BYTE[5] is CO,
    BYTE[6] is HC, etc.

    Exact CO / HC / CO2 / O2 mapping requires
    the manufacturer's RS232 protocol.

    """

    decoded = {

        "co": None,

        "hc": None,

        "co2": None,

        "o2": None,

        "result": None,

        "total_bytes": 0,

        "bytes": [],

        "ascii": "",

        "two_byte_candidates": [],

        "float_candidates": [],

        "bcd_candidates": []
    }

    try:

        # ------------------------------------------
        # CLEAN HEX
        # ------------------------------------------

        clean_hex = clean_hex_string(raw_hex)

        # ------------------------------------------
        # HEX -> BYTES
        # ------------------------------------------

        data = bytes.fromhex(clean_hex)

        decoded["total_bytes"] = len(data)

        # ------------------------------------------
        # BYTE LIST
        # ------------------------------------------

        decoded["bytes"] = format_bytes(data)

        # ------------------------------------------
        # ASCII
        # ------------------------------------------

        decoded["ascii"] = get_ascii(data)

        # ------------------------------------------
        # TWO BYTE VALUES
        # ------------------------------------------

        decoded["two_byte_candidates"] = \
            get_two_byte_candidates(data)

        # ------------------------------------------
        # FLOAT VALUES
        # ------------------------------------------

        decoded["float_candidates"] = \
            get_float_candidates(data)

        # ------------------------------------------
        # BCD VALUES
        # ------------------------------------------

        decoded["bcd_candidates"] = \
            get_bcd_candidates(data)

        # ==================================================
        # TERMINAL DISPLAY
        # ==================================================

        print()
        print("==================================================")
        print("                 HEX DECODER")
        print("==================================================")

        print()

        print("RAW HEX:")
        print(clean_hex)

        print()

        print(
            "TOTAL BYTES :",
            len(data)
        )

        print()

        print("--------------------------------------------------")
        print("BYTE ANALYSIS")
        print("--------------------------------------------------")

        for item in decoded["bytes"]:

            print(
                f"BYTE[{item['index']:02d}] = "
                f"{item['hex']} "
                f"DEC={item['decimal']}"
            )

        print()

        print("--------------------------------------------------")
        print("ASCII")
        print("--------------------------------------------------")

        print(decoded["ascii"])

        print()

        print("--------------------------------------------------")
        print("2-BYTE INTEGER CANDIDATES")
        print("--------------------------------------------------")

        for item in decoded["two_byte_candidates"]:

            print(
                f"[{item['position']}] "
                f"{item['hex']} | "
                f"BE={item['big_endian']} | "
                f"LE={item['little_endian']} | "
                f"BE/10={item['big_div_10']} | "
                f"BE/100={item['big_div_100']} | "
                f"BE/1000={item['big_div_1000']}"
            )

        print()

        print("--------------------------------------------------")
        print("4-BYTE FLOAT CANDIDATES")
        print("--------------------------------------------------")

        for item in decoded["float_candidates"]:

            print(
                f"[{item['position']}] "
                f"{item['hex']} | "
                f"BE_FLOAT={item['big_endian_float']} | "
                f"LE_FLOAT={item['little_endian_float']}"
            )

        print()

        print("--------------------------------------------------")
        print("BCD CANDIDATES")
        print("--------------------------------------------------")

        for item in decoded["bcd_candidates"]:

            print(
                f"BYTE[{item['position']}] "
                f"{item['hex']} -> "
                f"{item['bcd']}"
            )

        print()

        # ==================================================
        # EXACT VALUES
        # ==================================================

        print("==================================================")
        print("             POLLUTION VALUES")
        print("==================================================")

        print("CO  :", decoded["co"])
        print("HC  :", decoded["hc"])
        print("CO2 :", decoded["co2"])
        print("O2  :", decoded["o2"])
        print("RESULT :", decoded["result"])

        print("==================================================")
        print()

        return decoded

    except ValueError as e:

        print()
        print("==================================================")
        print("HEX DECODER ERROR")
        print("==================================================")

        print(str(e))

        print("==================================================")
        print()

        return decoded


# ==================================================
# HOME
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
# NORMAL POLLUTION API
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

        machine_id = request.args.get(
            "machine_id"
        )

        vehicle_no = request.args.get(
            "vehicle_no"
        )

        co = request.args.get("co")

        hc = request.args.get("hc")

        co2 = request.args.get("co2")

        o2 = request.args.get("o2")

        result = request.args.get("result")

    # ==================================================
    # POST
    # ==================================================

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

        vehicle_no = data.get(
            "vehicle_no"
        )

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

            "message":
            "machine_id is required"

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

        "machine_id":
        machine_id,

        "vehicle_no":
        vehicle_no

    }), 200


# ==================================================
# RAW HEX API
# ==================================================

@app.route(
    "/api/v1/puc/raw",
    methods=["POST"]
)
def receive_raw_data():

    # ==================================================
    # JSON
    # ==================================================

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({

            "status": "error",

            "message":
            "JSON data not received"

        }), 400

    # ==================================================
    # READ DATA
    # ==================================================

    machine_id = data.get(
        "machine_id"
    )

    raw_hex = data.get(
        "raw_hex"
    )

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

    try:

        clean_hex = clean_hex_string(
            raw_hex
        )

    except ValueError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    # ==================================================
    # DECODE
    # ==================================================

    decoded = decode_puc_hex(
        clean_hex
    )

    # ==================================================
    # VALUES
    # ==================================================

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
    # DATABASE
    # ==================================================

    conn = sqlite3.connect(DATABASE)

    # ==================================================
    # SAVE RAW DATA
    # ==================================================

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
    print(clean_hex)

    print()

    print("TOTAL BYTES:")
    print(decoded["total_bytes"])

    print()

    print("DECODED DATA:")
    print("CO  :", co)
    print("HC  :", hc)
    print("CO2 :", co2)
    print("O2  :", o2)
    print("RESULT :", result)

    print()

    print("==============================================")
    print()

    # ==================================================
    # RESPONSE
    # ==================================================

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

            "co": co,

            "hc": hc,

            "co2": co2,

            "o2": o2,

            "result": result
        },

        "analysis": {

            "total_bytes":
            decoded["total_bytes"],

            "bytes":
            decoded["bytes"],

            "ascii":
            decoded["ascii"],

            "two_byte_candidates":
            decoded["two_byte_candidates"],

            "float_candidates":
            decoded["float_candidates"],

            "bcd_candidates":
            decoded["bcd_candidates"]
        }

    }), 200


# ==================================================
# VIEW POLLUTION RESULTS
# ==================================================

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

            th, td {

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

                <th>Vehicle No</th>

                <th>CO</th>

                <th>HC</th>

                <th>CO2</th>

                <th>O2</th>

                <th>Result</th>

            </tr>

    """

    for row in rows:

        co = row["co"]

        hc = row["hc"]

        co2 = row["co2"]

        o2 = row["o2"]

        result = row["result"]

        vehicle_no = row["vehicle_no"]

        co_display = (
            str(co)
            if co is not None
            else
            '<span class="waiting">'
            'Waiting for decoder'
            '</span>'
        )

        hc_display = (
            str(hc)
            if hc is not None
            else
            '<span class="waiting">'
            'Waiting for decoder'
            '</span>'
        )

        co2_display = (
            str(co2)
            if co2 is not None
            else
            '<span class="waiting">'
            'Waiting for decoder'
            '</span>'
        )

        o2_display = (
            str(o2)
            if o2 is not None
            else
            '<span class="waiting">'
            'Waiting for decoder'
            '</span>'
        )

        result_display = (
            html.escape(str(result))
            if result is not None
            else "-"
        )

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
                    {html.escape(
                        str(vehicle_no)
                    ) if vehicle_no else "-"}
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


# ==================================================
# VIEW RAW DATA
# ==================================================

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

    print("==============================================")
    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )