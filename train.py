import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

# LOAD DATA
df = pd.read_csv("dataset/Clean_Dataset.csv")

# CLEAN
df = df.dropna()
df["duration"] = df["duration"].astype(float)

if "days_left" not in df.columns:
    df["days_left"] = 10

# ENCODE
label_cols = ["airline", "source_city", "destination_city"]

for col in label_cols:
    if col in df.columns:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])

# FEATURES
features = ["duration", "days_left"]

for col in label_cols:
    if col in df.columns:
        features.append(col)

X = df[features]
y = df["price"]

# TRAIN
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestRegressor(n_estimators=100)
model.fit(X_train, y_train)

# SAVE
joblib.dump(model, "ml_models/flight_price_model.pkl")
joblib.dump(features, "ml_models/model_columns.pkl")

print("✅ DONE")