import requests
import time
from rich.console import Console
from rich.table import Table
from rich.live import Live

console = Console()
BASE_URL = "http://localhost:5000"

def get_malicious_file_attack():
    return {
        'url': f"{BASE_URL}/upload_file",
        'method': 'POST',
        'files': {'file': ('exploit.exe', b'MZ\x90\x00\x03...')},
        'headers': {'X-ATTACK-TYPE': 'MALFILE'}
    }

def test_malicious_file():
    console.print("\n[bold red]MALICIOUS FILE TEST[/bold red]")
    table = Table(title="Malicious File Upload Progress")
    table.add_column("Attempt")
    table.add_column("Status")
    table.add_column("Protocol State")
    
    activated = False
    activation_time = None
    
    with Live(table, refresh_per_second=4) as live:
        for i in range(1, 11):  # 10 attempts
            attack = get_malicious_file_attack()
            try:
                response = requests.post(
                    attack['url'],
                    files=attack['files'],
                    headers=attack['headers'],
                    timeout=1
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
                
            time.sleep(1)
    
    console.print("\n[bold]RESULTS:[/bold]")
    if activated:
        console.print(f"[green]SUCCESS[/green]: Protocol activated after {activation_time} attempts")
    else:
        console.print("[red]FAILURE[/red]: Malicious file not detected")

if __name__ == "__main__":
    test_malicious_file()