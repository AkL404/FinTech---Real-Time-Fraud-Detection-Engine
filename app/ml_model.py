import numpy as np
from sklearn.ensemble import IsolationForest

# Train model once (simulated training data)
# Normal transactions around 10 - 3000
training_data = np.array([[50], [100], [300], [500], [1200], [2000], [2500], [3000]])

model = IsolationForest(contamination=0.15, random_state=42)
model.fit(training_data)

def ml_score(amount: float) -> float:
    """
    Returns anomaly probability (0 → safe, 100 → suspicious)
    """
    value = np.array([[amount]])
    prediction = model.decision_function(value)[0]

    # Convert IsolationForest score into 0–100 scale
    risk = (1 - prediction) * 100
    return round(min(max(risk, 0), 100), 2)
