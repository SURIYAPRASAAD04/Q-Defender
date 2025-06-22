import os
import time
import oqs
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
from datetime import datetime
from joblib import load
import base64
from Key_Obfuscation import Obfuscate, Clarify
from pymongo import MongoClient
import bson 
from bson.binary import Binary

client = MongoClient("mongodb://localhost:27017/")  

db = client["Q-Defender"]
AES_Encryption_collection = db["AES encryption"]
Key_Vault_collection = db["Key Vault"]
Key_Cipher_collection = db["Key Cipher"]
large_files_collection = db["Large files"]

MAX_DOC_SIZE = 16777216 

def create_folder():
    global output_dir
    output_dir = "folder_sec_inst"
    os.makedirs(output_dir, exist_ok=True)

def aes_encrypt(message, key, iv):
    padder = padding.PKCS7(128).padder()
    padded = padder.update(message) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(padded) + encryptor.finalize()

def aes_decrypt(ciphertext, key, iv):
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()

def derive_aes_keys(shared_secret):
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=48,  
        salt=None,
        info=b'aes_key_derivation',
        backend=default_backend()
    )
    key_material = hkdf.derive(shared_secret)
    return key_material[:32], key_material[32:48]

def generate_all_keys(data_id, key_id, user_id):
    create_folder()

    with oqs.KeyEncapsulation("Kyber768") as kem:
        global kyber_pub 
        kyber_pub = kem.generate_keypair()
       
        global kyber_priv
        kyber_priv= kem.export_secret_key()
       
    with oqs.KeyEncapsulation("Classic-McEliece-460896f") as kem:
        global mceliece_pub
        mceliece_pub = kem.generate_keypair()
        global mceliece_priv
        mceliece_priv = kem.export_secret_key()
           
    with oqs.Signature("Falcon-1024") as sig:
        falcon_pub = sig.generate_keypair()
      

        global falcon_public_key
        falcon_public_key = falcon_pub
        global falcon_priv
        falcon_priv =sig.export_secret_key()

    with oqs.KeyEncapsulation("sntrup761") as kem:
        global ntru_pub
        ntru_pub = kem.generate_keypair()
        global ntru_priv
        ntru_priv = kem.export_secret_key()
  
            
    print(f"[*] All key pairs generated and saved in the '{output_dir}' folder.")
    og_de_data = kyber_priv + mceliece_priv + falcon_public_key + ntru_priv
    de_data = str(og_de_data)
    Result =  Obfuscate(og_de_data) 
    record = {
        "Key": Result,
        "created_at": datetime.now(),
        "data_id": data_id,
        "decoy_attached": False,
        "key_id": key_id,
        "layers": 4,
        "user_id": user_id,
        "fragmented_at": "",
        "anomaly_detected_at": ""
   }
    try:
        Key_Vault_collection.insert_one(record)
        print( "Record inserted successfully!")
    except Exception as e:
        print( f"Error: {str(e)}")

   

def encrypt_layered(message, data_format, data_id, key_id, metadata, user_id,file_size_mb):
    create_folder()

    aes_key = os.urandom(32)  
    aes_iv = os.urandom(16)   
    start = time.time()
    aes_encrypted_message = aes_encrypt(message, aes_key, aes_iv)

    if not file_size_mb:
        file_size_mb = False

    if len(aes_encrypted_message) <= MAX_DOC_SIZE:
        if file_size_mb:
            record = {
                "anomaly_triggered": False,
                "data_id": data_id,
                "encrypted_at": datetime.now(),
                "key_id": key_id,
                "layers": 4,
                "meta_data": metadata,
                "status": "Active",
                "anomaly_detected": False,
                "decoy_attached": False,
                "user_id": user_id,
                "enc_data": Binary(aes_encrypted_message),
                "data_format": data_format,
                "anomaly_detected_at": None,
                "position_size_enc_data_added": False,
                "large_file": False,
                "file_size_mb":file_size_mb
            }
        else:
            record = {
                "anomaly_triggered": False,
                "data_id": data_id,
                "encrypted_at": datetime.now(),
                "key_id": key_id,
                "layers": 4,
                "meta_data": metadata,
                "status": "Active",
                "anomaly_detected": False,
                "decoy_attached": False,
                "user_id": user_id,
                "enc_data": Binary(aes_encrypted_message),
                "data_format": data_format,
                "anomaly_detected_at": None,
                "position_size_enc_data_added": False,
                "large_file": False,
                "file_size_mb":file_size_mb
            }
        try:
            AES_Encryption_collection.insert_one(record)
        except Exception as e:
            print( f"Error: {str(e)}")
    else:
       
        fragment_size = MAX_DOC_SIZE - 1000 
        num_fragments = (len(aes_encrypted_message) + fragment_size - 1) // fragment_size
        
        first_fragment = aes_encrypted_message[:fragment_size]
        if file_size_mb:
            record = {
                "anomaly_triggered": False,
                "data_id": data_id,
                "encrypted_at": datetime.now(),
                "key_id": key_id,
                "layers": 4,
                "meta_data": metadata,
                "status": "Active",
                "anomaly_detected": False,
                "decoy_attached": False,
                "user_id": user_id,
                "enc_data": Binary(first_fragment),
                "data_format": data_format,
                "anomaly_detected_at": None,
                "position_size_enc_data_added": False,
                "large_file": True,
                "total_fragments": num_fragments,
                "file_size_mb":file_size_mb
            }
        else:
            record = {
                "anomaly_triggered": False,
                "data_id": data_id,
                "encrypted_at": datetime.now(),
                "key_id": key_id,
                "layers": 4,
                "meta_data": metadata,
                "status": "Active",
                "anomaly_detected": False,
                "decoy_attached": False,
                "user_id": user_id,
                "enc_data": Binary(first_fragment),
                "data_format": data_format,
                "anomaly_detected_at": None,
                "position_size_enc_data_added": False,
                "large_file": True,
                "total_fragments": num_fragments,
                "file_size_mb":file_size_mb
            }
        try:
            AES_Encryption_collection.insert_one(record)
        except Exception as e:
            print( f"Error: {str(e)}")
        
        for i in range(1, num_fragments):
            start = i * fragment_size
            end = (i + 1) * fragment_size
            fragment = aes_encrypted_message[start:end]
            try:
                large_files_collection.insert_one({
                    "data_id": data_id,
                    "fragment_no": i,
                    "fragmented_enc_data": Binary(fragment),
                    "total_fragments": num_fragments
                })
            except Exception as e:
                print( f"Error: {str(e)}")

    aes_ciphertext = aes_encrypted_message
    end = time.time()

    print(f"[*] AES-256 encryption done in {end - start:.6f} sec.")
    
    with oqs.KeyEncapsulation("Kyber768") as kem:
        start = time.time()
        kyber_ciphertext, kyber_shared_secret = kem.encap_secret(kyber_pub) 

        enc_key, enc_iv = derive_aes_keys(kyber_shared_secret)
      
        cipher = Cipher(algorithms.AES(enc_key), modes.CFB(enc_iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_aes_key = encryptor.update(aes_key) + encryptor.finalize()

        end = time.time()

    print(f"[*] Kyber768 encapsulation of AES key done in {end - start:.6f} sec.")


    with oqs.KeyEncapsulation("Classic-McEliece-460896f") as kem:
        start = time.time()
        mceliece_ciphertext, mceliece_shared_secret = kem.encap_secret(mceliece_pub)
 
        enc_key, enc_iv = derive_aes_keys(mceliece_shared_secret)
   
        cipher = Cipher(algorithms.AES(enc_key), modes.CFB(enc_iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_kyber_ct = encryptor.update(kyber_ciphertext) + encryptor.finalize()
        end = time.time()

    print(f"[*] McEliece encapsulation of Kyber ciphertext done in {end - start:.6f} sec.")
    

    with oqs.Signature("Falcon-1024") as sig:
        sig = oqs.Signature("Falcon-1024", secret_key=falcon_priv)
        start = time.time()
        falcon_signature = sig.sign(mceliece_ciphertext)
        end = time.time()
  
    print(f"[*] Falcon1024 signing of McEliece ciphertext done in {end - start:.6f} sec.")
    

    with oqs.KeyEncapsulation("sntrup761") as kem:
        start = time.time()
        ntru_ciphertext, ntru_shared_secret = kem.encap_secret(ntru_pub)
      
        enc_key, enc_iv = derive_aes_keys(ntru_shared_secret)
    
        cipher = Cipher(algorithms.AES(enc_key), modes.CFB(enc_iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_falcon_sig = encryptor.update(falcon_signature) + encryptor.finalize()
        end = time.time()

    print(f"[*] sntrup761 encapsulation of Falcon signature done in {end - start:.6f} sec.")

    og_ci_data = kyber_ciphertext + mceliece_ciphertext + falcon_signature + ntru_ciphertext
    ci_data = str(kyber_ciphertext) + str(mceliece_ciphertext) + str(falcon_signature) + str(ntru_ciphertext)

    key_cipher_record={
        "data_id": data_id,
        "key_id": key_id,
        "cipher_data": {
            "kyber": encrypted_kyber_ct,
            "mceliece": mceliece_ciphertext,
            "Falcon_cipher": encrypted_falcon_sig,
            "Falcon_public_key":falcon_public_key,
            "ntru": ntru_ciphertext,
            "dilithium":" " 
        },
        "aes_bin":  encrypted_aes_key,
        "aes_iv":  aes_iv,
        "created_at": datetime.now(),
        "decoy_attached": False,
        "layers": 4,
        "user_id": user_id,
        "anomaly_detected_at": " "
    }
    try:
        Key_Cipher_collection.insert_one(key_cipher_record)
        print( "Record inserted successfully!")
    except Exception as e:
        print( f"Error: {str(e)}")

def split_bytes(combined_bytes):
    lengths = [2400, 13608, 1793,1763]
    parts = []
    start = 0
    for length in lengths:
        parts.append(combined_bytes[start:start+length])
        start += length
    return parts

def decrypt_layered(key,aes_iv, support_data, aes_ciphertext, ntru_ciphertext, mceliece_ciphertext, encrypted_falcon_sig, encrypted_kyber_ct,falcon_public_key_new):
    
    create_folder()
  
    Result = Clarify(key)
 
    kyber_priv, mceliece_priv, falcon_public_key,ntru_priv = split_bytes(Result)
   
    
    # === Step 5: sntrup761 Decapsulation ===
    with oqs.KeyEncapsulation("sntrup761", secret_key=ntru_priv) as kem:
        start = time.time()
        ntru_shared_secret = kem.decap_secret(ntru_ciphertext)
        end = time.time()
    print(f"[*] sntrup761 decapsulation done in {end - start:.6f} sec.")
    
    enc_key, enc_iv = derive_aes_keys(ntru_shared_secret)
    cipher = Cipher(algorithms.AES(enc_key), modes.CFB(enc_iv), backend=default_backend())
    decryptor = cipher.decryptor()
    falcon_signature = decryptor.update(encrypted_falcon_sig) + decryptor.finalize()
    
    # === Step 4: Falcon1024 Verification ===
    with oqs.Signature("Falcon-1024") as sig:
        start = time.time()
        falcon_valid = sig.verify(mceliece_ciphertext, falcon_signature, falcon_public_key)
        end = time.time()
    if not falcon_valid:
        print("[!] Falcon1024 signature verification failed!")
        return
    print(f"[*] Falcon1024 verified in {end - start:.6f} sec.")
    
    # === Step 3: McEliece Decapsulation ===
    with oqs.KeyEncapsulation("Classic-McEliece-460896f", secret_key=mceliece_priv) as kem:
        start = time.time()
        mceliece_shared_secret = kem.decap_secret(mceliece_ciphertext)
        end = time.time()
    print(f"[*] McEliece decapsulation done in {end - start:.6f} sec.")
    
    enc_key, enc_iv = derive_aes_keys(mceliece_shared_secret)
    cipher = Cipher(algorithms.AES(enc_key), modes.CFB(enc_iv), backend=default_backend())
    decryptor = cipher.decryptor()
    kyber_ciphertext = decryptor.update(encrypted_kyber_ct) + decryptor.finalize()
    
    # === Step 2: Kyber768 Decapsulation ===
    with oqs.KeyEncapsulation("Kyber768", secret_key=kyber_priv) as kem:
        start = time.time()
        kyber_shared_secret = kem.decap_secret(kyber_ciphertext)
        end = time.time()
    print(f"[*] Kyber768 decapsulation done in {end - start:.6f} sec.")
    
    encrypted_aes_key = support_data
    enc_key, enc_iv = derive_aes_keys(kyber_shared_secret)
    cipher = Cipher(algorithms.AES(enc_key), modes.CFB(enc_iv), backend=default_backend())
    decryptor = cipher.decryptor()
    aes_key = decryptor.update(encrypted_aes_key) + decryptor.finalize()
    
    # === Step 1: AES-256 Decryption ===
    
    start = time.time()
    decrypted_message = aes_decrypt(aes_ciphertext, aes_key, aes_iv)
    end = time.time()
    print(f"[*] AES-256 decryption done in {end - start:.6f} sec.")
    

    with open(os.path.join(output_dir, "Q-Defender_Decrypted.txt"), "wb") as f:
        f.write(decrypted_message)

    try:
        with open(os.path.join(output_dir, "a_og_input.txt"), "rb") as f1, \
             open(os.path.join(output_dir, "Q-Defender_Decrypted.txt"), "rb") as f2:
            original = f1.read()
            decrypted = f2.read()
            if original == decrypted:
                print("[✔] Original and decrypted messages match.")
            else:
                print("[✘] Mismatch between original and decrypted messages!")
    except FileNotFoundError:
        print("[!] Original input file not found. Cannot verify decryption.")    



