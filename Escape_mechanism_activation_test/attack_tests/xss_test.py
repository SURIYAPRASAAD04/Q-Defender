import requests
import random
import time
from rich.console import Console
from rich.table import Table
from rich.live import Live

console = Console()
BASE_URL = "http://localhost:5000"

def get_xss_attack():
    payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(document.cookie)"
    ]
    return {
        'url': f"{BASE_URL}/submit_message",
        'method': 'POST',
        'data': {'manual_message': random.choice(payloads)},
        'headers': {'X-ATTACK-TYPE': 'XSS'}
    }

def test_xss():
    console.print("\n[bold red]XSS TEST[/bold red]")
    table = Table(title="XSS Attack Progress")
    table.add_column("Attempt")
    table.add_column("Status")
    table.add_column("Protocol State")
    
    activated = False
    activation_time = None
    
    with Live(table, refresh_per_second=4) as live:
        for i in range(1, 21):  # 20 attempts
            attack = get_xss_attack()
            try:
                response = requests.post(
                    attack['url'],
                    data=attack['data'],
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
                
            time.sleep(0.5)
    
    console.print("\n[bold]RESULTS:[/bold]")
    if activated:
        console.print(f"[green]SUCCESS[/green]: Protocol activated after {activation_time} attempts")
    else:
        console.print("[red]FAILURE[/red]: XSS attack not detected")

if __name__ == "__main__":
    test_xss()