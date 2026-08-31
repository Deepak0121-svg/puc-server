import serial
import requests
import time


# ==================================================
# SETTINGS
# ==================================================

COM_PORT = "COM14"

BAUDRATE = 9600

SERVER_URL = (
    "https://puc-server.onrender.com/raw"
    "/api/v1/puc/raw"
)

MACHINE_ID = "PUC001"


# ==================================================
# SERIAL CONNECTION
# ==================================================

try:

    ser = serial.Serial(

        port=COM_PORT,

        baudrate=BAUDRATE,

        bytesize=serial.EIGHTBITS,

        parity=serial.PARITY_NONE,

        stopbits=serial.STOPBITS_ONE,

        timeout=1

    )

    print()
    print("==============================================")
    print("       PUC SERIAL BRIDGE STARTED")
    print("==============================================")

    print("COM Port :", COM_PORT)

    print("Baudrate :", BAUDRATE)

    print("Server   :", SERVER_URL)

    print()
    print("Waiting for PUC machine data...")
    print()

except Exception as e:

    print("Serial Port Error:")
    print(e)

    exit()


# ==================================================
# RECEIVE DATA
# ==================================================

while True:

    try:

        # Check available bytes

        if ser.in_waiting > 0:

            data = ser.read(ser.in_waiting)


            if data:

                # Convert binary bytes to HEX

                raw_hex = data.hex(" ").upper()


                # ----------------------------------
                # DISPLAY
                # ----------------------------------

                print()
                print("----------------------------------------------")

                print("Data received from PUC:")

                print(raw_hex)

                print("----------------------------------------------")


                # ----------------------------------
                # JSON DATA
                # ----------------------------------

                payload = {

                    "machine_id": MACHINE_ID,

                    "raw_hex": raw_hex

                }


                # ----------------------------------
                # SEND TO SERVER
                # ----------------------------------

                try:

                    response = requests.post(

                        SERVER_URL,

                        json=payload,

                        timeout=20

                    )


                    print(
                        "Server Status :",
                        response.status_code
                    )

                    print(
                        "Server Response :",
                        response.text
                    )


                except requests.exceptions.RequestException as e:

                    print("Server Connection Error:")

                    print(e)


        else:

            time.sleep(0.05)


    except KeyboardInterrupt:

        print()
        print("Program stopped.")

        break


    except Exception as e:

        print("Error:")

        print(e)

        time.sleep(1)


# ==================================================
# CLOSE SERIAL PORT
# ==================================================

ser.close()