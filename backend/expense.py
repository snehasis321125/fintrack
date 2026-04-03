from flask import jsonify
from db import get_connection

def add_expense(data):
    conn = get_connection()
    c = conn.cursor()

    c.execute("INSERT INTO expenses(user_id,category,amount,date) VALUES(?,?,?,?)",
              (data['user_id'], data['category'], data['amount'], data['date']))

    conn.commit()
    conn.close()

    return jsonify({"message":"Expense added"})

def update_expense(data, expense_id):
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("UPDATE expenses SET category=?, amount=?, date=? WHERE id=?",
              (data['category'], data['amount'], data['date'], expense_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({"message":"Expense updated"})

def delete_expense(expense_id):
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({"message":"Expense deleted"})

def get_dashboard_data(user_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT category, SUM(amount) FROM expenses WHERE user_id=? GROUP BY category", (user_id,))
    categories = c.fetchall()

    c.execute("SELECT amount,date FROM expenses WHERE user_id=? ORDER BY date DESC LIMIT 7", (user_id,))
    last_week = c.fetchall()

    c.execute("SELECT SUM(amount) FROM expenses WHERE user_id=?", (user_id,))
    total = c.fetchone()[0] or 0

    conn.close()

    return jsonify({
        "total_spent": total,
        "categories": categories,
        "last_week": last_week
    })
