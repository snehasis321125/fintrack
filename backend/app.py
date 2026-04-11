from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

from auth import register_user, login_user, get_user_profile, update_user_profile, change_user_password
from db import get_connection, init_db
from expense import add_expense, update_expense, delete_expense
from model import predict_expenses, train_model_for_user

# ---------------- APP CONFIG ---------------- #

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

app.secret_key = "fintrack_secure_session_key"
CORS(app)


@app.route("/")
def home():

    if "admin" in session:
        return redirect(url_for("admin_dashboard"))

    if "user" in session:
        return redirect(url_for("dashboard_page"))

    return render_template("index.html")


@app.route("/dashboard")
def dashboard_page():

    if "user" not in session:
        return redirect(url_for("home"))

    profile_response = get_user_profile(session["user"])
    profile_data = profile_response.get_json() if profile_response else {}
    return render_template("dashboard.html", profile=profile_data)


@app.route("/profile")
def profile_page():

    if "user" not in session:
        return redirect(url_for("home"))

    from auth import get_user_profile
    profile_response = get_user_profile(session["user"])
    profile_data = profile_response.get_json() if profile_response else {}
    
    return render_template("profile.html", profile=profile_data)


@app.route("/admin")
def admin_page():

    if "admin" in session:
        return redirect(url_for("admin_dashboard"))

    return render_template("admin_login.html")


@app.route("/admin-dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect(url_for("admin_page"))

    return render_template("admin_dashboard.html")


# ---------------- AUTH ---------------- #

@app.route("/register", methods=["POST"])
def register():
    return register_user(request.json)


@app.route("/login", methods=["POST"])
def login():

    response = login_user(request.json)
    data = response.get_json()

    if data and data.get("user_id"):
        session.clear()
        session["user"] = data["user_id"]

    return response


@app.route("/admin-login", methods=["POST"])
def admin_login():

    data = request.json
    admin_id = data.get("admin_id")
    password = data.get("password")

    if admin_id == "smadmin25" and password == "SNEhasism@2505":

        session.clear()
        session["admin"] = True

        return jsonify({"status": "success"})

    return jsonify({"status": "fail"})


@app.route("/logout")
def logout():

    session.clear()

    return jsonify({"status": "logged_out"})


# ---------------- USER DASHBOARD DATA ---------------- #

@app.route("/dashboard-data")
def dashboard_data():

    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user"]

    conn = get_connection()
    c = conn.cursor()

    # total spent
    c.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ?", (user_id,))
    total_spent = c.fetchone()[0] or 0

    # today spent
    today = datetime.now().strftime("%Y-%m-%d")

    c.execute("""
        SELECT SUM(amount)
        FROM expenses
        WHERE user_id = ? AND date = ?
    """, (user_id, today))

    today_spent = c.fetchone()[0] or 0

    # monthly budget
    c.execute("SELECT monthly_budget FROM users WHERE id = ?", (user_id,))
    monthly_budget = c.fetchone()[0] or 0

    remaining_budget = monthly_budget - total_spent

    budget_percentage = (
        (total_spent / monthly_budget) * 100
        if monthly_budget else 0
    )

    # last 7 days data
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    # Recent transactions (all in last 7 days)
    c.execute("""
        SELECT id, amount, date, category
        FROM expenses
        WHERE user_id = ? AND date >= ?
        ORDER BY date DESC
    """, (user_id, seven_days_ago))
    recent_transactions = c.fetchall()

    # Categories spending last 7 days
    c.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id = ? AND date >= ?
        GROUP BY category
    """, (user_id, seven_days_ago))
    categories_7days = c.fetchall()

    # Daily sums for line chart (last 7 days)
    c.execute("""
        SELECT date, SUM(amount) as daily_total
        FROM expenses
        WHERE user_id = ? AND date >= ?
        GROUP BY date
        ORDER BY date ASC
    """, (user_id, seven_days_ago))
    daily_sums_7days = c.fetchall()

    c.execute("SELECT name FROM users WHERE id = ?", (user_id,))
    user_name = c.fetchone()[0] or "User"

    conn.close()

    return jsonify({
        "total_spent": total_spent,
        "today_spent": today_spent,
        "monthly_budget": monthly_budget,
        "remaining_budget": remaining_budget,
        "budget_percentage": round(budget_percentage, 2),
        "recent_transactions": recent_transactions,
        "categories_7days": categories_7days,
        "daily_sums_7days": daily_sums_7days,
        "user": {
            "id": user_id,
            "name": user_name
        }
    })


# ---------------- SET BUDGET ---------------- #

@app.route("/get-profile")
def get_profile():

    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    return get_user_profile(session["user"])


@app.route("/update-profile", methods=["POST"])
def update_profile():

    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    updates = request.json
    return update_user_profile(session["user"], updates)


@app.route("/change-password", methods=["POST"])
def change_password():

    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}
    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")

    if not old_password or not new_password:
        return jsonify({"error": "Both old and new password are required"}), 400

    return change_user_password(session["user"], old_password, new_password)


@app.route("/set-budget", methods=["POST"])
def set_budget():

    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    budget = request.json.get("budget")

    conn = get_connection()
    c = conn.cursor()

    c.execute(
        "UPDATE users SET monthly_budget = ? WHERE id = ?",
        (budget, session["user"])
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "updated"})


# ---------------- ADD EXPENSE ---------------- #

@app.route("/add-expense", methods=["POST"])
def add():

    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    data["user_id"] = session["user"]

    response = add_expense(data)

    # retrain model instantly
    train_model_for_user(session["user"])

    return response

# ---------------- UPDATE EXPENSE ---------------- #

@app.route("/update-expense/<int:expense_id>", methods=["PUT"])
def update_expense(expense_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    user_id = session["user"]

    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT user_id FROM expenses WHERE id = ?", (expense_id,))
    result = c.fetchone()
    if not result or result[0] != user_id:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    c.execute("""
        UPDATE expenses SET category = ?, amount = ?, date = ? 
        WHERE id = ?
    """, (data['category'], data['amount'], data['date'], expense_id))

    conn.commit()
    conn.close()

    # Retrain model
    train_model_for_user(user_id)

    return jsonify({"status": "updated"})

# ---------------- DELETE EXPENSE ---------------- #

@app.route("/delete-expense/<int:expense_id>", methods=["DELETE"])
def user_delete_expense(expense_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user"]

    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT user_id FROM expenses WHERE id = ?", (expense_id,))
    result = c.fetchone()
    if not result or result[0] != user_id:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))

    conn.commit()
    conn.close()

    # Retrain model
    train_model_for_user(user_id)

    return jsonify({"status": "deleted"})


# ---------------- ML PREDICTION ---------------- #

@app.route("/predict")
def predict():

    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    return predict_expenses(session["user"])


# ---------------- ADMIN APIs ---------------- #

@app.route("/admin/users")
def admin_users():

    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT id, name, email FROM users")

    users = c.fetchall()

    conn.close()

    return jsonify(users)


@app.route("/admin/expenses")
def admin_expenses():

    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT expenses.id, users.name, category, amount, date
        FROM expenses
        JOIN users ON expenses.user_id = users.id
    """)

    expenses = c.fetchall()

    conn.close()

    return jsonify(expenses)


@app.route("/admin/delete-user/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):

    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_connection()
    c = conn.cursor()

    c.execute("DELETE FROM users WHERE id = ?", (user_id,))

    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})


@app.route("/admin/delete-expense/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):

    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_connection()
    c = conn.cursor()

    c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))

    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})


# ---------------- DAILY MODEL RETRAIN ---------------- #

def retrain_all_models():

    print("Starting daily ML retraining...")

    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT id FROM users")
    users = c.fetchall()

    conn.close()

    for user in users:
        train_model_for_user(user[0])

    print("Daily ML retraining completed.")


# ---------------- MAIN ---------------- #

if __name__ == "__main__":

    print("Initializing DB...")
    init_db()
    print("Database ready.")

    print("Starting scheduler...")

    scheduler = BackgroundScheduler()
    scheduler.add_job(retrain_all_models, 'cron', hour=2)
    scheduler.start()

    print("Server starting...")

    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
