from flask import Flask, request, jsonify, render_template, Response, send_file
from component.motor_control import RobotMotors
import time
import json
import queue
import threading
import board
import busio
import adafruit_bme280.basic as adafruit_bme280
import adafruit_veml7700
import os
import csv

app = Flask(__name__)
motors = RobotMotors()

# ===== CONFIG CAPTEURS =====
SENSOR_REFRESH_SEC = 5.0
MAX_ROWS_API = 500

# --- BME280 ---
i2c = busio.I2C(board.SCL, board.SDA)
bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
veml = adafruit_veml7700.VEML7700(i2c)

CSV_FILE = "donnees_robot.csv"
CSV_LOCK = threading.Lock()

CSV_HEADERS = [
    "ts",
    "date_time",
    "temperature_c",
    "humidity_pct",
    "pressure_hpa",
    "lux"
]

def reset_csv():
    """Vide le CSV au démarrage et réécrit l'en-tête."""
    with CSV_LOCK:
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)

def append_csv_row(row: dict):
    """Ajoute une ligne au CSV (row = dict avec les clés de CSV_HEADERS)."""
    with CSV_LOCK:
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([row.get(h) for h in CSV_HEADERS])


# --- état live (ce qu’on affiche sur le site) ---

LIVE = {
    "action": "stop",
    "speed": getattr(motors, "speed", None),

    "temperature": None,
    "humidity": None,
    "pressure": None,
    "lux": None,

    "ts": time.time(),
}

# --- file d'événements SSE ---
EVENTS = queue.Queue(maxsize=200)

def push_event(payload: dict):
    """Envoie un event aux clients SSE (sans bloquer si overflow)."""
    payload = dict(payload)
    payload["ts"] = time.time()
    try:
        EVENTS.put_nowait(payload)
    except queue.Full:
        # On jette l'event si trop d'évènements (pas grave)
        pass

@app.route("/data.json")
def data_json():
    if not os.path.exists(CSV_FILE):
        return jsonify({
            "ok": False,
            "error": "CSV introuvable",
            "headers": [],
            "rows": [],
            "refresh_sec": SENSOR_REFRESH_SEC
        }), 200

    with CSV_LOCK:
        with open(CSV_FILE, "r", newline="") as f:
            reader = csv.reader(f)
            all_rows = list(reader)

    if not all_rows:
        return jsonify({
            "ok": True,
            "headers": [],
            "rows": [],
            "refresh_sec": SENSOR_REFRESH_SEC
        })

    headers = all_rows[0]
    rows = all_rows[1:]

    # On ne renvoie que les dernières lignes pour éviter de charger le navigateur
    if len(rows) > MAX_ROWS_API:
        rows = rows[-MAX_ROWS_API:]

    return jsonify({
        "ok": True,
        "headers": headers,
        "rows": rows,
        "refresh_sec": SENSOR_REFRESH_SEC
    })


@app.route("/data")
def data_page():
    return render_template("data.html")


@app.route("/download-csv")
def download_csv():
    if not os.path.exists(CSV_FILE):
        return jsonify({"ok": False, "error": "CSV introuvable"}), 404
    # lock pour éviter lecture pendant écriture
    with CSV_LOCK:
        return send_file(CSV_FILE, as_attachment=True)

@app.route("/graph")
def graph_page():
    return render_template("graph.html")


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/events")
def events():
    def gen():
        # état initial
        yield f"data: {json.dumps(LIVE)}\n\n"
        last_ping = time.time()

        while True:
            # ping toutes les 15s si rien ne se passe
            now = time.time()
            if now - last_ping > 15:
                yield "data: {}\n\n"
                last_ping = now

            try:
                data = EVENTS.get(timeout=1)
                yield f"data: {json.dumps(data)}\n\n"
            except queue.Empty:
                pass

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return Response(gen(), headers=headers)

@app.before_request
def _update_last_cmd():
    # si tu utilises LAST_CMD_TS ailleurs, garde-le
    global LAST_CMD_TS
    LAST_CMD_TS = time.time()

@app.route("/move", methods=["POST"])
def move():
    data = request.get_json(force=True) or {}
    action = data.get("action", "stop")
    speed = data.get("speed", None)

    # update speed si fourni
    if speed is not None:
        try:
            motors.set_speed(float(speed))
        except ValueError:
            pass

    # action moteurs
    if action == "forward":
        motors.forward()
    elif action == "backward":
        motors.backward()
    elif action == "left":
        motors.left_turn()
    elif action == "right":
        motors.right_turn()
    else:
        motors.stop()
        action = "stop"

    # met à jour LIVE + push event
    LIVE["action"] = action
    LIVE["speed"] = getattr(motors, "speed", speed)
    LIVE["ts"] = time.time()

    push_event({"action": LIVE["action"], "speed": LIVE["speed"]})

    return jsonify({"ok": True, "action": action, "speed": LIVE["speed"]})

@app.route("/stop", methods=["POST"])
def stop():
    motors.stop()
    LIVE["action"] = "stop"
    LIVE["speed"] = getattr(motors, "speed", LIVE.get("speed"))
    LIVE["ts"] = time.time()

    push_event({"action": "stop", "speed": LIVE["speed"]})
    return jsonify({"ok": True})

def bme_loop():
    while True:
        try:
            ts = time.time()
            payload = {
                "temperature": round(bme.temperature, 2),
                "humidity": round(bme.humidity, 2),
                "pressure": round(bme.pressure, 2),
                "lux": round(veml.lux, 2),
            }

            LIVE.update(payload)
            push_event(payload)

            append_csv_row({
                "ts": ts,
                "date_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)),
                "temperature_c": payload["temperature"],
                "humidity_pct": payload["humidity"],
                "pressure_hpa": payload["pressure"],
                "lux": payload["lux"],
            })

        except Exception as e:
            push_event({"sensor_error": str(e)})

        time.sleep(SENSOR_REFRESH_SEC)



if __name__ == "__main__":
    reset_csv()
    threading.Thread(target=bme_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
