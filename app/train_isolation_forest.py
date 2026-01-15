import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from joblib import dump

# --- Simulated transaction dataset ---
# Normal transactions
normal = np.random.normal(loc=200, scale=80, size=(900, 1))

# Fraud-like transactions
fraud = np.random.normal(loc=1500, scale=300, size=(100, 1))

data = np.vstack((normal, fraud))

df = pd.DataFrame(data, columns=["amount"])

# --- Train Isolation Forest ---
model = IsolationForest(
    n_estimators=200,
    contamination=0.1,   # 10% expected anomalies
    random_state=42
)

model.fit(df)

# --- Save Model ---
dump(model, "app/isolation_forest.pkl")

print("Isolation Forest model saved successfully!")
