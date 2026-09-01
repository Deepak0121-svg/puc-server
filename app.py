from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# Store received data in memory
received_data = []


# ============================================================
# HOME
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return """
    <h1>PUC Data Server</h1>

    <p>Server is running successfully.</p>

    <p>
        POST API:
        <b>/api/v1/test/start</b>
    </p>

    <p>
        View received data:
        <b>/view</b>
    </p>
    """


# ============================================================
# RECEIVE POST DATA
# ============================================================

@app.route(
    "/api/v1/test/start",
    methods=["POST"]
)
def receive_data():

    # --------------------------------------------------------
    # Read JSON
    # --------------------------------------------------------

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({

            "status": "error",

            "message": "JSON data not received"

        }), 400


    # --------------------------------------------------------
    # Add server time
    # --------------------------------------------------------

    item = {

        "received_at":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "data":
            data

    }


    # --------------------------------------------------------
    # Store data
    # --------------------------------------------------------

    received_data.append(item)


    # --------------------------------------------------------
    # Terminal
    # --------------------------------------------------------

    print()
    print("==============================================")
    print("             DATA RECEIVED")
    print("==============================================")

    print(
        json.dumps(
            data,
            indent=4
        )
    )

    print("==============================================")
    print()


    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return jsonify({

        "status": "success",

        "message":
            "Data received successfully",

        "received_data":
            data

    }), 200


# ============================================================
# VIEW RAW JSON DATA
# ============================================================

@app.route(
    "/view",
    methods=["GET"]
)
def view_data():

    if not received_data:

        return """
        <h2>No data received yet.</h2>
        """


    output = ""

    for item in reversed(received_data):

        output += f"""
        <pre>
Received Time:
{item["received_at"]}

Data:
{json.dumps(
    item["data"],
    indent=4
)}

----------------------------------------------
        </pre>
        """


    return f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>PUC Received Data</title>

    </head>

    <body>

        <h1>PUC Received Data</h1>

        {output}

    </body>

    </html>
    """


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000

    )