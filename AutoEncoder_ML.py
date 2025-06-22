import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib
import matplotlib.pyplot as plt
from flask import Flask, request, jsonify
import threading
import time
from datetime import datetime
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense
from tensorflow.keras import regularizers
from tensorflow.keras.models import load_model
import os


df = pd.read_csv('quantum_crypto_refined_dataset.csv')


drop_cols = ['Unnamed: 0', 'Time']
for col in drop_cols:
    if col in df.columns:
        df.drop(columns=col, inplace=True)


features = df.select_dtypes(include=[np.number]).columns.tolist()
X = df[features]


scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

input_dim = X_scaled.shape[1]
encoding_dim = input_dim // 2  

input_layer = Input(shape=(input_dim,))
encoded = Dense(encoding_dim, activation='relu',
                activity_regularizer=regularizers.l1(1e-4))(input_layer)
decoded = Dense(input_dim, activation='linear')(encoded)

autoencoder = Model(inputs=input_layer, outputs=decoded)
autoencoder.compile(optimizer='adam', loss='mse')
autoencoder.fit(X_scaled, X_scaled, epochs=50, batch_size=32, shuffle=True, verbose=1)


X_pred = autoencoder.predict(X_scaled)
mse = np.mean(np.power(X_scaled - X_pred, 2), axis=1)
threshold = mse.mean() + 2 * mse.std()


model_data = {
    'scaler': scaler,
    'threshold': threshold,
    'features': features,
    'autoencoder_path': 'autoencoder_model.h5'
}
joblib.dump(model_data, 'anomaly_detection_model.pkl')
autoencoder.save('autoencoder_model.h5')


df['reconstruction_error'] = mse
df['predicted_anomaly'] = df['reconstruction_error'].apply(lambda x: 1 if x > threshold else 0)


plt.figure(figsize=(12, 6))
sample_feature = features[0]
plt.scatter(df.index, df[sample_feature], c=df['predicted_anomaly'], cmap='coolwarm', alpha=0.6)
plt.title('Anomaly Detection Results (Autoencoder)')
plt.xlabel('Record Index')
plt.ylabel(sample_feature)
plt.colorbar(label='Anomaly (1) / Normal (0)')
plt.savefig('anomaly_detection_results.png')
plt.close()


app = Flask(__name__)

request_buffer = []
buffer_lock = threading.Lock()

def monitor_requests():
    model_data = joblib.load('anomaly_detection_model.pkl')
    scaler = model_data['scaler']
    threshold = model_data['threshold']
    features = model_data['features']
    autoencoder = load_model(model_data['autoencoder_path'])

    while True:
        time.sleep(60)
        with buffer_lock:
            if len(request_buffer) > 0:
                current_buffer = pd.DataFrame(request_buffer)
                X_current = current_buffer[features]
                X_scaled = scaler.transform(X_current)
                X_pred = autoencoder.predict(X_scaled)
                errors = np.mean(np.power(X_scaled - X_pred, 2), axis=1)
                anomalies = errors > threshold

                if any(anomalies):
                    print(f"Detected {sum(anomalies)} anomalies in the last minute!")
                    for idx in np.where(anomalies)[0]:
                        print(f"Anomaly error: {errors[idx]:.4f}")
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

@app.route('/')
def home():
    return "Quantum Escape Mechanism - Autoencoder-Based Anomaly Detection"

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({"message": "Secure data accessed successfully"})

