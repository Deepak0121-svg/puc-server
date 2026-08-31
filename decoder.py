# ============================================================
# decoder.py
# PUC MACHINE HEX DECODER
# ============================================================

import struct
import re


# ============================================================
# CLEAN HEX STRING
# ============================================================

def clean_hex_string(raw_hex):

    if not raw_hex:
        raise ValueError("Empty HEX data")

    clean = str(raw_hex).strip()

    # Remove common separators
    clean = clean.replace("-", "")
    clean = clean.replace(":", "")
    clean = clean.replace(",", "")
    clean = clean.replace(" ", "")
    clean = clean.replace("\n", "")
    clean = clean.replace("\r", "")
    clean = clean.replace("\t", "")

    # Remove 0x
    clean = re.sub(
        r"0x",
        "",
        clean,
        flags=re.IGNORECASE
    )

    # HEX must contain even number of characters
    if len(clean) % 2 != 0:
        raise ValueError(
            "HEX data contains an odd number of characters"
        )

    # Validate HEX
    if not re.fullmatch(
        r"[0-9A-Fa-f]+",
        clean
    ):
        raise ValueError(
            "Invalid HEX characters detected"
        )

    return clean.upper()


# ============================================================
# BYTE ANALYSIS
# ============================================================

def format_bytes(data):

    result = []

    for index, byte in enumerate(data):

        result.append({

            "index": index,

            "hex": f"{byte:02X}",

            "decimal": byte

        })

    return result


# ============================================================
# ASCII
# ============================================================

def get_ascii(data):

    result = ""

    for byte in data:

        if 32 <= byte <= 126:

            result += chr(byte)

        else:

            result += "."

    return result


# ============================================================
# BCD
# ============================================================

def bcd_value(byte):

    high = (byte >> 4) & 0x0F

    low = byte & 0x0F

    if high > 9 or low > 9:

        return None

    return high * 10 + low


def get_bcd_candidates(data):

    candidates = []

    for index, byte in enumerate(data):

        value = bcd_value(byte)

        if value is not None:

            candidates.append({

                "position": index,

                "hex": f"{byte:02X}",

                "bcd": value

            })

    return candidates


# ============================================================
# TWO BYTE INTEGER ANALYSIS
# ============================================================

def get_two_byte_candidates(data):

    candidates = []

    for i in range(len(data) - 1):

        byte1 = data[i]

        byte2 = data[i + 1]

        # Big endian
        big_endian = (
            (byte1 << 8) |
            byte2
        )

        # Little endian
        little_endian = (
            (byte2 << 8) |
            byte1
        )

        candidates.append({

            "position":
                f"{i}-{i + 1}",

            "hex":
                f"{byte1:02X} {byte2:02X}",

            "big_endian":
                big_endian,

            "little_endian":
                little_endian,

            "big_div_10":
                round(
                    big_endian / 10,
                    3
                ),

            "big_div_100":
                round(
                    big_endian / 100,
                    3
                ),

            "big_div_1000":
                round(
                    big_endian / 1000,
                    3
                ),

            "little_div_10":
                round(
                    little_endian / 10,
                    3
                ),

            "little_div_100":
                round(
                    little_endian / 100,
                    3
                ),

            "little_div_1000":
                round(
                    little_endian / 1000,
                    3
                )

        })

    return candidates


# ============================================================
# FLOAT ANALYSIS
# ============================================================

def get_float_candidates(data):

    candidates = []

    for i in range(len(data) - 3):

        chunk = data[i:i + 4]

        hex_value = " ".join(
            f"{x:02X}"
            for x in chunk
        )

        # Big endian float
        try:

            big_float = struct.unpack(
                ">f",
                bytes(chunk)
            )[0]

        except Exception:

            big_float = None

        # Little endian float
        try:

            little_float = struct.unpack(
                "<f",
                bytes(chunk)
            )[0]

        except Exception:

            little_float = None

        candidates.append({

            "position":
                f"{i}-{i + 3}",

            "hex":
                hex_value,

            "big_endian_float":
                round(
                    big_float,
                    6
                )
                if big_float is not None
                else None,

            "little_endian_float":
                round(
                    little_float,
                    6
                )
                if little_float is not None
                else None

        })

    return candidates


# ============================================================
# EXACT PUC VALUE DECODER
# ============================================================

def decode_puc_values(data):

    """
    IMPORTANT:

    Exact CO / HC / CO2 / O2 mapping depends
    on the manufacturer's RS232 protocol.

    DO NOT assume byte positions without
    protocol documentation.

    Currently returns None until the protocol
    mapping is confirmed.
    """

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


# ============================================================
# MAIN DECODER
# ============================================================

def decode_puc_hex(raw_hex):

    decoded = {

        "raw_hex": None,

        "total_bytes": 0,

        "bytes": [],

        "ascii": "",

        "two_byte_candidates": [],

        "float_candidates": [],

        "bcd_candidates": [],

        "co": None,

        "hc": None,

        "co2": None,

        "o2": None,

        "result": None,

        "error": None

    }

    try:

        # ----------------------------------------------------
        # CLEAN HEX
        # ----------------------------------------------------

        clean_hex = clean_hex_string(
            raw_hex
        )

        decoded["raw_hex"] = clean_hex

        # ----------------------------------------------------
        # HEX -> BYTES
        # ----------------------------------------------------

        data = bytes.fromhex(
            clean_hex
        )

        decoded["total_bytes"] = len(data)

        # ----------------------------------------------------
        # BYTE LIST
        # ----------------------------------------------------

        decoded["bytes"] = format_bytes(
            data
        )

        # ----------------------------------------------------
        # ASCII
        # ----------------------------------------------------

        decoded["ascii"] = get_ascii(
            data
        )

        # ----------------------------------------------------
        # TWO BYTE
        # ----------------------------------------------------

        decoded["two_byte_candidates"] = \
            get_two_byte_candidates(
                data
            )

        # ----------------------------------------------------
        # FLOAT
        # ----------------------------------------------------

        decoded["float_candidates"] = \
            get_float_candidates(
                data
            )

        # ----------------------------------------------------
        # BCD
        # ----------------------------------------------------

        decoded["bcd_candidates"] = \
            get_bcd_candidates(
                data
            )

        # ----------------------------------------------------
        # PUC VALUES
        # ----------------------------------------------------

        values = decode_puc_values(
            data
        )

        decoded["co"] = values["co"]

        decoded["hc"] = values["hc"]

        decoded["co2"] = values["co2"]

        decoded["o2"] = values["o2"]

        decoded["result"] = values["result"]

        return decoded

    except ValueError as e:

        decoded["error"] = str(e)

        return decoded