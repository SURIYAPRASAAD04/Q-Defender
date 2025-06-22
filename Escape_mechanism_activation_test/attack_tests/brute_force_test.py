import requests
import random
import time
from rich.console import Console
from rich.table import Table
from rich.live import Live

console = Console()
BASE_URL = "http://localhost:5000"

def get_brute_force_attack():
    endpoints = ['/process_new', '/decryption', '/download_decoded']
    return {
        'url': f"{BASE_URL}{random.choice(endpoints)}",
        'method': 'POST' if random.random() > 0.5 else 'GET',
        'data': {'dummy': 'A'*10000},
        'headers': {'X-ATTACK-TYPE': 'BRUTE', 'User-Agent': 'MALICIOUS-BOT'}
    }

def test_brute_force():
    console.print("\n[bold red]BRUTE FORCE TEST[/bold red]")
    table = Table(title="Brute Force Attack Progress")
    table.add_column("Attempt")
    table.add_column("Status")
    table.add_column("Protocol State")
    
    activated = False
    activation_time = None
    
    with Live(table, refresh_per_second=4) as live:
        for i in range(1, 101):  # 100 attempts
            attack = get_brute_force_attack()
            try:
                if attack['method'] == 'POST':
                    response = requests.post(
                        attack['url'],
                        data=attack['data'],
                        headers=attack['headers'],
                        timeout=0.5
                    )
                else:
                    response = requests.get(
                        attack['url'],
                        headers=attack['headers'],
                        timeout=0.5
                    )
                status = response.status_code
            except:
                status = "FAILED"
            
            # Check if protocol activated
            check = requests.get(BASE_URL, timeout=1)
            activated = "Quantum Escape Protocol" in check.text
            
            table.add_row(
                str(i),
                str(status),
                "[blink red]ACTIVATED[/blink red]" if activated else "normal"
            )
            
            if activated:
                activation_time = i
                break
                
            time.sleep(0.1)
    
    console.print("\n[bold]RESULTS:[/bold]")
    if activated:
        console.print(f"[green]SUCCESS[/green]: Protocol activated after {activation_time} attempts")
    else:
        console.print("[red]FAILURE[/red]: Brute force attack not detected")

if __name__ == "__main__":
    test_brute_force()