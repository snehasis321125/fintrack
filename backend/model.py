import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from flask import jsonify
from db import get_connection

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FOLDER = os.path.join(BASE_DIR, "trained_models")

if not os.path.exists(MODEL_FOLDER):
    os.makedirs(MODEL_FOLDER)

def train_model_for_user(user_id):

    try:
        conn = get_connection()

        df = pd.read_sql_query(
            "SELECT * FROM expenses WHERE user_id = ? ORDER BY date",
            conn,
            params=(user_id,)
        )

        conn.close()

        if df.empty or len(df) < 10:
            print(f"Not enough data ({len(df)}) for user {user_id}")
            return False

        df['date'] = pd.to_datetime(df['date'])
        df['day'] = df['date'].dt.day
        df['month'] = df['date'].dt.month
        df['weekday'] = df['date'].dt.weekday
        df['day_of_year'] = df['date'].dt.dayofyear

        # Category encoding
        le = LabelEncoder()
        df['category_encoded'] = le.fit_transform(df['category'])

        # Lag feature
        df = df.sort_values('date')
        df['lag_1'] = df['amount'].shift(1)
        df['lag_1'].fillna(df['amount'].mean(), inplace=True)

        feature_cols = ['day', 'month', 'weekday', 'day_of_year', 'category_encoded', 'lag_1']
        X = df[feature_cols]
        y = df['amount']

        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X, y)

        joblib.dump(model, f"{MODEL_FOLDER}/model_user_{user_id}.pkl")
        joblib.dump(le, f"{MODEL_FOLDER}/le_user_{user_id}.pkl")
        joblib.dump(feature_cols, f"{MODEL_FOLDER}/features_user_{user_id}.pkl")

        print(f"Model trained for user {user_id}: {len(df)} samples")
        return True

    except Exception as e:
        print("Training error:", e)
        return False

def predict_expenses(user_id):

    model_path = f"{MODEL_FOLDER}/model_user_{user_id}.pkl"
    le_path = f"{MODEL_FOLDER}/le_user_{user_id}.pkl"

    # Auto-train if no model
    if not (os.path.exists(model_path) and os.path.exists(le_path)):
        print(f"No model for user {user_id}, training...")
        if not train_model_for_user(user_id):
            return jsonify({
                "predicted_total": 15000,  # Average monthly default
                "trend": "New user - add more expenses",
                "predicted_savings": 5000
            })

    try:
        model = joblib.load(model_path)
        le = joblib.load(le_path)

        conn = get_connection()
        df = pd.read_sql_query(
            "SELECT * FROM expenses WHERE user_id = ? ORDER BY date",
            conn,
            params=(user_id,)
        )
        conn.close()

        if df.empty:
            return jsonify({"predicted_total": 0, "trend": "No data", "predicted_savings": 0})

        df['date'] = pd.to_datetime(df['date'])
        df['day'] = df['date'].dt.day
        df['month'] = df['date'].dt.month
        df['weekday'] = df['date'].dt.weekday
        df['day_of_year'] = df['date'].dt.dayofyear
        df['category_encoded'] = le.transform(df['category'])
        df['lag_1'] = df['amount'].shift(1).fillna(df['amount'].mean())

        feature_cols = joblib.load(f"{MODEL_FOLDER}/features_user_{user_id}.pkl")
        X_recent = df[feature_cols].iloc[-1:].copy()

        predictions = []
        current_lag = X_recent['lag_1'].iloc[0]
        last_date = df['date'].max()

        for i in range(30):
            next_date = last_date + pd.Timedelta(days=i+1)
            next_features = X_recent.copy()
            next_features.loc[next_features.index[0], 'day'] = next_date.day
            next_features.loc[next_features.index[0], 'month'] = next_date.month
            next_features.loc[next_features.index[0], 'weekday'] = next_date.weekday()
            next_features.loc[next_features.index[0], 'day_of_year'] = next_date.timetuple().tm_yday
            next_features.loc[next_features.index[0], 'lag_1'] = current_lag
            
            # Random category from user's history
            cat_idx = np.random.choice(le.classes_)
            next_features.loc[next_features.index[0], 'category_encoded'] = le.transform([cat_idx])[0]
            
            pred = model.predict(next_features)[0]
            pred = max(pred, 50)  # Min daily spend
            predictions.append(pred)
            current_lag = pred

        predicted_total = sum(predictions)
        predicted_week = round(sum(predictions[:7]), 2)

        recent_avg = df['amount'].tail(7).mean()
        trend_pct = ((predictions[0] - recent_avg) / recent_avg) * 100 if recent_avg else 0
        if trend_pct > 15:
            trend = "Increasing 📈"
        elif trend_pct < -15:
            trend = "Decreasing 📉"
        else:
            trend = "Stable ➖"

        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT monthly_budget FROM users WHERE id = ?", (user_id,))
        result = c.fetchone()
        budget = result[0] if result else 0
        conn.close()

        predicted_savings = max(0, budget - predicted_total)

        return jsonify({
            "predicted_total": round(predicted_total, 2),
            "predicted_week": predicted_week,
            "trend": trend,
            "predicted_savings": round(predicted_savings, 2)
        })

    except Exception as e:
        print("Prediction error:", str(e))
        return jsonify({
            "predicted_total": 15000,
            "trend": "Training in progress",
            "predicted_savings": 5000
        })

