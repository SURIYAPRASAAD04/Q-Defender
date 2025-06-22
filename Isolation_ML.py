import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib
import matplotlib.pyplot as plt
from flask import Flask, request, jsonify
import threading
import time
from datetime import datetime

df = pd.read_csv('quantum_crypto_refined_dataset.csv')

drop_cols = ['Unnamed: 0', 'Time']
for col in drop_cols:
    if col in df.columns:
        df.drop(columns=col, inplace=True)

features = df.select_dtypes(include=[np.number]).columns.tolist()
X = df[features]


model = Pipeline([
    ('scaler', StandardScaler()),
    ('isolation_forest', IsolationForest(
        n_estimators=200,
        max_samples='auto',
        contamination=0.05, 
        max_features=1.0,
        bootstrap=False,
        n_jobs=-1,
        random_state=42,
        verbose=1
    ))
])

model.fit(X)


joblib.dump(model, 'anomaly_detection_model.pkl')


df['anomaly_score'] = model.decision_function(X)
df['predicted_anomaly'] = model.predict(X)
df['predicted_anomaly'] = df['predicted_anomaly'].apply(lambda x: 1 if x == -1 else 0)


plt.figure(figsize=(12, 6))
sample_feature = features[0]  
plt.scatter(df.index, df[sample_feature], c=df['predicted_anomaly'], cmap='coolwarm', alpha=0.6)
plt.title('Anomaly Detection Results')
plt.xlabel('Record Index')
plt.ylabel(sample_feature)
plt.colorbar(label='Anomaly (1) / Normal (0)')
plt.savefig('anomaly_detection_results.png')
plt.close()


app = Flask(__name__)

request_buffer = []
buffer_lock = threading.Lock()
anomaly_threshold = -0.5  

def monitor_requests():
    model = joblib.load('anomaly_detection_model.pkl')
    while True:
        time.sleep(60)
        with buffer_lock:
            if len(request_buffer) > 0:
                current_buffer = pd.DataFrame(request_buffer)
                X_current = current_buffer[features]

                scores = model.decision_function(X_current)
                anomalies = scores < anomaly_threshold

                if any(anomalies):
                    print(f"Detected {sum(anomalies)} anomalies in the last minute!")
                    for idx in np.where(anomalies)[0]:
                        print(f"Anomaly score: {scores[idx]:.2f}")
                        print(current_buffer.iloc[idx].to_dict())

                    trigger_quantum_escape_protocol()

                request_buffer.clear()

def trigger_quantum_escape_protocol():
    print("Activating Quantum Escape additional security layers...")


monitor_thread = threading.Thread(target=monitor_requests, daemon=True)
monitor_thread.start()

@app.before_request
def log_request():
    
    request_data = {
        'timestamp': datetime.now()
    }
    for feature in features:
        request_data[feature] = np.random.normal(df[feature].mean(), df[feature].std())

    with buffer_lock:
        request_buffer.append(request_data)

@app.after_request
def update_response(response):
    return response

