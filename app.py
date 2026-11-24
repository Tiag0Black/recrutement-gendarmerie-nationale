import os
import sqlite3
from functools import wraps
from pathlib import Path
from flask import Flask, request, redirect, url_for, render_template, flash, session, abort
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "applications.sqlite3"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
if not app.config["SECRET_KEY"]:
    raise RuntimeError("Définissez SECRET_KEY dans les variables d'environnement.")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
)
csrf = CSRFProtect(app)

FIELDS = [
    ("name", "Nom et prénom RP"), ("discord", "Pseudo Discord"),
    ("age", "Âge du personnage"), ("grade", "Grade actuel"),
    ("experience", "Expérience RP"), ("availability", "Disponibilités"),
    ("playtime", "Temps de jeu hebdomadaire"), ("corps", "Corps souhaité"),
    ("specialty", "Spécialité souhaitée"), ("second", "Deuxième choix"),
    ("whyUnit", "Pourquoi cette affectation ?"), ("presentation", "Présentation"),
    ("motivation", "Motivations"), ("qualities", "Qualités"),
    ("improve", "Point à améliorer"), ("conflict", "Gestion d'un désaccord"),
    ("teamwork", "Travail en équipe"), ("rules", "Connaissance du règlement"),
    ("past", "Expérience antérieure"), ("extra", "Informations complémentaires"),
]
REQUIRED = {
    "name", "discord", "age", "grade", "experience", "availability",
    "corps", "specialty", "whyUnit", "presentation", "motivation",
    "qualities", "improve", "conflict", "teamwork", "rules"
}

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            status TEXT NOT NULL DEFAULT 'pending',
            data TEXT NOT NULL
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )""")
        username = os.environ.get("ADMIN_USERNAME")
        password = os.environ.get("ADMIN_PASSWORD")
        if username and password:
            existing = con.execute("SELECT id FROM admins WHERE username=?", (username,)).fetchone()
            if not existing:
                con.execute("INSERT INTO admins(username,password_hash) VALUES(?,?)",
                            (username, generate_password_hash(password)))
        elif con.execute("SELECT COUNT(*) FROM admins").fetchone()[0] == 0:
            print("ATTENTION : définissez ADMIN_USERNAME et ADMIN_PASSWORD avant de vous connecter.")

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapped

@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/")
def index():
    return render_template("index.html", fields=FIELDS)

@app.post("/submit")
def submit():
    data = {key: request.form.get(key, "").strip()[:5000] for key, _ in FIELDS}
    missing = [label for key, label in FIELDS if key in REQUIRED and not data[key]]
    if missing:
        flash("Merci de compléter les champs obligatoires : " + ", ".join(missing), "error")
        return redirect(url_for("index") + "#form")
    try:
        age = int(data["age"])
        if age < 18 or age > 99:
            raise ValueError()
    except ValueError:
        flash("L'âge du personnage doit être un nombre compris entre 18 et 99.", "error")
        return redirect(url_for("index") + "#form")
    import json
    with db() as con:
        con.execute("INSERT INTO applications(data) VALUES(?)", (json.dumps(data, ensure_ascii=False),))
    flash("Candidature envoyée. Votre dossier est en attente d'examen.", "success")
    return redirect(url_for("index"))

@app.route("/recrutement/connexion", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with db() as con:
            admin = con.execute("SELECT * FROM admins WHERE username=?", (username,)).fetchone()
        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["username"]
            return redirect(url_for("dashboard"))
        flash("Identifiant ou mot de passe incorrect.", "error")
    return render_template("login.html")

@app.get("/recrutement")
@admin_required
def dashboard():
    import json
    with db() as con:
        rows = con.execute("SELECT * FROM applications ORDER BY id DESC").fetchall()
    applications = []
    for row in rows:
        item = dict(row)
        item["data"] = json.loads(item["data"])
        applications.append(item)
    counts = {s: sum(1 for a in applications if a["status"] == s)
              for s in ("pending", "accepted", "refused")}
    return render_template("dashboard.html", applications=applications, counts=counts, fields=FIELDS)

@app.post("/recrutement/dossier/<int:app_id>/decision")
@admin_required
def decision(app_id):
    status = request.form.get("status")
    if status not in {"pending", "accepted", "refused"}:
        abort(400)
    with db() as con:
        cur = con.execute("UPDATE applications SET status=? WHERE id=?", (status, app_id))
        if cur.rowcount == 0:
            abort(404)
    flash("Décision enregistrée.", "success")
    return redirect(url_for("dashboard"))

@app.post("/recrutement/dossier/<int:app_id>/supprimer")
@admin_required
def delete_application(app_id):
    with db() as con:
        con.execute("DELETE FROM applications WHERE id=?", (app_id,))
    flash("Dossier supprimé.", "success")
    return redirect(url_for("dashboard"))

@app.post("/recrutement/deconnexion")
@admin_required
def logout():
    session.clear()
    return redirect(url_for("index"))

init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
