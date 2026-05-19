from flask import Flask, render_template, request, redirect, url_for, session, abort
import psycopg2
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)

# SECRET_KEY session'ları imzalamak için şart. Env'den alınıyor.
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-degistir")

# Admin kullanıcı adı ve şifresi env'den geliyor
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")

def get_db():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "postgres-service"),
        database=os.environ.get("DB_NAME", "restorandb"),
        user=os.environ.get("DB_USER", "admin"),
        password=os.environ.get("DB_PASSWORD", "password123")
    )

def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS randevular (
                id SERIAL PRIMARY KEY,
                ad_soyad VARCHAR(100) NOT NULL,
                telefon VARCHAR(20) NOT NULL,
                tarih DATE NOT NULL,
                saat TIME NOT NULL,
                kisi_sayisi INTEGER NOT NULL,
                notlar TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB init error: {e}")

# --- Auth decorator ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# --- Login / Logout ---
@app.route("/admin/login", methods=["GET", "POST"])
def login():
    hata = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("admin"))
        else:
            hata = "Kullanıcı adı veya şifre hatalı."
    return render_template("login.html", hata=hata)

@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# --- Ana rotalar ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/randevu", methods=["GET", "POST"])
def randevu():
    if request.method == "POST":
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO randevular (ad_soyad, telefon, tarih, saat, kisi_sayisi, notlar)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                request.form["ad_soyad"],
                request.form["telefon"],
                request.form["tarih"],
                request.form["saat"],
                request.form["kisi_sayisi"],
                request.form.get("notlar", "")
            ))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for("basarili"))
        except Exception as e:
            return render_template("randevu.html", hata=str(e))
    return render_template("randevu.html")

@app.route("/basarili")
def basarili():
    return render_template("basarili.html")

@app.route("/admin")
@login_required
def admin():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM randevular ORDER BY tarih, saat")
        randevular = cur.fetchall()
        cur.close()
        conn.close()
        return render_template("admin.html", randevular=randevular)
    except Exception as e:
        return render_template("admin.html", randevular=[], hata=str(e))

@app.route("/health")
def health():
    return {"status": "ok"}, 200

with app.app_context():
    init_db()

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
