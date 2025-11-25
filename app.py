# -----------------------------
# CAR CONTACT SYSTEM (FINAL)
# -----------------------------
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import sqlite3, qrcode, json, time, base64
from Crypto.Cipher import AES
import os

app = Flask(__name__)

# AES 32-byte key
AES_KEY = b'12345678901234567890123456789012'
TOKEN_EXPIRY = 86400  # 24 hours
ADMIN_USERNAME = "iamrohit10"
ADMIN_PASSWORD = "iamrohit10"
DB_FILE = "cars.db"
RATE_LIMIT = {}
ATTEMPT_LIMIT = 5
BLOCK_TIME = 3600  # 1 hour

# -----------------------------
# AES Helper Functions
# -----------------------------
def pad(s):
    return s + (AES.block_size - len(s) % AES.block_size) * chr(AES.block_size - len(s) % AES.block_size)

def unpad(s):
    return s[:-ord(s[-1])]

def encrypt(text):
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    return base64.urlsafe_b64encode(cipher.encrypt(pad(text).encode())).decode()

def decrypt(enc):
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    return unpad(cipher.decrypt(base64.urlsafe_b64decode(enc)).decode())

# -----------------------------
# Database Helper
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cars
                 (car_id TEXT PRIMARY KEY, nickname TEXT, last4 TEXT, owner_name TEXT, owner_phone TEXT)''')
    # Preload cars
    c.execute("INSERT OR REPLACE INTO cars VALUES ('car1','Brezza','8321','ROHIT SENMA','8511758308')")
    c.execute("INSERT OR REPLACE INTO cars VALUES ('car2','Dzire','3932','ROHIT SENMA','8511758308')")
    conn.commit()
    conn.close()

def get_car(car_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM cars WHERE car_id=?", (car_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"car_id": row[0], "nickname": row[1], "last4": row[2], "owner_name": row[3], "owner_phone": row[4]}
    return None

def get_all_cars():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM cars")
    rows = c.fetchall()
    conn.close()
    cars = []
    for row in rows:
        cars.append({"car_id": row[0], "nickname": row[1], "last4": row[2], "owner_name": row[3], "owner_phone": row[4]})
    return cars

# -----------------------------
# Rate Limiting
# -----------------------------
def rate_limited(ip):
    rec = RATE_LIMIT.get(ip, {"count":0,"time":time.time(),"blocked":False})
    if rec["blocked"] and time.time() - rec["time"] < BLOCK_TIME:
        return True
    if time.time() - rec["time"] > BLOCK_TIME:
        RATE_LIMIT[ip] = {"count":0,"time":time.time(),"blocked":False}
        return False
    return rec["blocked"]

def add_attempt(ip):
    rec = RATE_LIMIT.setdefault(ip, {"count":0,"time":time.time(),"blocked":False})
    rec["count"] +=1
    if rec["count"] >= ATTEMPT_LIMIT:
        rec["blocked"]=True

# -----------------------------
# Token Functions
# -----------------------------
def create_token(car_id):
    data = {"car":car_id,"ts":int(time.time())}
    return encrypt(json.dumps(data))

def validate_token(token):
    try:
        decoded = json.loads(decrypt(token))
    except:
        return None
    if time.time() - decoded["ts"] > TOKEN_EXPIRY:
        return None
    return decoded

# -----------------------------
# QR Generation
# -----------------------------
@app.route("/qr/<car_id>")
def qr(car_id):
    car = get_car(car_id)
    if not car:
        return "Car not found."
    token = create_token(car_id)
    url = f"{request.url_root}contact?token={token}"
    img = qrcode.make(url)
    filename = f"qr_{car_id}.png"
    img.save(filename)
    return send_file(filename, mimetype="image/png")

# -----------------------------
# Contact Page
# -----------------------------
@app.route("/contact")
def contact():
    token = request.args.get("token")
    decoded = validate_token(token)
    if not decoded:
        return "<h2>Invalid or expired QR.</h2>"
    return render_template("contact.html", token=token)

# -----------------------------
# Verify Digits
# -----------------------------
@app.route("/verify", methods=["POST"])
def verify():
    ip = request.remote_addr
    if rate_limited(ip):
        return jsonify({"success":False,"msg":"Too many attempts, try later."})
    data = request.json
    token = data["token"]
    digits = data["digits"]
    decoded = validate_token(token)
    if not decoded:
        return jsonify({"success":False,"msg":"Invalid or expired token."})
    car = get_car(decoded["car"])
    if digits != car["last4"]:
        add_attempt(ip)
        return jsonify({"success":False,"msg":"Incorrect digits."})
    return jsonify({"success":True,"redirect":f"/owner?token={token}"})

# -----------------------------
# Owner Info
# -----------------------------
@app.route("/owner")
def owner():
    token = request.args.get("token")
    decoded = validate_token(token)
    if not decoded:
        return "Invalid or expired token."
    car = get_car(decoded["car"])
    return render_template("owner.html", car=car)

# -----------------------------
# Admin
# -----------------------------
@app.route("/admin")
def admin():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Unauthorized."
    cars = get_all_cars()
    return render_template("admin.html", cars=cars)

# -----------------------------
# App Start
# -----------------------------
# if __name__=="__main__":
#     init_db()
#     print("App started. Visit /qr/car1 or /qr/car2 to generate QR codes.")
#     app.run(host="0.0.0.0", port=5000, debug=True) 
#App Ends
            
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"
    app.run(host=host, port=port)
