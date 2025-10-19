import os
import io
import base64
import pickle
import datetime
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from functools import wraps
import numpy as np
from PIL import Image
import face_recognition
import csv

APP_ROOT = Path(__file__).parent
DATASET_DIR = APP_ROOT / "dataset"
ENCODINGS_FILE = APP_ROOT / "encodings.pkl"
DB_PATH = APP_ROOT / "database.db"

os.makedirs(DATASET_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = "ba1cb5b7549aa91f55df23563edd0df5"

# --- DB helpers --------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll TEXT,
            email TEXT
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()

init_db()

# --- Admin default -----------------------------------------------------------
def ensure_admin_exists():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM admins")
    if cur.fetchone()["c"] == 0:
        cur.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ("admin", "adminpass"))
        conn.commit()
    conn.close()

ensure_admin_exists()

# --- Encoding utilities ------------------------------------------------------
def build_encodings():
    known = {"meta": {}, "encodings": {}}
    for user_dir in DATASET_DIR.iterdir():
        if not user_dir.is_dir():
            continue
        try:
            user_id = int(user_dir.name)
        except ValueError:
            continue
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT name FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            continue
        known["meta"][str(user_id)] = row["name"]
        encs = []
        for img_path in user_dir.glob("*"):
            try:
                img = face_recognition.load_image_file(str(img_path))
                faces = face_recognition.face_encodings(img)
                if faces:
                    encs.append(faces[0])
            except Exception as e:
                print("skip", img_path, e)
        if encs:
            known["encodings"][str(user_id)] = encs
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(known, f)
    return known

def load_encodings():
    if not ENCODINGS_FILE.exists():
        return build_encodings()
    with open(ENCODINGS_FILE, "rb") as f:
        return pickle.load(f)

# --- Admin decorator ---------------------------------------------------------
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not request.cookies.get("admin"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

# --- Password hashing placeholder -------------------------------------------
def hash_password(pwd):
    # Replace with actual hashing (bcrypt, werkzeug.security, etc.)
    return pwd

# --- Routes -----------------------------------------------------------------
@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    conn = get_db()
    cur = conn.cursor()
    
    # Check if there are any admins
    cur.execute("SELECT COUNT(*) as c FROM admins")
    admin_count = cur.fetchone()["c"]
    conn.close()
    
    # If no admins exist, redirect to add first admin page
    if admin_count == 0:
        flash("No admin accounts found. Please create the first admin.")
        return redirect(url_for("add_first_admin"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM admins WHERE username=? AND password=?", (username, password))
        admin = cur.fetchone()
        conn.close()
        if admin:
            resp = redirect(url_for("dashboard"))
            resp.set_cookie("admin", username)
            return resp
        flash("Invalid credentials")
    
    return render_template("login.html")


@app.route("/dashboard")
@admin_required
def dashboard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY id")
    users = cur.fetchall()
    today = datetime.date.today().isoformat()
    cur.execute("SELECT * FROM attendance WHERE date=?", (today,))
    rows = {r["user_id"]: r for r in cur.fetchall()}
    conn.close()
    return render_template("dashboard.html", users=users, rows=rows, current_year=datetime.date.today().year)

# --- Users CRUD --------------------------------------------------------------
@app.route("/users")
@admin_required
def users():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return render_template("users.html", users=rows)

@app.route("/users/add", methods=["GET", "POST"])
@admin_required
def add_user():
    if request.method == "POST":
        name = request.form["name"]
        roll = request.form.get("roll")
        email = request.form.get("email")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name, roll, email) VALUES (?, ?, ?)", (name, roll, email))
        user_id = cur.lastrowid
        conn.commit()
        conn.close()

        user_dir = DATASET_DIR / str(user_id)
        os.makedirs(user_dir, exist_ok=True)

        images = request.form.getlist("images[]")
        for i, b64 in enumerate(images):
            if not b64:
                continue
            header, data = b64.split(",", 1)
            imgdata = base64.b64decode(data)
            fname = user_dir / f"{i}.jpg"
            with open(fname, "wb") as f:
                f.write(imgdata)

        build_encodings()
        flash("User created and images saved.")
        return redirect(url_for("users"))
    return render_template("add_user.html")

@app.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        name = request.form["name"]
        roll = request.form.get("roll")
        email = request.form.get("email")
        cur.execute("UPDATE users SET name=?, roll=?, email=? WHERE id=?", (name, roll, email, user_id))
        conn.commit()
        conn.close()
        flash("Updated.")
        return redirect(url_for("users"))

    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cur.fetchone()
    conn.close()
    return render_template("add_user.html", user=user, edit=True)

@app.route("/users/delete/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    user_dir = DATASET_DIR / str(user_id)
    if user_dir.exists():
        for f in user_dir.glob("*"):
            try: f.unlink()
            except Exception: pass
        try: user_dir.rmdir()
        except Exception: pass

    build_encodings()
    flash("User deleted.")
    return redirect(url_for("users"))
@app.route("/add_first_admin", methods=["GET", "POST"])
def add_first_admin():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM admins")
    if cur.fetchone()["c"] > 0:
        conn.close()
        flash("Admin already exists. Please login.")
        return redirect(url_for("login"))
    conn.close()
    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if not username or not password:
            flash("Both username and password are required")
            return redirect(url_for("add_first_admin"))
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO admins (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        flash(f"Admin '{username}' created successfully. Please login.")
        return redirect(url_for("login"))

    return render_template("add_first_admin.html")

# --- Recognition -------------------------------------------------------------
@app.route("/recognize", methods=["POST"])
@admin_required
def recognize():
    payload = request.get_json()
    if not payload or "image" not in payload:
        return jsonify({"error": "no image"}), 400

    b64 = payload["image"].split(",", 1)[1]
    img_bytes = base64.b64decode(b64)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    frame = np.array(img)

    known = load_encodings()
    encs_map = known.get("encodings", {})
    meta = known.get("meta", {})

    faces = face_recognition.face_locations(frame)
    face_encs = face_recognition.face_encodings(frame, faces)

    if not face_encs:
        return jsonify({"recognized": False})

    for fe in face_encs:
        for user_id, enc_list in encs_map.items():
            matches = face_recognition.compare_faces(enc_list, fe, tolerance=0.5)
            if True in matches:
                uid = int(user_id)
                today = datetime.date.today().isoformat()
                conn = get_db()
                cur = conn.cursor()
                cur.execute("SELECT * FROM attendance WHERE user_id=? AND date=?", (uid, today))
                if not cur.fetchone():
                    cur.execute(
                        "INSERT INTO attendance (user_id, date, status, timestamp) VALUES (?, ?, ?, ?)",
                        (uid, today, "present", datetime.datetime.now().isoformat())
                    )
                # fetch roll number for table update
                cur.execute("SELECT roll FROM users WHERE id=?", (uid,))
                roll_row = cur.fetchone()
                conn.commit()
                conn.close()
                roll = roll_row["roll"] if roll_row else "-"
                return jsonify({"recognized": True, "user_id": uid, "name": meta.get(user_id), "roll": roll})

    return jsonify({"recognized": False})

# --- Attendance view & export -----------------------------------------------
@app.route("/attendance")
@admin_required
def attendance_view():
    date_q = request.args.get("date", datetime.date.today().isoformat())
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY id")
    users = cur.fetchall()
    cur.execute("SELECT * FROM attendance WHERE date=?", (date_q,))
    rows = {r["user_id"]: r for r in cur.fetchall()}
    conn.close()
    return render_template("attendance_view.html", users=users, rows=rows, date=date_q)

@app.route("/attendance/export")
@admin_required
def attendance_export():
    date_q = request.args.get("date", datetime.date.today().isoformat())
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, roll FROM users ORDER BY id")
    users = cur.fetchall()
    cur.execute("SELECT user_id, status FROM attendance WHERE date=?", (date_q,))
    present = {r["user_id"]: r["status"] for r in cur.fetchall()}
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["user_id", "name", "roll", "status", "date"])
    for u in users:
        status = present.get(u[0], "absent")
        writer.writerow([u[0], u[1], u[2], status, date_q])
    output.seek(0)
    return send_file(io.BytesIO(output.read().encode()), mimetype="text/csv",
                     as_attachment=True, download_name=f"attendance_{date_q}.csv")

# --- Admin management --------------------------------------------------------
@app.route("/admins")
@admin_required
def admins():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM admins ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return render_template("admins.html", admins=rows)

@app.route("/admins/add", methods=["GET", "POST"])
def add_admin():
    # Check if any admins exist
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM admins")
    admin_count = cur.fetchone()["c"]
    conn.close()

    # If admins exist, require login
    if admin_count > 0 and not request.cookies.get("admin"):
        flash("Please login as admin to add new admins")
        return redirect(url_for("login"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if not username or not password:
            flash("Both username and password are required")
            return redirect(url_for("add_admin"))

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO admins (username, password) VALUES (?, ?)", (username, hash_password(password)))
            conn.commit()
            flash(f"Admin '{username}' added successfully.")
        except sqlite3.IntegrityError:
            flash(f"Username '{username}' already exists.")
        finally:
            conn.close()
        return redirect(url_for("admins"))

    return render_template("add_admin.html")


@app.route("/admins/delete/<int:admin_id>", methods=["POST"])
@admin_required
def delete_admin(admin_id):
    current_admin = request.cookies.get("admin")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username FROM admins WHERE id=?", (admin_id,))
    row = cur.fetchone()
    if row and row["username"] == current_admin:
        flash("You cannot delete your own account while logged in.")
    else:
        cur.execute("DELETE FROM admins WHERE id=?", (admin_id,))
        conn.commit()
        flash("Admin deleted successfully.")
    conn.close()
    return redirect(url_for("admins"))

# --- Logout ------------------------------------------------------------
@app.route("/logout")
def logout():
    resp = redirect(url_for("login"))
    resp.delete_cookie("admin")
    return resp

if __name__ == "__main__":
    app.run(debug=True, port=5000)
