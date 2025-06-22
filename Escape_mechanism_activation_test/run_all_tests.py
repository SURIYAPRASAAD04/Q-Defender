import subprocess
from rich.console import Console

console = Console()

tests = [
    "sql_injection_test.py",
    "xss_test.py",
    "brute_force_test.py",
    "malicious_file_test.py",
    "slowloris_test.py"
]

def run_all_tests():
    console.print("[bold green]RUNNING COMPLETE QUANTUM ESCAPE TEST SUITE[/bold green]")
    
    results = {}
    for test in tests:
        console.print(f"\n[bold]Running {test}...[/bold]")
        try:
            result = subprocess.run(
                ["python", f"attack_tests/{test}"],
                check=True,
                capture_output=True,
                text=True
            )
            console.print(result.stdout)
            results[test] = "PASSED"
        except subprocess.CalledProcessError as e:
            console.print(f"[red]{e.stderr}[/red]")
            results[test] = "FAILED"
    
    console.print("\n[bold]TEST SUMMARY:[/bold]")
    for test, status in results.items():
        color = "green" if status == "PASSED" else "red"
        console.print(f"{test}: [{color}]{status}[/{color}]")

if __name__ == "__main__":
    run_all_tests()