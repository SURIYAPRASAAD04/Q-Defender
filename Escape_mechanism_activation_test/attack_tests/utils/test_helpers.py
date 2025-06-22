from rich.console import Console
from rich.table import Table
import time, random, requests
from rich.live import Live

console = Console()

def run_attack_test(attack_func, base_url, test_name, duration=60):
    console.print(f"\n[bold red]STARTING {test_name} TEST[/bold red]")
    
    table = Table(title=f"{test_name} Attack Progress")
    table.add_column("Time")
    # table.add_column("Status")
    table.add_column("Attack")
    
    start_time = time.time()
    activated = False
    activation_time = None
    
    with Live(table, refresh_per_second=4) as live:
        while time.time() - start_time < duration and not activated:
            # Execute attack
            attack = attack_func(base_url)
            try:
                response = requests.request(
                    attack['method'],
                    attack['url'],
                    data=attack.get('data'),
                    files=attack.get('files'),
                    headers=attack.get('headers', {}),
                    timeout=attack.get('timeout', 1)
                )
                # status = response.status_code
            except:
                status = "FAILED"
            
            # Check activation
            try:
                check_response = requests.get(base_url, timeout=1)
                activated = "Quantum Escape Protocol" in check_response.text
            except:
                activated = False
            
            if activated and not activation_time:
                activation_time = time.time() - start_time
            
            table.add_row(
                f"{time.time()-start_time:.1f}s",
                "[blink red]ACTIVATED[/blink red]" 
            )
            
            time.sleep(0.5)
    
    return activated, activation_time

def print_test_result(test_name, success, activation_time):
    console.print(f"\n[bold]{test_name} RESULTS:[/bold]")
    if success:
        console.print(f"[green]SUCCESS[/green]: Protocol activated after {activation_time:.1f}s")
    else:
        console.print("[red]FAILURE[/red]: Protocol not activated")