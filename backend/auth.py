from flask import jsonify
from db import get_connection

def register_user(data):
    conn = get_connection()
    c = conn.cursor()

    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    name = f"{first_name} {last_name}".strip() or first_name
    email = data['email']
    password = data['password']

    c.execute("""INSERT INTO users 
                 (name, first_name, last_name, email, password) 
                 VALUES (?, ?, ?, ?, ?)""",
              (name, first_name, last_name, email, password))
    conn.commit()
    conn.close()

    return jsonify({"message":"User Registered"})

def login_user(data):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT id FROM users WHERE email=? AND password=?",
              (data['email'], data['password']))

    user = c.fetchone()
    conn.close()

    if user:
        return jsonify({"user_id":user[0]})
    return jsonify({"error":"Invalid credentials"})


def get_user_profile(user_id):
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
        SELECT name, first_name, last_name, email, phone, birthday, bio, 
               country, city, postal_code, tax_id, language, date_format, 
               currency, timezone, COALESCE(profile_photo, '') as profile_photo
        FROM users WHERE id = ?
    """, (user_id,))
    profile = c.fetchone()
    conn.close()
    
    if profile:
        profile_data = dict(zip([
            'name', 'first_name', 'last_name', 'email', 'phone', 'birthday', 'bio',
            'country', 'city', 'postal_code', 'tax_id', 'language', 'date_format',
            'currency', 'timezone', 'profile_photo'
        ], profile))
        full_name = " ".join(
            part for part in [profile_data.get("first_name"), profile_data.get("last_name")] if part
        ).strip()
        profile_data["name"] = full_name or profile_data.get("name") or "User"
        return jsonify(profile_data)
    return jsonify({"error": "User not found"}), 404


def update_user_profile(user_id, updates):
    conn = get_connection()
    c = conn.cursor()
    
    fields = []
    values = []
    
    editable_fields = [
        'name', 'first_name', 'last_name', 'email', 'phone', 'birthday', 'bio',
        'country', 'city', 'postal_code', 'tax_id', 'language', 'date_format',
        'currency', 'timezone', 'profile_photo'
    ]
    
    for field in editable_fields:
        if field in updates:
            fields.append(f"{field} = ?")
            values.append(updates[field])

    next_first_name = updates.get("first_name")
    next_last_name = updates.get("last_name")
    next_name = updates.get("name")

    if next_name is None and ("first_name" in updates or "last_name" in updates):
        c.execute("SELECT first_name, last_name, name FROM users WHERE id = ?", (user_id,))
        existing = c.fetchone()
        if existing:
            first_name = next_first_name if next_first_name is not None else (existing[0] or "")
            last_name = next_last_name if next_last_name is not None else (existing[1] or "")
            derived_name = " ".join(part for part in [first_name, last_name] if part).strip()
            next_name = derived_name or existing[2] or first_name or "User"

    if next_name is not None and "name" not in updates:
        fields.append("name = ?")
        values.append(next_name)
    
    if not fields:
        conn.close()
        return jsonify({"error": "No fields to update"}), 400
    
    values.append(user_id)
    query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
    
    c.execute(query, values)
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Profile updated"})


def change_user_password(user_id, old_password, new_password):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT password FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    if user[0] != old_password:
        conn.close()
        return jsonify({"error": "Old password is incorrect"}), 400

    c.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, user_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Password updated"})
