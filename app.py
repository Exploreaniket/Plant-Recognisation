import os

from datetime import datetime, timedelta

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import google.generativeai as genai
from dotenv import load_dotenv
import json
from PIL import Image


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    MODEL_NAME = "models/gemini-2.0-flash"  # <-- replace with one from test output
    model = genai.GenerativeModel(MODEL_NAME)
    print("Using Gemini model:", MODEL_NAME)
else:
    model = None
    print("WARNING: GEMINI_API_KEY not set.")










# =======================
# CONFIG & FOLDERS
# =======================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
AVATAR_FOLDER = os.path.join(UPLOAD_FOLDER, "avatars")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AVATAR_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app = Flask(__name__)
app.config["SECRET_KEY"] = "replace-with-a-secure-random-string"  # CHANGE THIS
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///plantid.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
app.permanent_session_lifetime = timedelta(days=7)

db = SQLAlchemy(app)


# =======================
# MODELS
# =======================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar_url = db.Column(db.String(300), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    plants_identified = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Identification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    plant_name = db.Column(db.String(200), nullable=False)       # scientific
    common_name = db.Column(db.String(200), nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    care_light = db.Column(db.String(300), nullable=True)
    care_water = db.Column(db.String(300), nullable=True)
    care_soil = db.Column(db.String(300), nullable=True)
    care_notes = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="identifications")


# =======================
# HELPERS
# =======================

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return User.query.get(uid)


# =======================
# ROOT
# =======================

@app.route("/")
def index():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    return redirect(url_for("detect"))


# =======================
# AUTH ROUTES
# =======================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("register"))

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("An account with that email already exists. Please log in.", "warning")
            return redirect(url_for("login"))

        default_avatar = (
            "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e"
            "?w=100&h=100&fit=crop&crop=face"
        )

        user = User(
            name=name,
            email=email,
            avatar_url=default_avatar,
            bio=""
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

        session.permanent = True
        session["user_id"] = user.id
        flash(f"Welcome back, {user.name}!", "success")
        return redirect(url_for("detect"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# =======================
# PROFILE ROUTE
# =======================

@app.route("/profile", methods=["GET", "POST"])
def profile():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        bio = request.form.get("bio", "").strip()
        avatar_file = request.files.get("avatar_file")

        if not name:
            flash("Name cannot be empty.", "danger")
            return redirect(url_for("profile"))

        user.name = name
        user.bio = bio

        # If user selected a new profile picture
        if avatar_file and avatar_file.filename:
            filename = avatar_file.filename
            if not allowed_file(filename):
                flash("Profile picture must be an image (png, jpg, jpeg, gif).", "danger")
                return redirect(url_for("profile"))

            safe_name = secure_filename(filename)
            base, ext = os.path.splitext(safe_name)
            final_name = f"avatar_user{user.id}{ext.lower()}"
            save_path = os.path.join(AVATAR_FOLDER, final_name)

            avatar_file.save(save_path)

            # validate image
            try:
                img = Image.open(save_path)
                img.verify()
            except Exception:
                os.remove(save_path)
                flash("Invalid image file.", "danger")
                return redirect(url_for("profile"))

            user.avatar_url = url_for("uploaded_file", filename=f"avatars/{final_name}")

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile"))

    # last identifications for cards
    history = (
        Identification.query
        .filter_by(user_id=user.id)
        .order_by(Identification.created_at.desc())
        .limit(6)
        .all()
    )

    return render_template("profile.html", user=user, history=history)



@app.route("/profile/reset", methods=["POST"])
def reset_profile():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # Delete all Identification records by this user
    Identification.query.filter_by(user_id=user.id).delete()

    # Reset plant count
    user.plants_identified = 0

    db.session.commit()

    flash("Your profile statistics have been reset.", "info")
    return redirect(url_for("profile"))



# =======================
# DETECT PAGE (UPLOAD UI)
# =======================

@app.route("/detect")
def detect():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # only the most recent identification for sidebar
    latest = (
        Identification.query
        .filter_by(user_id=user.id)
        .order_by(Identification.created_at.desc())
        .first()
    )

    return render_template("detect.html", user=user, latest=latest)


# =======================
# UPLOAD IDENTIFICATION API
# =======================

@app.route("/upload", methods=["POST"])
def upload():
    """Handle plant image upload + AI identification."""
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401

    # ---------- 1. basic file checks ----------
    if "image" not in request.files:
        return jsonify({"ok": False, "error": "No file uploaded"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"ok": False, "error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"ok": False, "error": "File type not allowed"}), 400

    # ---------- 2. save file safely ----------
    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)

    base, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(save_path):
        filename = f"{base}_{counter}{ext}"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        counter += 1

    file.save(save_path)

    # validate that it's actually an image
    try:
        img_check = Image.open(save_path)
        img_check.verify()
    except Exception:
        os.remove(save_path)
        return jsonify({"ok": False, "error": "Invalid image file"}), 400

    # ---------- 3. default values (fallback) ----------
    plant_name = "Ficus elastica"
    common_name = "Rubber Plant"
    confidence = 0.94
    care_light = "Bright, indirect light."
    care_water = "Water when the top 2–3 cm of soil are dry."
    care_soil = "Well-draining potting mix."
    care_notes = "Demo result: AI model not available, showing sample plant data."

    # ---------- 4. Gemini AI call (best effort) ----------
    try:
        # only try if Gemini is configured
        if GEMINI_API_KEY and MODEL_NAME and model is not None:
            # read bytes again (for safety)
            with open(save_path, "rb") as f:
                image_bytes = f.read()

            # quick mime type from extension
            ext_lower = ext.lower()
            if ext_lower in [".jpg", ".jpeg"]:
                mime_type = "image/jpeg"
            elif ext_lower == ".png":
                mime_type = "image/png"
            elif ext_lower == ".gif":
                mime_type = "image/gif"
            else:
                mime_type = "image/jpeg"

            image_part = {
                "mime_type": mime_type,
                "data": image_bytes,
            }

            prompt = """
You are an expert botanist and plant doctor.

TASK:
Given this plant photo, you MUST:
1. Identify the plant (scientific + common name).
2. Estimate how confident you are (0–1).
3. Suggest basic care information.

RULES:
- ALWAYS give your BEST GUESS of the plant name.
- If you are unsure, still guess the closest likely plant and keep "confidence" <= 0.5.
- Respond STRICTLY as JSON with NO extra text.

Use EXACTLY this JSON schema:

{
  "plant_name": "Ficus elastica",
  "common_name": "Rubber Plant",
  "confidence": 0.94,
  "care_light": "Bright, indirect light.",
  "care_water": "Water when the top 2–3 cm of soil are dry.",
  "care_soil": "Well-draining potting mix.",
  "care_notes": "Short extra notes about care and disease risk."
}
"""

            # call Gemini – if the model name is wrong or not allowed,
            # this will raise, and we'll fall back to demo values above
            response = model.generate_content([prompt, image_part])
            raw_text = (response.text or "").strip()

            # strip ```json ... ``` if Gemini wraps the JSON
            if raw_text.startswith("```"):
                raw_text = raw_text.strip("`")
                if raw_text.lower().startswith("json"):
                    raw_text = raw_text[4:].strip()

            data = json.loads(raw_text)

            plant_name = data.get("plant_name", "").strip() or plant_name
            common_name = data.get("common_name", "").strip() or plant_name
            try:
                confidence = float(data.get("confidence", confidence) or confidence)
            except Exception:
                pass

            care_light = data.get("care_light", care_light) or care_light
            care_water = data.get("care_water", care_water) or care_water
            care_soil = data.get("care_soil", care_soil) or care_soil
            care_notes = data.get("care_notes", care_notes) or care_notes

    except Exception as e:
        # if Gemini fails (404, quota, etc.), just log and keep fallback values
        print("Gemini error (ignored, using demo data):", repr(e))

    # ---------- 5. save to DB ----------
    ident = Identification(
        user_id=user.id,
        filename=filename,
        plant_name=plant_name,
        common_name=common_name,
        confidence=confidence,
        care_light=care_light,
        care_water=care_water,
        care_soil=care_soil,
        care_notes=care_notes,
    )
    user.plants_identified += 1
    db.session.add(ident)
    db.session.commit()

    image_url = url_for("uploaded_file", filename=filename)

    # ---------- 6. respond to frontend ----------
    return jsonify({
        "ok": True,
        "identification": {
            "id": ident.id,
            "plant_name": plant_name,
            "common_name": common_name,
            "confidence": confidence,
            "care_light": care_light,
            "care_water": care_water,
            "care_soil": care_soil,
            "care_notes": care_notes,
            "image_url": image_url
        }
    })






# =======================
# STATIC UPLOADED FILES
# =======================

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# =======================
# CLI: INIT DB
# =======================

@app.cli.command("init-db")
def init_db():
    """Initialize the SQLite database."""
    db.create_all()
    print("Database initialized.")


# =======================
# MAIN
# =======================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
