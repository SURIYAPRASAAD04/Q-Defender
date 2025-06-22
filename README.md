
# Quantum Dynamic Escape Mechanism (Q-Defender) - D8071 

## Overview

**Quantum Dynamic Escape Mechanism (Q-Defender)** is a post-quantum cryptographic defense system designed to provide multi-layered security using a combination of classical and quantum-safe algorithms. The system features anomaly detection, dynamic encryption layers, attack simulations, and automated escape mechanisms to defend against modern and quantum-level threats.

## Features

- 🔐 Multi-layer Encryption (AES-256 + Post-Quantum Algorithms: Kyber, McEliece, Falcon, NTRU, Dilithium)
- 🤖 Machine Learning-based Anomaly Detection (AutoEncoder, Isolation Forest)
- ⚠️ Dynamic Escape Activation on Anomalies
- 🧪 Simulated Attack Testing (MITM, Brute-force, SQL Injection, XSS, etc.)
- 📧 Email Notification Alerts
- ☁️ Firebase integration for event logging

## Project Structure

```
Quantum Dynamic Escape Mechanism /
├── AutoEncoder_ML.py
├── Isolation_ML.py
├── anomaly_detection_model.pkl
├── anomaly_detection_results.png
├── Escape_mechanism.py
├── File_format_identifier.py
├── Key_Obfuscation.py
├── MITM_Attack.py
├── PQC_layers.py
├── Q-Defender.py
├── Send_notification_mail.py
├── quantum_crypto_refined_dataset.csv
├── q-defender-firebase-adminsdk-*.json
├── static/css/...
└── Escape_mechanism_activation_test/
    ├── run_all_tests.py
    └── attack_tests/
        ├── brute_force_test.py
        ├── sql_injection_test.py
        ├── slowloris_test.py
        ├── xss_test.py
        ├── malicious_file_test.py
        └── utils/
            ├── attack_patterns.py
            └── test_helpers.py
```

## Installation

1. **Clone or extract** the repository.
2. **Install dependencies** (Python 3.10+ recommended):

```bash
pip install -r requirements.txt
```

> Create `requirements.txt` with the necessary libraries such as `scikit-learn`, `tensorflow`, `pandas`, `flask`, etc.

## Usage

### Start Main Encryption System

```bash
python Q-Defender.py
```

### Run Anomaly Detection

```bash
python AutoEncoder_ML.py
# or
python Isolation_ML.py
```

### Test Escape Mechanism Activation

```bash
cd Escape_mechanism_activation_test
python run_all_tests.py
```

## Notes

- Ensure proper Firebase credentials in `q-defender-firebase-adminsdk-*.json`
- Email notifications require valid SMTP setup in `Send_notification_mail.py`

## License

This project is part of Unisys Innovation Program (UIP'16). All rights @Unisys.
