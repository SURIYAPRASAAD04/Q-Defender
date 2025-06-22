
import os
import time
import json
import secrets
import threading
from datetime import datetime
from bson import ObjectId, json_util

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from flask_socketio import SocketIO, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from pymongo import MongoClient
from authlib.integrations.flask_client import OAuth
from firebase_admin import credentials, firestore
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib
from joblib import load

from PQC_layers import generate_all_keys, encrypt_layered, decrypt_layered, create_folder
from Escape_mechanism import escape_mechanism, escape_mechanism_reconstruction
from Send_notification_mail import send_attack_detect_email, send_welcome_email, send_error_report_email
from File_format_identifier import identify_file_type




app = Flask(__name__)
app.secret_key = 'D-Defender@uip16' 

client = MongoClient("mongodb://localhost:27017/") 
db = client["Q-Defender"]
AES_Encryption_collection = db["AES encryption"]
Key_Vault_collection = db["Key Vault"]
Key_Cipher_collection = db["Key Cipher"]
large_files_collection = db["Large files"]

cred = credentials.Certificate("q-defender-firebase-adminsdk-fbsvc-756017b167.json")

db_fire = firestore.client()


app.config['REDIRECT_URI'] = "http://127.0.0.1:5000/auth/callback"  


oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account',  
    },
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
)

output_dir = "folder_sec_inst"

stored_message = None
socketio = SocketIO(app)
anomaly_state = {
            "detected": False,
            "last_detected": None,
            "lockout_until": None
        }

limiter = Limiter(
    app=app,
    key_func=get_remote_address
)


try:
    model = load('anomaly_detection_model.pkl')
except:
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('isolation_forest', IsolationForest(
            n_estimators=150,
            contamination=0.03,
            max_features=0.8,
            random_state=42,
            verbose=1
        ))
    ])
    dummy_data = np.random.rand(200, 12)
    model.fit(dummy_data)
    joblib.dump(model, 'anomaly_detection_model.pkl')

request_buffer = []
anomaly_detected = False
security_lock = threading.Lock()
high_alert = False

FEATURES = [
    'response_time',
    'request_size',
    'response_size',
    'status_200',
    'status_404',
    'status_500',
    'unique_ip',
    'api_endpoint',
    'requests_per_min',
    'user_agent',
    'encrypted',
    'sensitive'
]

def monitor_requests():
    global anomaly_detected, high_alert
    while True:
        time.sleep(15)  
        with security_lock:
            if len(request_buffer) > 10:  
                df = pd.DataFrame(request_buffer[-20:])  
                
                for feature in FEATURES:
                    if feature not in df.columns:
                        df[feature] = 0
                
                scores = model.decision_function(df[FEATURES])
                predictions = model.predict(df[FEATURES])
                
                if any(predictions == -1):
                    anomaly_score = min(scores)
                    print(f"🚨 SECURITY ALERT! Anomaly score: {anomaly_score:.2f}")
                    log_security_event(f"Anomaly detected - Score: {anomaly_score:.2f}")
                    
                    if anomaly_score < -0.7: 
                        high_alert = True
                        trigger_quantum_escape_protocol(severity='high')
                    else:
                        high_alert = False
                        trigger_quantum_escape_protocol(severity='medium')
                    
                    anomaly_detected = True

def log_security_event(message):
    with open('security.log', 'a') as f:
        f.write(f"{datetime.now()} - {message}\n")


def trigger_quantum_escape_protocol(severity='medium'):
    global stored_message
    
    actions = {
        'medium': [
            "Activated additional Kyber encryption layer",
            "Enabled traffic obfuscation",
            "Triggered 2FA verification"
        ],
        'high': [
            "FULL QUANTUM ESCAPE PROTOCOL ENGAGED",
            "Regenerated all cryptographic keys",
            "Enabled maximum fragmentation with decoys",
            "Isolated sensitive data stores",
            "Disabled non-essential endpoints"
        ]
    }
    
    log_security_event(f"QUANTUM ESCAPE ACTIVATED - Severity: {severity.upper()}")
    
    if stored_message:
        encrypt_layered(stored_message, security_level=severity)
    
    if severity == 'high':
        generate_all_keys(force_refresh=True)
        socketio.emit('security_alert', {
            'level': 'critical',
            'message': 'Quantum Escape Protocol Engaged',
            'actions': actions['high']
        })

def check_anomaly():
    global anomaly_detected
    with security_lock:
        if anomaly_detected:
            anomaly_detected = False
            return True
        return False

def log_request_data(request):
    sensitive_endpoints = ['/process_new', '/upload_file', '/submit_message', 
                          '/decryption', '/download_decoded']
    return {
        'timestamp': datetime.now(),
        'response_time': np.random.normal(120, 20, 1)[0].clip(50, 1000),
        'request_size': request.content_length or 0,
        'response_size': 0,
        'status_200': 0,
        'status_404': 0,
        'status_500': 0,
        'unique_ip': 1 if request.remote_addr not in [r.get('ip', '') for r in request_buffer] else 0,
        'api_endpoint': hash(request.path) % 30,
        'requests_per_min': len([r for r in request_buffer if (datetime.now() - r['timestamp']).seconds < 60]),
        'user_agent': hash(request.user_agent.string) % 15 if request.user_agent else 0,
        'ip': request.remote_addr,
        'path': request.path,
        'method': request.method,
        'encrypted': 1 if request.path in sensitive_endpoints else 0,
        'sensitive': 1 if 'data' in request.path or 'decrypt' in request.path else 0
    }

def check_and_handle_anomaly(request):
    """Enhanced anomaly detection logic"""
    global anomaly_state
    
    if anomaly_state["lockout_until"] and time.time() < anomaly_state["lockout_until"]:
        return True
    
    anomaly_score = 0

    suspicious_headers = ["X-ATTACK-TYPE", "MALICIOUS-BOT"]
    for h in suspicious_headers:
        if h in request.headers:
            anomaly_score += 30
    
    if request.content_length and request.content_length > 10000*10000:  # 10KB
        anomaly_score += 20
    
    if request.method == "POST":
        data = request.get_data(as_text=True)
        attack_patterns = ["' OR '1'='1", "<script>", "../", "\\x00"]
        for pattern in attack_patterns:
            if pattern in data:
                anomaly_score += 40
    
    if anomaly_score >= 50:
        anomaly_state = {
            "detected": True,
            "last_detected": time.time(),
            "lockout_until": time.time() + 300  
        }
        return True
    
    return False

def before_request_handler():
    """Check all requests for anomalies"""
    if check_and_handle_anomaly(request):
        print("request ",request)
        if request.endpoint != 'activate':
            print("in before request part")
            return True
    return True



@app.after_request
def after_request_handler(response):
    if request.endpoint and request.endpoint != 'static' and request_buffer:
        with security_lock:
            last_request = request_buffer[-1]
            last_request['response_size'] = response.content_length or 0
            if response.status_code == 200:
                last_request['status_200'] = 1
            elif response.status_code == 404:
                last_request['status_404'] = 1
            elif response.status_code == 500:
                last_request['status_500'] = 1
    return response


monitor_thread = threading.Thread(target=monitor_requests, daemon=True)
monitor_thread.start()


client = MongoClient("mongodb://localhost:27017/")
db = client["Q-Defender"]
users = db["Q-Defender User Details"]

@app.route('/')
def home():
    if False:
        return redirect(url_for('activate'))
    else:
        try:
         email = session.get("email")
         user = users.find_one({"email": email})
         if(user):
            picture = user.get("picture") 
            user_id = user.get("id")
            print("Picture URL from DB:", picture)
          
            total_data_secured = AES_Encryption_collection.count_documents({"user_id": user_id})
            
            security_shield_activated = AES_Encryption_collection.count_documents({
                "user_id": user_id,
                "status": "Fragmented"
            })
            stats = db.command("dbstats")
            storage_used = round(stats['dataSize'] / (1024 * 1024), 2) 
           
            recent_data_cursor = AES_Encryption_collection.find(
                {"user_id": user_id},
                {
                    "meta_data": 1,
                    "encrypted_at": 1,
                    "data_format": 1,
                    "status": 1,
                    "layers": 1,
                    "_id": 0
                }
            ).sort("encrypted_at", -1).limit(5)
            
          
            recent_data = []
            for item in recent_data_cursor:
                
                if 'encrypted_at' in item:
                    if isinstance(item['encrypted_at'], dict) and '$date' in item['encrypted_at']:
                       
                        try:
                            item['encrypted_at'] = datetime.fromisoformat(
                                item['encrypted_at']['$date'].replace('Z', '+00:00')
                            )
                        except ValueError:
                            item['encrypted_at'] = None
                    elif isinstance(item['encrypted_at'], datetime):
                       
                        pass
                    else:
                        item['encrypted_at'] = None
                
               
                item.setdefault('meta_data', 'Unknown')
                item.setdefault('data_format', 'Unknown')
                item.setdefault('status', 'Unknown')
                item.setdefault('layers', 0)
                
                recent_data.append(item)
            
            return render_template('Q-Defender.html',
                                total_data_secured=total_data_secured,
                                security_shield_activated=security_shield_activated,
                                storage_used=storage_used,
                                recent_data=recent_data, picture=picture)

         else:
            return render_template("index.html")
         
        except Exception as e:
            print(f"Error in dashboard route: {str(e)}")
            
            return render_template('Q-Defender.html',
                                total_data_secured=0,
                                security_shield_activated=0,
                                storage_used=0,
                                recent_data=[])

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return ""
    return value.strftime(format)

@app.route("/login/google")
def login():
    return google.authorize_redirect(redirect_uri=app.config['REDIRECT_URI'])

@app.route("/auth/callback")
def callback():
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    print(user_info)

    session['email'] = user_info['email']
    session['name'] = user_info['name']
    session["picture"] = user_info['picture']

    send_welcome_email(user_info['email'], user_info['name'])

    users.update_one(
        {"email": user_info["email"]},
        {
            "$set": {
                **user_info,
                "last_login": datetime.now()
            }
        },
        upsert=True
    )
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route('/login')
def login_page():
    if False:
        return redirect(url_for('activate'))
    return render_template('login.html')


@app.route('/decryption')
def decryption_page():
    data_id = session.get("data_id")
    print("Decryt ",data_id)
    if before_request_handler():
        print("here")
        return redirect(url_for('activate',data_id=data_id))
    email = session.get("email")
    user = users.find_one({"email": email})
    if(user):
            picture = user.get("picture") 
            print("Picture URL from DB:", picture)

    AES_Encryption = AES_Encryption_collection.find_one({"data_id": data_id})
    anomaly_triggered = AES_Encryption.get("anomaly_triggered")
    metadata = AES_Encryption.get("meta_data").capitalize()
    print(anomaly_triggered)
    if(anomaly_triggered == True):
        return render_template('decryption_backup_db.html',picture=picture, metadata=metadata)
    else:
        return render_template('decryption_primary_db.html',picture=picture, metadata=metadata)


@app.route('/about')
def about():
    return render_template('about.html')



@app.route('/managedata')
def managedata():
    if check_and_handle_anomaly():
        return redirect(url_for('activate'))
    else:
        email = session.get("email")
        user = users.find_one({"email": email})
        if user:
            picture = user.get("picture")
            user_id = user.get("id")
       
            encryption_data = list(AES_Encryption_collection.find({"user_id": user_id}))
            
    
            def serialize_doc(doc):
                if isinstance(doc, dict):
                    for key, value in doc.items():
                        if isinstance(value, ObjectId):
                            doc[key] = str(value)
                        elif isinstance(value, bytes):
                            doc[key] = "Binary data"
                        elif isinstance(value, datetime):
                            doc[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                        elif isinstance(value, dict) and '$date' in value:
                            try:
                                date_str = value['$date']
                                if '.' in date_str:
                                    parsed_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                                else:
                                    parsed_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                                doc[key] = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                doc[key] = "Date unavailable"
                    return doc
                return doc
            
         
            processed_data = [serialize_doc(doc) for doc in encryption_data]

          
            for doc in processed_data:
                doc.setdefault('data_id', 'N/A')
                doc.setdefault('meta_data', 'No description')
                doc.setdefault('status', 'Unknown')
                doc.setdefault('data_format', 'Unknown')
                doc.setdefault('layers', 0)
                doc.setdefault('user_id', 'N/A')
            
        
            return render_template(
                "ManageData.html", 
                picture=picture,
                encryption_data=json.loads(json_util.dumps(processed_data))
            )
        else:
            return render_template("index.html")


@app.route('/view-data/<data_id>')
def view_data(data_id):
    try:
      
        session['data_id'] = data_id
        data = AES_Encryption_collection.find_one({"_id": ObjectId(data_id)})
        if data:
         
            data['_id'] = str(data['_id'])
            if 'enc_data' in data:
                data['enc_data'] = "REDACTED"
            return jsonify(data)
        else:
            return jsonify({"error": "Data not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete-data/<data_id>', methods=['DELETE'])
def delete_data(data_id):
    try:
        result1 = AES_Encryption_collection.delete_one({"data_id": data_id})
        result2 = Key_Vault_collection.delete_one({"data_id": data_id})
        result3 = Key_Cipher_collection.delete_one({"data_id": data_id})
        result4 = large_files_collection.delete_many({"data_id": data_id})

        if result1.deleted_count > 0 :
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Document not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    

@app.route('/unlock-data/<data_id>', methods=['POST'])
def unlock_data(data_id):
    session['data_id'] = data_id
    data_id = data_id
    print("unlock",data_id)
    if before_request_handler():
        return redirect(url_for('activate',data_id=data_id))
    else:
   
        AES_Encryption = AES_Encryption_collection.find_one({"data_id": data_id})
        Key_Vault = Key_Vault_collection.find_one({"data_id": data_id})
        Key_Cipher = Key_Cipher_collection.find_one({"data_id": data_id})
        key_dict = Key_Vault.get("Key")
        aes_ciphertext = AES_Encryption.get("enc_data")
        
        if not AES_Encryption:
            raise ValueError(f"No record found for data_id: {data_id}")
        
        if not AES_Encryption.get("large_file", False):
             aes_ciphertext = AES_Encryption.get("enc_data")
        else:
            aes_ciphertext = AES_Encryption["enc_data"]
            
            fragments = list(large_files_collection.find(
                {"data_id": data_id},
                sort=[("fragment_no", 1)]
            ))
            
            expected_fragments = AES_Encryption["total_fragments"] - 1 
            if len(fragments) != expected_fragments:
                raise ValueError(f"Missing fragments. Expected {expected_fragments}, found {len(fragments)}")

            for fragment in fragments:
                aes_ciphertext += fragment["fragmented_enc_data"]
        
    

        ntru_ciphertext = Key_Cipher.get("cipher_data").get("ntru")
        mceliece_ciphertext = Key_Cipher.get("cipher_data").get("mceliece")
        encrypted_falcon_sig = Key_Cipher.get("cipher_data").get("Falcon_cipher")
        falcon_public_key = Key_Cipher.get("cipher_data").get("Falcon_public_key")
        encrypted_kyber_ct = Key_Cipher.get("cipher_data").get("kyber")
        support_data = Key_Cipher.get("aes_bin")
        aes_iv = Key_Cipher.get("aes_iv")
        anomaly_triggered = AES_Encryption.get("anomaly_triggered")
        if anomaly_triggered:
            dilithium_signature = Key_Cipher.get("cipher_data").get("dilithium")
            escape_mechanism_reconstruction(data_id, aes_iv, support_data, aes_ciphertext, ntru_ciphertext, mceliece_ciphertext, encrypted_falcon_sig, encrypted_kyber_ct,falcon_public_key,dilithium_signature)  
        else:    
          decrypt_layered(key_dict,aes_iv, support_data, aes_ciphertext, ntru_ciphertext, mceliece_ciphertext, encrypted_falcon_sig, encrypted_kyber_ct,falcon_public_key)
        
        email = session.get("email")
        user = users.find_one({"email": email})
        if(user):
            picture = user.get("picture") 
            print("Picture URL from DB:", picture)
        return redirect(url_for('decryption_page', data_id=data_id))


@app.route('/my_profile')
def my_profile():
    email = session.get("email")
    user = users.find_one({"email": email})
    if(user):
            picture = user.get("picture") 
            name = user.get("name").capitalize()
            given_name = user.get("given_name").capitalize()
            last_login = str(user.get("last_login"))
            dt = datetime.fromisoformat(last_login)
            last_login = dt.strftime("%B %d, %Y at %I:%M %p")
            user_id = user.get("id")

    return render_template('my_profile.html', picture=picture,name=name,given_name = given_name,last_login=last_login,user_id=user_id,email=email)

@app.route('/account_settings')
def account_settings():
    email = session.get("email")
    user = users.find_one({"email": email})
    if(user):
            picture = user.get("picture") 
            print("Picture URL from DB:", picture)
    return render_template('account_settings.html', picture=picture)
global counter
counter = 1
@app.route('/activate/<data_id>')
def activate(data_id):
    email = session.get("email")
    user = users.find_one({"email": email})
    user_id = user.get("id")
    if(user):
            picture = user.get("picture") 
            print("Picture URL from DB:", picture)
    logo = "https://i.ibb.co/rGFMz0nC/logo.png"
    security_measures = [
        "Post-Quantum Cryptography (Kyber-1024)",
        "Data Fragmentation with Entropy Decoys",
        "Multi-Path Obfuscation Routing",
        "Temporary Access Restrictions"
    ]

    send_attack_detect_email(email)
    print("Data Id in problem is ",data_id)

    AES_Encryption = AES_Encryption_collection.find_one({"data_id": data_id})
    Key_Vault = Key_Vault_collection.find_one({"data_id": data_id})
    Key_Cipher = Key_Cipher_collection.find_one({"data_id": data_id})
    key_dict = Key_Vault["Key"]
    print("length of key before passing: ",len(key_dict))
    global counter
    if(counter == 1):
        escape_mechanism(Key_Vault,Key_Cipher,data_id,user_id)
        counter += 1


    return render_template('activate.html',
                         message="Quantum Escape Protocol Engaged",
                         measures=security_measures,
                         alert_level="high" if high_alert else "medium", picture=picture , logo= logo)

@app.route('/process_new', methods=['POST'])
@limiter.limit("10 per minute")
def process_new():

    
    user_data = request.form.get('user_data')
    session['user_data'] = user_data  
    return redirect(url_for('activate'))

def generate_id(prefix):
    random_part = secrets.token_hex(8)  
    return f"{prefix}_{random_part}"

def bytes_to_bitstring(data_bytes):
    return ''.join(format(byte, '08b') for byte in data_bytes)

def bits_to_image(bit_data, output_path):
    byte_data = bytearray(int(bit_data[i:i+8], 2) for i in range(0, len(bit_data), 8))
    with open(output_path, "wb") as f:
        f.write(byte_data)

def compare_files(file1, file2):
    with open(file1, "rb") as f1, open(file2, "rb") as f2:
        while True:
            b1 = f1.read(4096)
            b2 = f2.read(4096)
            if b1 != b2:
                return False
            if not b1:
                break
    return True

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  

@app.route('/upload_file', methods=['POST'])
@limiter.limit("5 per minute")
def upload_file():
    MAX_FILE_SIZE = 1024 * 1024 * 1024  
    
    if 'file' not in request.files:
        flash("No file uploaded.", "error")
        return render_template('encryption.html')
    
    uploaded_file = request.files['file']
    file_size = request.content_length  
    file_size_mb = file_size / (1024 * 1024)  

    print(f"Uploaded file size: {file_size} bytes ({file_size_mb:.2f} MB)")

  
    if request.content_length > MAX_FILE_SIZE:
        flash("File size exceeds maximum limit of 1GB", "error")
        return render_template('encryption.html')
    
 
    chunk_size = 4096  
    file_data = bytearray()
    
    while True:
        chunk = uploaded_file.read(chunk_size)
        if not chunk:
            break
        file_data.extend(chunk)
    

    create_folder()
    with open(os.path.join(output_dir, "a_og_input.txt"), "wb") as f:
        f.write(file_data)
 

    generate_all_keys()
    encrypt_layered(file_data)
    flash("Text file secured with quantum encryption!", "success")

    return render_template('encryption.html')


@app.route('/encryption_processing', methods=['POST'])
@limiter.limit("15 per minute")
def submit_message():
    email = session.get("email")
    user = users.find_one({"email": email})
    user_id = user.get("id")
    if(user):
                picture = user.get("picture") 
    try:
        data_id = generate_id("DATA")
        session["data_id"] = data_id
        session.modified = True
        manual_message = request.form.get('manual_message', '').strip()
        uploaded_file = request.files.get('file')
        file_size = request.content_length  
        file_size_mb = round(file_size / (1024 * 1024), 2)  

        print(f"Uploaded file size: {file_size} bytes ({file_size_mb:.2f} MB)")

        metadata = request.form.get('metadata')

        if not manual_message and (not uploaded_file or uploaded_file.filename == ''):
            flash("Please enter a message or upload a file.", "error")
            email = session.get("email")
            user = users.find_one({"email": email})
            if(user):
                picture = user.get("picture") 
                print("Picture URL from DB:", picture)
            return render_template('encryption.html',picture=picture)
        
        try:
            create_folder()
            if manual_message:
                full_payload = manual_message.encode()
            else:
                full_payload = uploaded_file.read()

            with open(os.path.join(output_dir, "a_og_input.txt"), "wb") as f:
                f.write(full_payload)

            input_file= os.path.join(output_dir, "a_og_input.txt")

            data_format = identify_file_type(input_file)

            data_format = data_format[1:]
            print("data_format",data_format)
        
            key_id = generate_id("KEY")
            email = session.get("email")
            user = users.find_one({"email": email})
            if(user):
                user_id = user.get("id") 
            generate_all_keys(data_id, key_id, user_id)
            encrypt_layered(full_payload, data_format, data_id, key_id, metadata, user_id, file_size_mb)
            flash("Data secured with quantum encryption!", "success")
            
        except Exception as e:
            
            flash(f"Security error: {str(e)}", "error")
       
              
        if check_anomaly():
            return redirect(url_for('activate'))
        else:
            error = {
                    'writeErrors': [
                        {
                            'index': 2,
                            'code': 11000,
                            'errmsg': 'E11000 duplicate key error...',
                            'op': "{ /* document */ }"
                        }
                    ],
                    'nInserted': 2,
                    'writeConcernErrors': []
                }
        return render_template('encryption.html',picture=picture)
        
    except Exception as e:
        send_error_report_email(user_id,"Data Submit error", e)
        return render_template('error.html',picture=picture)


@app.route('/download_decoded')
@limiter.limit("5 per hour")
def download_decoded():
   
    file_path = os.path.join(output_dir, "Q-Defender_Decrypted.txt")

    data_id = session.get("data_id")
    AES_Encryption = AES_Encryption_collection.find_one({"data_id": data_id})
    metadata = AES_Encryption.get("meta_data")
    if not os.path.exists(file_path):
        flash("Decrypted file not available.", "error")
        return redirect(url_for('decryption'))

    with open(file_path, "rb") as f:
        content = f.read()

    payload = content

    with open(file_path, "wb") as f:
            f.write(payload)
    ext =  identify_file_type(file_path)
    
    if ext == ".txt":
        filename =  file_path
   
        with open(file_path, "wb") as f:
            f.write(payload)
        return send_file(file_path, as_attachment=True)

    else:

        bit_string = payload
        image_path = os.path.join(output_dir, f"Q-Defender_{metadata}{ext}")
        bit_string = bytes_to_bitstring(bit_string)
        bits_to_image(bit_string, image_path)

        return send_file(image_path, as_attachment=True)
        
    return redirect(url_for('decryption'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template('rate_limit.html'), 429


@socketio.on('connect')
def handle_connect():
    emit('security_status', {
        'status': 'normal',
        'message': 'All systems operational'
    })

@socketio.on('security_check')
def handle_security_check():
    emit('security_update', {
        'alert_level': 'high' if high_alert else 'normal',
        'last_checked': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/debug/anomaly', methods=['POST'])
def debug_anomaly():
    """Endpoint to test anomaly detection"""
    score = 0
    report = []

    suspicious = ["X-ATTACK-TYPE", "MALICIOUS", "EVIL"]
    for h in request.headers:
        if any(s in h.upper() for s in suspicious):
            score += 30
            report.append(f"Suspicious header: {h} (+30)")

    if request.method == "POST":
        data = request.get_data(as_text=True)
        patterns = ["' OR", "<script>", "../", "\\x00"]
        for p in patterns:
            if p in data:
                score += 40
                report.append(f"Attack pattern: {p} (+40)")
    
    return jsonify({
        "score": score,
        "threshold": 50,
        "will_trigger": score >= 50,
        "analysis": report
    })

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)