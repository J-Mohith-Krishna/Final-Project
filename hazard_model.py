import sqlite3
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib # type: ignore

conn = sqlite3.connect('hazard_data.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS hazards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    latitude REAL,
                    longitude REAL,
                    risk_level TEXT
                )''')
conn.commit()

data = {
    'latitude': np.random.uniform(12.8, 13.2, 100),
    'longitude': np.random.uniform(77.5, 77.8, 100),
    'accident_history': np.random.randint(0, 10, 100),
    'road_condition': np.random.choice([0, 1], 100),
    'traffic_density': np.random.randint(1, 100, 100),
    'weather_condition': np.random.choice([0, 1], 100)
}
df = pd.DataFrame(data)

def classify_risk(row):
    score = row['accident_history'] * 0.4 + row['road_condition'] * 0.2 + \
            row['traffic_density'] * 0.3 + row['weather_condition'] * 0.1
    if score > 7:
        return "High"
    elif score > 4:
        return "Medium"
    else:
        return "Low"

df['risk_level'] = df.apply(classify_risk, axis=1)

X = df[['accident_history', 'road_condition', 'traffic_density', 'weather_condition']]
y = df['risk_level']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('model', RandomForestClassifier(n_estimators=100, random_state=42))
])

pipeline.fit(X_train, y_train)

joblib.dump(pipeline, 'hazard_model.pkl')

for _, row in df.iterrows():
    cursor.execute("INSERT INTO hazards (latitude, longitude, risk_level) VALUES (?, ?, ?)",
                   (row['latitude'], row['longitude'], row['risk_level']))

conn.commit()
conn.close()

print("Hazard prediction model trained and data stored successfully!")
