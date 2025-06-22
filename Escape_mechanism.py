import os
import random
from datetime import datetime
from pymongo import MongoClient
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import firebase_admin
from firebase_admin import credentials, firestore
import oqs
import time
from PQC_layers import create_folder, aes_decrypt, derive_aes_keys
import traceback


mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["Q-Defender"]
collection_AES = db["AES encryption"]
collection_keyvault = db["Key Vault"]
collection_keychipher = db["Key Cipher"]


cred = credentials.Certificate("q-defender-firebase-adminsdk-fbsvc-756017b167.json")
firebase_admin.initialize_app(cred)
firestore_db = firestore.client()


output_dir = "folder_sec_inst"
os.makedirs(output_dir, exist_ok=True)

def split_bytes_anomaly(combined_bytes):
    """Split combined bytes into specific length components"""
    if not isinstance(combined_bytes, bytes):
        raise TypeError("combined_bytes must be bytes type")
    
    lengths = [2400, 13608, 1793, 1763, 1952]
    if len(combined_bytes) != sum(lengths):
        raise ValueError(f"Combined bytes length {len(combined_bytes)} doesn't match expected {sum(lengths)}")
    
    parts = []
    start = 0
    for length in lengths:
        parts.append(combined_bytes[start:start+length])
        start += length
    return parts

def generate_decoy_positions(data_size, num_fragments=2):
    """Generate random positions for decoy insertion"""
    if data_size < 1024: 
        raise ValueError("Data size too small for decoy insertion")
    
    min_gap = 512
    max_pos = data_size - min_gap
    if max_pos <= min_gap:
        raise ValueError("Insufficient data size for decoy positions")
    
    positions = sorted(random.sample(range(min_gap, max_pos), num_fragments))
    return positions

def encrypt_position(position, key):
    """Encrypt decoy position using AES-CBC"""
    if not isinstance(position, int) or position < 0:
        raise ValueError("Position must be positive integer")
    if len(key) not in [16, 24, 32]:
        raise ValueError("Invalid key length for AES")

    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(position.to_bytes(4, 'big')) + padder.finalize()
    
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return iv + ciphertext

def decrypt_position(ciphertext, key):
    """Decrypt decoy position"""
    if len(ciphertext) < 32: 
        raise ValueError("Invalid ciphertext length")
    if len(key) not in [16, 24, 32]:
        raise ValueError("Invalid key length for AES")

    iv = ciphertext[:16]
    actual_ciphertext = ciphertext[16:]
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    decrypted_padded = decryptor.update(actual_ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
    
    return int.from_bytes(decrypted, 'big')

def fragment_and_inject_decoys(data, data_id, user_id):
    """Fragment data and inject decoys with validation"""
    if not isinstance(data, bytes):
        raise TypeError("Data must be bytes type")
    if not data_id or not user_id:
        raise ValueError("Missing data_id or user_id")

    position_key = os.urandom(32)
    data_size = len(data)
    
    try:
        decoy_positions = generate_decoy_positions(data_size)
    except ValueError as e:
        raise ValueError(f"Cannot generate decoy positions: {str(e)}")

   
    split_point = data_size // 2
    fragment1 = data[:split_point]
    fragment2 = data[split_point:]
    

    fragments = []
    
    for i, fragment in enumerate([fragment1, fragment2]):
        try:
            decoy = os.urandom(512)
            position = decoy_positions[i]
            enc_position = encrypt_position(position, position_key)
            
            fragment_with_decoy = (
                fragment[:position] +
                decoy +
                fragment[position:] +
                position_key
            )
            fragments.append((fragment_with_decoy, enc_position))
        except Exception as e:
            raise RuntimeError(f"Failed to process fragment {i+1}: {str(e)}")

  
    try:
        
        update_result = collection_keyvault.update_one(
            {"data_id": data_id},
            {"$set": {
                "Key": fragments[0][0],
                "decoy_attached": True,
                "layers": 2,
                "fragmented_at": datetime.now(),
                "anomaly_detected_at": datetime.now()
            }}
        )
        if update_result.matched_count == 0:
            raise ValueError(f"No document found with data_id: {data_id}")

        
        firestore_db.collection("Q-Defender").add({
            "key_id": data_id,
            "data_id": data_id,
            "user_id": user_id,
            "key": fragments[1][0],
            "decoy_attached": True,
            "layers": 2,
            "fragmented_at": datetime.now(),
            "anomaly_detected_at": datetime.now(),
            "position_enc_data": fragments[1][1]
        })

        
        collection_AES.update_one(
            {"data_id": data_id},
            {"$set": {
                "anomaly_triggered": True,
                "decoy_attached": True,
                "layers": 2,
                "status": "Fragmented",
                "anomaly_detected_at": datetime.now(),
                "position_size_enc_data_added": True,
                "anomaly_detected": True,
                "position_enc_data": fragments[0][1]
            }}
        )
    except Exception as e:
        raise RuntimeError(f"Database operation failed: {str(e)}")

    return True

def reconstruct_data(data_id):
    """Reconstruct data by removing decoys with enhanced position validation"""
    try:
        
        mongo_doc = collection_keyvault.find_one({"data_id": data_id})
        if not mongo_doc:
            raise ValueError(f"No Key Vault found for data_id: {data_id}")
        
        fragment1 = mongo_doc["Key"]
        if not isinstance(fragment1, bytes):
            raise TypeError("Fragment1 must be bytes")

        mongo_doc_enc = collection_AES.find_one({"data_id": data_id})
        if not mongo_doc_enc:
            raise ValueError(f"No AES document found for data_id: {data_id}")
        
        pos_enc1 = mongo_doc_enc["position_enc_data"]
        if not isinstance(pos_enc1, bytes):
            raise TypeError("Position encryption data must be bytes")

        
        firestore_docs = list(firestore_db.collection("Q-Defender").where("data_id", "==", data_id).get())
        if not firestore_docs:
            raise ValueError(f"No Firestore document found for data_id: {data_id}")
        
        firestore_data = firestore_docs[0].to_dict()
        fragment2 = firestore_data.get("key")
        pos_enc2 = firestore_data.get("position_enc_data")
        
        if not all([fragment2, pos_enc2]):
            raise ValueError("Missing required fields in Firestore document")

       
        key1 = fragment1[-32:]
        key2 = fragment2[-32:]
        
        pos1 = decrypt_position(pos_enc1, key1)
        pos2 = decrypt_position(pos_enc2, key2)

        
        def validate_position(pos, fragment, frag_name):
            if pos < 0:
                raise ValueError(f"Negative position in {frag_name}")
            if pos + 512 > len(fragment) - 32:
                print(f"\n[!] Invalid position in {frag_name}:")
                print(f"- Position: {pos}")
                print(f"- Fragment length: {len(fragment)}")
                print(f"- Available space: {len(fragment) - 32}")
                print(f"- Required space: {pos + 512}")
                raise ValueError(f"Decoy position exceeds fragment bounds in {frag_name}")
            return pos

        pos1 = validate_position(pos1, fragment1, "fragment1")
        pos2 = validate_position(pos2, fragment2, "fragment2")

        
        reconstructed = (
            fragment1[:pos1] +
            fragment1[pos1 + 512:-32] +
            fragment2[:pos2] +
            fragment2[pos2 + 512:-32]
        )
        
        return reconstructed

    except Exception as e:
        raise RuntimeError(f"Reconstruction failed: {str(e)}")
    
def escape_mechanism(Key_Vault, Key_Cipher, data_id, user_id):
    """Handle anomaly by fragmenting and injecting decoys with enhanced error handling"""
    try:
       
        if not all([Key_Vault, Key_Cipher, data_id, user_id]):
            raise ValueError("Missing required parameters (Key_Vault, Key_Cipher, data_id, or user_id)")
        
        print("\n=== Starting Escape Mechanism ===")
        print(f"Processing data_id: {data_id} for user: {user_id}")

       
        if not isinstance(Key_Vault, dict) or "Key" not in Key_Vault:
            raise ValueError("Key_Vault must be a dictionary containing 'Key'")
        
        key_dict = Key_Vault["Key"]
        if not isinstance(key_dict, bytes):
            raise TypeError(f"Key_Vault['Key'] must be bytes, got {type(key_dict)}")
        
        print(f"Key material length: {len(key_dict)} bytes")

        
        if not isinstance(Key_Cipher, dict) or "cipher_data" not in Key_Cipher:
            raise ValueError("Key_Cipher must be a dictionary containing 'cipher_data'")
        
        cipher_data = Key_Cipher["cipher_data"]
        if not isinstance(cipher_data, dict) or "ntru" not in cipher_data:
            raise ValueError("cipher_data must contain 'ntru' ciphertext")
        
        ntru_ciphertext = cipher_data["ntru"]
        if not isinstance(ntru_ciphertext, bytes):
            raise TypeError("NTRU ciphertext must be bytes")

        print(f"NTRU ciphertext length: {len(ntru_ciphertext)} bytes")

        
        print("Generating Dilithium keys...")
        with oqs.Signature("Dilithium3") as sig:
            try:
                dilithium_pub = sig.generate_keypair()
                dilithium_priv = sig.export_secret_key()
                print(f"[*] Generated Dilithium public key (length: {len(dilithium_pub)})")
                
                
                with oqs.Signature("Dilithium3", secret_key=dilithium_priv) as signer:
                    print("[*] Signing NTRU ciphertext...")
                    dilithium_signature = signer.sign(ntru_ciphertext)
                    print(f"[*] Generated signature (length: {len(dilithium_signature)})")
            except Exception as e:
                raise RuntimeError(f"Digital signature generation failed: {str(e)}")

        
        print(f"Key_Vault['Key'] length: {len(key_dict)}")       
        print(f"Dilithium public key length: {len(dilithium_pub)}")  

        full_key_data = key_dict + dilithium_pub
        expected_length = 2400 + 13608 + 1793 + 1763 + 1952  
        if len(full_key_data) != expected_length:
            raise ValueError(f"Combined key length mismatch. Expected {expected_length}, got {len(full_key_data)}")

        
        print("[*] Updating Key Cipher in database...")
        try:
            update_result = collection_keychipher.update_one(
                {"data_id": data_id},
                {"$set": {
                    "cipher_data": {**cipher_data, "dilithium": dilithium_signature},
                    "complete": full_key_data
                }}
            )
            if update_result.matched_count == 0:
                raise ValueError(f"No document found with data_id: {data_id}")
            print("[✔] Database update successful")
        except Exception as e:
            raise RuntimeError(f"Database update failed: {str(e)}")

        
        print("[*] Fragmenting data and injecting decoys...")
        try:
            if not fragment_and_inject_decoys(full_key_data, data_id, user_id):
                raise RuntimeError("Fragment and inject operation returned False")
            print("[✔] Data fragmentation and decoy injection complete")
        except Exception as e:
            raise RuntimeError(f"Fragmentation failed: {str(e)}")

        print("\n[✔] Escape mechanism completed successfully!")
        return True

    except Exception as e:
        error_msg = f"\n[✘] Escape mechanism failed at step: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        raise RuntimeError(error_msg) from e
    
def escape_mechanism_reconstruction(data_id, aes_iv, support_data, aes_ciphertext, 
                                  ntru_ciphertext, mceliece_ciphertext, 
                                  encrypted_falcon_sig, encrypted_kyber_ct,
                                  falcon_public_key, dilithium_signature):
    """Full reconstruction and decryption workflow with comprehensive validation"""
    try:
        
        if not all([data_id, aes_iv, support_data, aes_ciphertext, ntru_ciphertext,
                   mceliece_ciphertext, encrypted_falcon_sig, encrypted_kyber_ct,
                   falcon_public_key, dilithium_signature]):
            raise ValueError("Missing required reconstruction parameters")

        print("\n=== Starting Reconstruction ===")
        
        
        reconstructed_data = reconstruct_data(data_id)
        print(f"Reconstructed data length: {len(reconstructed_data)} bytes")
        
       
        try:
            kyber_priv, mceliece_priv, _, ntru_priv, dilithium_public_key = split_bytes_anomaly(reconstructed_data)
        except ValueError as e:
            raise ValueError(f"Key splitting failed: {str(e)}")
        
        print(f"Component keys extracted - Dilithium public key length: {len(dilithium_public_key)}")

        # ===== 1. Dilithium Signature Verification =====
        with oqs.Signature("Dilithium3") as verifier:
            start = time.time()
            is_valid = verifier.verify(ntru_ciphertext, dilithium_signature, dilithium_public_key)
            end = time.time()
            
            if not is_valid:
                print("Dilithium3 signature verification failed!")
                return None
            print(f"Dilithium3 verification successful ({end-start:.4f}s)")

        # ===== 2. NTRU Decapsulation =====
        with oqs.KeyEncapsulation("sntrup761", secret_key=ntru_priv) as kem:
            start = time.time()
            ntru_shared_secret = kem.decap_secret(ntru_ciphertext)
            end = time.time()
            if not ntru_shared_secret:
                raise ValueError("NTRU decapsulation failed")
            print(f"sntrup761 decapsulation done ({end-start:.4f}s)")

        # ===== 3. Decrypt Falcon Signature =====
        enc_key, enc_iv = derive_aes_keys(ntru_shared_secret)
        cipher = Cipher(algorithms.AES(enc_key), modes.CFB(enc_iv), backend=default_backend())
        decryptor = cipher.decryptor()
        falcon_signature = decryptor.update(encrypted_falcon_sig) + decryptor.finalize()

        # ===== 4. Falcon Signature Verification =====
        with oqs.Signature("Falcon-1024") as verifier:
            start = time.time()
            is_valid = verifier.verify(mceliece_ciphertext, falcon_signature, falcon_public_key)
            end = time.time()
            
            if not is_valid:
                print("Falcon1024 signature verification failed!")
                return None
            print(f"Falcon1024 verification successful ({end-start:.4f}s)")

        # ===== 5. McEliece Decapsulation =====
        with oqs.KeyEncapsulation("Classic-McEliece-460896f", secret_key=mceliece_priv) as kem:
            start = time.time()
            mceliece_shared_secret = kem.decap_secret(mceliece_ciphertext)
            end = time.time()
            if not mceliece_shared_secret:
                raise ValueError("McEliece decapsulation failed")
            print(f"McEliece decapsulation done ({end-start:.4f}s)")

        # ===== 6. Decrypt Kyber Ciphertext =====
        enc_key, enc_iv = derive_aes_keys(mceliece_shared_secret)
        cipher = Cipher(algorithms.AES(enc_key), modes.CFB(enc_iv), backend=default_backend())
        decryptor = cipher.decryptor()
        kyber_ciphertext = decryptor.update(encrypted_kyber_ct) + decryptor.finalize()

        # ===== 7. Kyber Decapsulation =====
        with oqs.KeyEncapsulation("Kyber768", secret_key=kyber_priv) as kem:
            start = time.time()
            kyber_shared_secret = kem.decap_secret(kyber_ciphertext)
            end = time.time()
            if not kyber_shared_secret:
                raise ValueError("Kyber decapsulation failed")
            print(f"Kyber768 decapsulation done ({end-start:.4f}s)")

        # ===== 8. Decrypt AES Key =====
        enc_key, enc_iv = derive_aes_keys(kyber_shared_secret)
        cipher = Cipher(algorithms.AES(enc_key), modes.CFB(enc_iv), backend=default_backend())
        decryptor = cipher.decryptor()
        aes_key = decryptor.update(support_data) + decryptor.finalize()

        # ===== 9. Final AES Decryption =====
        start = time.time()
        decrypted_message = aes_decrypt(aes_ciphertext, aes_key, aes_iv)
        end = time.time()
        if not decrypted_message:
            raise ValueError("AES decryption failed")
        print(f"AES-256 decryption done ({end-start:.4f}s)")

        # Save decrypted message
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "Q-Defender_Decrypted.txt")
        with open(output_path, "wb") as f:
            f.write(decrypted_message)
        
        print(f"\nReconstruction complete! Decrypted message saved to {output_path}")
        return decrypted_message

    except Exception as e:
        print(f"\nReconstruction failed with error: {str(e)}")
        traceback.print_exc()
        return None