import os
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, recall_score, f1_score, confusion_matrix
)

from db import get_connection

MODEL_FOLDER = "./trained_models"
MIN_RECORDS = 10

# =========================
# 🔹 Categorization Function
# =========================
def categorize(amount):
    if amount < 1000:
        return 0   # Low
    elif amount < 5000:
        return 1   # Medium
    else:
        return 2   # High


# =========================
# 🔹 Evaluate Single User
# =========================
def evaluate_model(user_id):
    print(f"\n🔍 Evaluating User {user_id}...")

    model_path = f"{MODEL_FOLDER}/model_user_{user_id}.pkl"
    le_path = f"{MODEL_FOLDER}/le_user_{user_id}.pkl"
    features_path = f"{MODEL_FOLDER}/features_user_{user_id}.pkl"

    # Check model files
    if not all(os.path.exists(p) for p in [model_path, le_path, features_path]):
        print(f"❌ No trained model found for user {user_id}")
        return

    # Load model artifacts
    model = joblib.load(model_path)
    le = joblib.load(le_path)
    feature_cols = joblib.load(features_path)

    # Load user data
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY date",
        conn,
        params=(user_id,)
    )
    conn.close()

    if len(df) < MIN_RECORDS:
        print(f"⚠️ Only {len(df)} records (need {MIN_RECORDS})")
        return

    # =========================
    # 🔹 Feature Engineering
    # =========================
    df['date'] = pd.to_datetime(df['date'])

    df['day'] = df['date'].dt.day
    df['month'] = df['date'].dt.month
    df['weekday'] = df['date'].dt.weekday
    df['day_of_year'] = df['date'].dt.dayofyear

    df['category_encoded'] = le.transform(df['category'])

    df['lag_1'] = df['amount'].shift(1)
    df['lag_1'].fillna(df['amount'].mean(), inplace=True)

    X = df[feature_cols]
    y_true = df['amount']

    # =========================
    # 🔹 Prediction
    # =========================
    y_pred = model.predict(X)

    # =========================
    # 📊 REGRESSION METRICS
    # =========================
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)

    # Tolerance Accuracy (±20%)
    tolerance = 0.2
    tolerance_accuracy = np.mean(
        np.abs(y_true - y_pred) <= tolerance * y_true
    )

    # =========================
    # 📊 CLASSIFICATION METRICS
    # =========================
    y_true_cat = y_true.apply(categorize)
    y_pred_cat = pd.Series(y_pred).apply(categorize)

    accuracy = accuracy_score(y_true_cat, y_pred_cat)
    recall = recall_score(y_true_cat, y_pred_cat, average='weighted')
    f1 = f1_score(y_true_cat, y_pred_cat, average='weighted')
    cm = confusion_matrix(y_true_cat, y_pred_cat)

    # =========================
    # 📊 FEATURE IMPORTANCE
    # =========================
    feat_imp_df = None
    if hasattr(model, "feature_importances_"):
        feat_imp_df = pd.DataFrame({
            "Feature": feature_cols,
            "Importance": model.feature_importances_
        }).sort_values(by="Importance", ascending=False)

    # =========================
    # 🧾 OUTPUT
    # =========================
    print(f"\n=== Results for User {user_id} ===")
    print(f"Records: {len(df)}")

    print("\n--- Regression ---")
    print(f"MAE: ₹{mae:.2f}")
    print(f"RMSE: ₹{rmse:.2f}")
    print(f"R²: {r2:.4f}")
    print(f"Tolerance Accuracy (±20%): {tolerance_accuracy*100:.2f}%")

    print("\n--- Classification ---")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1 Score: {f1:.4f}")

    print("\nConfusion Matrix:")
    print("[[Low, Medium, High]]")
    print(cm)

    # =========================
    # 📊 Visualization
    # =========================
    if feat_imp_df is not None:
        print("\n--- Feature Importance ---")
        print(feat_imp_df)

        plt.figure()
        plt.barh(feat_imp_df["Feature"], feat_imp_df["Importance"])
        plt.title(f"Feature Importance - User {user_id}")
        plt.xlabel("Importance")
        plt.ylabel("Feature")
        plt.gca().invert_yaxis()
        plt.show()

    # =========================
    # 🧠 Interpretation
    # =========================
    if r2 > 0.8:
        print("📊 EXCELLENT regression")
    elif r2 > 0.6:
        print("📈 GOOD regression")
    else:
        print("⚠️ Improve regression model")

    if accuracy > 0.8:
        print("🎯 Strong classification")
    elif accuracy > 0.6:
        print("📊 Moderate classification")
    else:
        print("⚠️ Weak classification")


# =========================
# 🚀 Evaluate ALL Users
# =========================
def evaluate_all_users():
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT id FROM users")
    users = c.fetchall()

    conn.close()

    if not users:
        print("❌ No users found")
        return

    print(f"\n🚀 Evaluating {len(users)} users...\n")

    for user in users:
        try:
            evaluate_model(user[0])
        except Exception as e:
            print(f"❌ Error evaluating user {user[0]}: {e}")


# =========================
# ▶ MAIN
# =========================
if __name__ == "__main__":
    evaluate_all_users()