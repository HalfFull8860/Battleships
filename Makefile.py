import concurrent.futures
import subprocess

commands = [
    "python -m flask run",
    "java -cp bin Mainer"
]

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"Command: {cmd}\nReturn code: {result.returncode}\nOutput:\n{result.stdout}\nError:\n{result.stderr}")
    return result.returncode

if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(run_command, cmd) for cmd in commands]
        for future in concurrent.futures.as_completed(futures):
            future.result()