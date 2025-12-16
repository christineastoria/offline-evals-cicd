"""Run all evaluations in sequence"""
import os
import subprocess
import sys

def run_eval(script_path: str):
    """Run an evaluation script"""
    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=False
    )
    
    if result.returncode != 0:
        return False
    
    return True

if __name__ == "__main__":
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    evals = [
        os.path.join(script_dir, "run_portfolio_eval.py"),
        os.path.join(script_dir, "run_market_eval.py")
    ]
    
    results = {}
    for eval_script in evals:
        script_name = os.path.basename(eval_script)
        results[script_name] = run_eval(eval_script)
    
    all_passed = all(results.values())
    
    if not all_passed:
        sys.exit(1)

