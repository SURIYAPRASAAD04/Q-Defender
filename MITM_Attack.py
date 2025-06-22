import time
import random
import threading
import socket
from rich.console import Console
from rich.panel import Panel
import socket
import threading
from datetime import datetime
from bson import BSON
import random
from rich import box
from rich.align import Align

class MongoActivityLogger:
    def __init__(self):
        self.proxy_port = 27018
        self.real_mongo_port = 27017
        self.running = True

    def log_operation(self, data):
        try:
            op = BSON(data[16:]).decode()
            op_type = list(op.keys())[0]
            collection = op.get(op_type, "unknown")
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {op_type.upper()} operation detected on {collection}")
            
            print(f"  Operation size: {len(data)} bytes")
            
        except Exception as e:
            print(f"[Activity Log] Protocol error: {str(e)}")

    def handle_client(self, client_sock):
        mongo_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mongo_sock.connect(("localhost", self.real_mongo_port))
        
        try:
            while self.running:
                data = client_sock.recv(4096)
                if not data: break
                
                self.log_operation(data)
                mongo_sock.sendall(data)
                
                response = mongo_sock.recv(4096)
                if response:
                    client_sock.sendall(response)
                    
        finally:
            client_sock.close()
            mongo_sock.close()

    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("0.0.0.0", self.proxy_port))
        sock.listen(5)
        print(f"\nMongoDB Activity Logger started on port {self.proxy_port}")
        print("Monitoring operations without displaying content...\n")
        
        while self.running:
            client_sock, _ = sock.accept()
            threading.Thread(
                target=self.handle_client,
                args=(client_sock,),
                daemon=True
            ).start()

console = Console()
TARGET_ENDPOINT = "http://127.0.0.1:5000"

class StealthSecurityScanner:
    def __init__(self):
        self.running = True
        self.message_count = 0
        self.max_messages = random.randint(5, 10)
        self.security_checks = self._get_security_check_message()

    def _get_security_check_message(self):
        return f"Intercepting data transmissions at {random.choices(['/decryption', '/managedata'], weights=[8, 2])[0]}"

    def _display_scan_status(self, message):
        timestamp = time.strftime('%H:%M:%S')
        console.print(f"[{timestamp}] {message}", style="dim cyan")
        self.message_count += 1

    def _display_mitm_banner(self):
        banner = Panel(
            Align.center("[bold red]MAN-IN-THE-MIDDLE ATTACK[/bold red]", vertical="middle"),
            width=170,
            box=box.ROUNDED,
            border_style="red"
        )
        console.print(banner)

    def _display_attack_intro(self):
        intro = Panel(
            Align.left("[bold]MITM Simulation On a system[/bold]\nAttack simulation\nChecking for weak links..."),
            width=170,
            box=box.ROUNDED,
            border_style="cyan"
        )
        console.print(intro)

    def _simulate_scan(self):
        for _ in range(15):
            time.sleep(random.uniform(0.3, 1.0))
            self._display_scan_status(self._get_security_check_message())

    def run_scan(self):
        self._display_mitm_banner()
        self._display_attack_intro()

        scan_thread = threading.Thread(target=self._simulate_scan, daemon=True)
        scan_thread.start()
        
        while scan_thread.is_alive() and self.message_count < self.max_messages:
            time.sleep(0.1)

if __name__ == "__main__":
    scanner = StealthSecurityScanner()
    scan_thread = threading.Thread(target=scanner.run_scan, daemon=True)
    scan_thread.start()

    try:
        while scan_thread.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        scanner.running = False
        console.print("\n[red]Security scan aborted[/red]")