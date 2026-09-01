
from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# ============================================================
# STORE RECEIVED DATA
# ============================================================

received_data = []


# ============================================================
# HOME
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return """
    <!DOCTYPE html>

    <html>

    <head>

        <title>PUC Data Server</title>

    </head>

    <body>

        <h1>PUC Data Server</h1>

        <p>Server is running successfully.</p>

        <h3>POST API</h3>

        <p>
            /api/v1/test/start
        </p>

        <h3>View Received Data</h3>

        <p>
            <a href="/view">
                /view
            </a>
        </p>

    </body>

    </html>
    """


# ============================================================
# RECEIVE ANY JSON DATA
# ============================================================

@app.route(
    "/api/v1/test/start",
    methods=["POST"]
)
def receive_data():

    received_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    # ========================================================
    # GET RAW BODY
    # ========================================================

    raw_body = request.get_data(
        as_text=True
    )


    # ========================================================
    # PRINT REQUEST INFORMATION
    # ========================================================

    print()
    print("==================================================")
    print("             POST DATA RECEIVED")
    print("==================================================")

    print()
    print("Received Time:")
    print(received_at)

    print()
    print("Method:")
    print(request.method)

    print()
    print("URL:")
    print(request.url)

    print()
    print("Content-Type:")
    print(request.content_type)

    print()
    print("RAW DATA:")
    print(raw_body)


    # ========================================================
    # TRY TO READ JSON
    # ========================================================

    data = request.get_json(
        silent=True
    )


    # ========================================================
    # IF JSON IS INVALID
    # ========================================================

    if data is None:

        print()
        print("ERROR:")
        print("Valid JSON data was not received.")

        print()
        print("==================================================")
        print()

        return jsonify({

            "status": "error",

            "message":
                "Valid JSON data was not received",

            "raw_data":
                raw_body

        }), 400


    # ========================================================
    # STORE EXACT JSON
    # ========================================================

    item = {

        "received_at":
            received_at,

        "data":
            data

    }

    received_data.append(
        item
    )


    # ========================================================
    # DISPLAY EXACT JSON IN TERMINAL
    # ========================================================

    print()
    print("JSON DATA:")
    print("----------------------------------------------")

    print(
        json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        )
    )

    print("----------------------------------------------")

    print()
    print("Total Received:")
    print(len(received_data))

    print()
    print("==================================================")
    print()


    # ========================================================
    # RETURN SAME JSON BACK
    # ========================================================

    return jsonify({

        "status":
            "success",

        "message":
            "Data received successfully",

        "received_data":
            data

    }), 200


# ============================================================
# VIEW EXACT RECEIVED JSON
# ============================================================

@app.route(
    "/view",
    methods=["GET"]
)
def view_data():

    if not received_data:

        return """
        <!DOCTYPE html>

        <html>

        <head>

            <title>Received Data</title>

        </head>

        <body>

            <h1>Received Data</h1>

            <h2>No data received yet.</h2>

        </body>

        </html>
        """


    output = ""


    # ========================================================
    # NEWEST DATA FIRST
    # ========================================================

    for item in reversed(
        received_data
    ):

        json_text = json.dumps(

            item["data"],

            indent=4,

            ensure_ascii=False

        )


        output += f"""

        <div style="
            background:#f5f5f5;
            padding:20px;
            margin-bottom:20px;
            border:1px solid #ddd;
        ">

            <p>
                <b>Received Time:</b>
                {item["received_at"]}
            </p>

            <pre>{json_text}</pre>

        </div>

        """


    # ========================================================
    # HTML PAGE
    # ========================================================

    return f"""

    <!DOCTYPE html>

    <html>

    <head>

        <title>Received JSON Data</title>

        <meta
            http-equiv="refresh"
            content="5"
        >

    </head>

    <body>

        <h1>
            Received JSON Data
        </h1>

        {output}

    </body>

    </html>

    """


# ============================================================
# 404
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({

        "status":
            "error",

        "message":
            "URL not found",

        "requested_url":
            request.url,

        "method":
            request.method

    }), 404


# ============================================================
# 405
# ============================================================

@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({

        "status":
            "error",

        "message":
            "HTTP method not allowed",

        "requested_url":
            request.url,

        "method":
            request.method

    }), 405


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print()
    print("==================================================")
    print("              PUC DATA SERVER")
    print("==================================================")

    print()
    print("Local URL:")
    print(
        "http://127.0.0.1:5000/"
    )

    print()
    print("POST API:")
    print(
        "http://127.0.0.1:5000"
        "/api/v1/test/start"
    )

    print()
    print("View Data:")
    print(
        "http://127.0.0.1:5000/view"
    )

    print()
    print("==================================================")
    print()

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=False

    )

