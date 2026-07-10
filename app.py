import sqlite3
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, g, session

app = Flask(__name__)
app.secret_key = "smart-pashu-mitra-secret-key"  # change before real deployment

# ---------------------------------------------------------------------------
# Veterinary Officer credentials  (change before real deployment)
# ---------------------------------------------------------------------------
VET_USERNAME = "vet_officer"
VET_PASSWORD = "pashumitra@2026"

DATABASE = "database/pashu_mitra.db"

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        with open("database/schema.sql") as f:
            db.executescript(f.read())
        db.commit()


def login_required(f):
    """Decorator: redirect to login page if vet officer is not logged in."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Rule-based health advisory data
# Symptom -> (possible causes, advice)
# ---------------------------------------------------------------------------
HEALTH_RULES = {
    "fever": {
        "causes": ["Infection", "Heat stress", "Early-stage disease"],
        "advice": "Keep the animal in shade with clean water. Monitor temperature. "
                   "Contact the veterinary officer if fever continues beyond a day.",
    },
    "cough": {
        "causes": ["Respiratory infection", "Dust irritation", "Early pneumonia"],
        "advice": "Keep the animal away from dusty or damp areas. "
                   "If coughing persists more than two days, consult the veterinary officer.",
    },
    "loss of appetite": {
        "causes": ["Digestive upset", "Fever", "Parasitic infection"],
        "advice": "Offer fresh water and soft fodder. Check for other symptoms like fever. "
                   "Persistent loss of appetite needs a veterinary check-up.",
    },
    "skin infection": {
        "causes": ["Fungal infection", "Parasites (ticks/mites)", "Wound infection"],
        "advice": "Keep the affected area clean and dry. Avoid contact with other animals. "
                   "Visit the veterinary officer for proper medication.",
    },
    "lameness": {
        "causes": ["Foot injury", "Hoof infection", "Joint strain"],
        "advice": "Rest the animal and inspect the hoof for wounds or foreign objects. "
                   "Report to the veterinary officer if swelling or limping continues.",
    },
    "reduced milk yield": {
        "causes": ["Poor nutrition", "Stress", "Early mastitis"],
        "advice": "Check udder for swelling or heat. Review feed quality and quantity. "
                   "Consult the veterinary officer if the drop is sudden or severe.",
    },
}

GOVERNMENT_SCHEMES = [
    {
        "name": "Livestock Insurance Scheme",
        "description": "Provides insurance cover for cattle, buffalo, and other livestock "
                        "against death due to disease, accident, or natural calamity.",
    },
    {
        "name": "National Livestock Mission",
        "description": "Supports entrepreneurship in poultry, sheep, goat, and piggery, "
                        "along with fodder development, through subsidies and training.",
    },
    {
        "name": "Dairy Entrepreneurship Development Scheme (DEDS)",
        "description": "Offers financial assistance for setting up small dairy farms, "
                        "milk processing units, and cold storage facilities.",
    },
    {
        "name": "Animal Husbandry Infrastructure Development Fund (AHIDF)",
        "description": "Incentivises investment in dairy, meat processing, and animal "
                        "feed plants through interest-subsidised loans.",
    },
    {
        "name": "Rashtriya Gokul Mission",
        "description": "Focuses on conservation and development of indigenous cattle "
                        "breeds and improving milk productivity.",
    },
]


# ---------------------------------------------------------------------------
# Routes: Login / Logout
# ---------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == VET_USERNAME and password == VET_PASSWORD:
            session["logged_in"] = True
            session["username"] = username
            flash("Welcome back, Veterinary Officer!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Routes: Farmer Dashboard (public — no login required)
# ---------------------------------------------------------------------------

@app.route("/farmer-portal", methods=["GET", "POST"])
def farmer_portal():
    db = get_db()
    search_query = request.form.get("search", "").strip() if request.method == "POST" else ""
    results = []
    if search_query:
        results = db.execute(
            """SELECT animals.*, farmers.name AS farmer_name, farmers.village, farmers.mobile
               FROM animals
               JOIN farmers ON animals.farmer_id = farmers.farmer_id
               WHERE animals.name LIKE ? OR farmers.name LIKE ? OR animals.breed LIKE ?
               ORDER BY animals.name""",
            (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"),
        ).fetchall()
        if not results:
            flash(f"No animals found matching '{search_query}'.", "error")

    return render_template(
        "farmer_portal.html",
        search_query=search_query,
        results=results,
        schemes=GOVERNMENT_SCHEMES,
    )


@app.route("/farmer-portal/animal/<int:animal_id>")
def farmer_animal_detail(animal_id):
    db = get_db()
    animal = db.execute(
        """SELECT animals.*, farmers.name AS farmer_name, farmers.village, farmers.mobile
           FROM animals
           JOIN farmers ON animals.farmer_id = farmers.farmer_id
           WHERE animals.animal_id = ?""",
        (animal_id,),
    ).fetchone()
    if not animal:
        flash("Animal not found.", "error")
        return redirect(url_for("farmer_portal"))
    today = date.today().isoformat()
    vacc_records = db.execute(
        """SELECT * FROM vaccinations WHERE animal_id = ? ORDER BY next_due_date ASC""",
        (animal_id,),
    ).fetchall()
    return render_template(
        "farmer_animal_detail.html",
        animal=animal,
        vacc_records=vacc_records,
        today=today,
        schemes=GOVERNMENT_SCHEMES,
    )


# ---------------------------------------------------------------------------
# Routes: Home, Dashboard
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    total_farmers = db.execute("SELECT COUNT(*) AS c FROM farmers").fetchone()["c"]
    total_animals = db.execute("SELECT COUNT(*) AS c FROM animals").fetchone()["c"]
    today = date.today().isoformat()
    vaccinations_due = db.execute(
        "SELECT COUNT(*) AS c FROM vaccinations WHERE next_due_date <= ?", (today,)
    ).fetchone()["c"]
    recent_queries = db.execute(
        "SELECT * FROM health_queries ORDER BY query_id DESC LIMIT 5"
    ).fetchall()
    return render_template(
        "dashboard.html",
        total_farmers=total_farmers,
        total_animals=total_animals,
        vaccinations_due=vaccinations_due,
        total_schemes=len(GOVERNMENT_SCHEMES),
        recent_queries=recent_queries,
    )


# ---------------------------------------------------------------------------
# Routes: Farmers
# ---------------------------------------------------------------------------

@app.route("/farmers")
@login_required
def farmers():
    db = get_db()
    all_farmers = db.execute(
        "SELECT * FROM farmers ORDER BY farmer_id DESC"
    ).fetchall()
    return render_template("farmers.html", farmers=all_farmers)


@app.route("/farmers/add", methods=["GET", "POST"])
@login_required
def add_farmer():
    if request.method == "POST":
        name = request.form["name"].strip()
        village = request.form["village"].strip()
        mobile = request.form["mobile"].strip()
        if not name or not village or not mobile:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("add_farmer"))
        db = get_db()
        db.execute(
            "INSERT INTO farmers (name, village, mobile) VALUES (?, ?, ?)",
            (name, village, mobile),
        )
        db.commit()
        flash(f"Farmer '{name}' registered successfully.", "success")
        return redirect(url_for("farmers"))
    return render_template("add_farmer.html")


@app.route("/farmers/delete/<int:farmer_id>", methods=["POST"])
@login_required
def delete_farmer(farmer_id):
    db = get_db()
    db.execute("DELETE FROM farmers WHERE farmer_id = ?", (farmer_id,))
    db.commit()
    flash("Farmer record removed.", "success")
    return redirect(url_for("farmers"))


# ---------------------------------------------------------------------------
# Routes: Animals
# ---------------------------------------------------------------------------

@app.route("/animals")
@login_required
def animals():
    db = get_db()
    all_animals = db.execute(
        """SELECT animals.*, farmers.name AS farmer_name
           FROM animals JOIN farmers ON animals.farmer_id = farmers.farmer_id
           ORDER BY animals.animal_id DESC"""
    ).fetchall()
    return render_template("animals.html", animals=all_animals)


@app.route("/animals/add", methods=["GET", "POST"])
@login_required
def add_animal():
    db = get_db()
    if request.method == "POST":
        farmer_id = request.form["farmer_id"]
        name = request.form["name"].strip()
        breed = request.form["breed"].strip()
        age = request.form["age"].strip()
        weight = request.form["weight"].strip()
        if not all([farmer_id, name, breed, age, weight]):
            flash("Please fill in all fields.", "error")
            return redirect(url_for("add_animal"))
        db.execute(
            "INSERT INTO animals (farmer_id, name, breed, age, weight) VALUES (?, ?, ?, ?, ?)",
            (farmer_id, name, breed, age, weight),
        )
        db.commit()
        flash(f"Animal '{name}' registered successfully.", "success")
        return redirect(url_for("animals"))
    all_farmers = db.execute("SELECT * FROM farmers ORDER BY name").fetchall()
    if not all_farmers:
        flash("Register a farmer first before adding an animal.", "error")
        return redirect(url_for("add_farmer"))
    return render_template("add_animal.html", farmers=all_farmers)


@app.route("/animals/delete/<int:animal_id>", methods=["POST"])
@login_required
def delete_animal(animal_id):
    db = get_db()
    db.execute("DELETE FROM animals WHERE animal_id = ?", (animal_id,))
    db.commit()
    flash("Animal record removed.", "success")
    return redirect(url_for("animals"))


# ---------------------------------------------------------------------------
# Routes: Vaccinations
# ---------------------------------------------------------------------------

@app.route("/vaccinations")
@login_required
def vaccinations():
    db = get_db()
    all_vaccinations = db.execute(
        """SELECT vaccinations.*, animals.name AS animal_name, farmers.name AS farmer_name
           FROM vaccinations
           JOIN animals ON vaccinations.animal_id = animals.animal_id
           JOIN farmers ON animals.farmer_id = farmers.farmer_id
           ORDER BY vaccinations.next_due_date ASC"""
    ).fetchall()
    today = date.today().isoformat()
    return render_template("vaccinations.html", vaccinations=all_vaccinations, today=today)


@app.route("/vaccinations/add", methods=["GET", "POST"])
@login_required
def add_vaccination():
    db = get_db()
    if request.method == "POST":
        animal_id = request.form["animal_id"]
        vaccine_name = request.form["vaccine_name"].strip()
        last_date = request.form.get("last_date", "").strip()
        next_due_date = request.form["next_due_date"].strip()
        if not all([animal_id, vaccine_name, next_due_date]):
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("add_vaccination"))
        db.execute(
            """INSERT INTO vaccinations (animal_id, vaccine_name, last_date, next_due_date)
               VALUES (?, ?, ?, ?)""",
            (animal_id, vaccine_name, last_date or None, next_due_date),
        )
        db.commit()
        flash(f"Vaccination record for '{vaccine_name}' added.", "success")
        return redirect(url_for("vaccinations"))
    all_animals = db.execute(
        """SELECT animals.animal_id, animals.name, farmers.name AS farmer_name
           FROM animals JOIN farmers ON animals.farmer_id = farmers.farmer_id
           ORDER BY animals.name"""
    ).fetchall()
    if not all_animals:
        flash("Register an animal first before adding a vaccination record.", "error")
        return redirect(url_for("add_animal"))
    return render_template("add_vaccination.html", animals=all_animals)


@app.route("/vaccinations/delete/<int:vaccination_id>", methods=["POST"])
@login_required
def delete_vaccination(vaccination_id):
    db = get_db()
    db.execute("DELETE FROM vaccinations WHERE vaccination_id = ?", (vaccination_id,))
    db.commit()
    flash("Vaccination record removed.", "success")
    return redirect(url_for("vaccinations"))


# ---------------------------------------------------------------------------
# Routes: Health Advisory
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET", "POST"])
@login_required
def health():
    db = get_db()
    result = None
    if request.method == "POST":
        symptom_key = request.form["symptom"]
        animal_id = request.form.get("animal_id") or None
        rule = HEALTH_RULES.get(symptom_key)
        if rule:
            result = {
                "symptom": symptom_key.title(),
                "causes": rule["causes"],
                "advice": rule["advice"],
            }
            db.execute(
                "INSERT INTO health_queries (animal_id, symptom, advice) VALUES (?, ?, ?)",
                (animal_id, symptom_key.title(), rule["advice"]),
            )
            db.commit()
    all_animals = db.execute(
        """SELECT animals.animal_id, animals.name, farmers.name AS farmer_name
           FROM animals JOIN farmers ON animals.farmer_id = farmers.farmer_id
           ORDER BY animals.name"""
    ).fetchall()
    history = db.execute(
        "SELECT * FROM health_queries ORDER BY query_id DESC LIMIT 10"
    ).fetchall()
    return render_template(
        "health.html",
        symptoms=HEALTH_RULES.keys(),
        animals=all_animals,
        result=result,
        history=history,
    )


# ---------------------------------------------------------------------------
# Routes: Government Schemes
# ---------------------------------------------------------------------------

@app.route("/schemes")
def schemes():
    return render_template("schemes.html", schemes=GOVERNMENT_SCHEMES)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    if not os.path.exists(DATABASE):
        init_db()
        print("Database initialised.")
    app.run(debug=True)
