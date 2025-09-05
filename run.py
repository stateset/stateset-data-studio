#!/usr/bin/env python3
import subprocess
import os
import sys
import time
import signal
import atexit

# Define the processes list to keep track of them
processes = []

def cleanup():
    """Cleanup function to kill all child processes on exit"""
    for process in processes:
        if process.poll() is None:  # If the process is still running
            try:
                process.terminate()
                process.wait(timeout=1)
            except:
                process.kill()

# Register the cleanup function to be called on exit
atexit.register(cleanup)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nReceived signal to terminate. Shutting down services...")
    cleanup()
    sys.exit(0)

# Set up signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_mock_vllm():
    """Start the mock vLLM server for development"""
    print("Starting mock vLLM server...")
    # Make sure we're in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    if not os.path.exists("mock_vllm_server.py"):
        print("Warning: mock_vllm_server.py not found, skipping mock vLLM server")
        return None
    
    vllm_cmd = [sys.executable, "mock_vllm_server.py"]
    vllm_process = subprocess.Popen(
        vllm_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1
    )
    processes.append(vllm_process)
    return vllm_process

def start_backend():
    """Start the FastAPI backend server"""
    print("Starting the backend server...")
    # Make sure we're in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Create and initialize the database if needed
    print("Initializing database...")
    if os.path.exists("synthetic_data_api.db"):
        print("Database already exists, using existing database")
    
    # Run the backend app from the backend module, not the root app.py
    backend_cmd = ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    backend_process = subprocess.Popen(
        backend_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1
    )
    processes.append(backend_process)
    return backend_process

def start_frontend():
    """Start the React frontend development server"""
    print("Starting the frontend server...")
    
    # Make sure we're in the project root directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Check if the frontend directory exists
    if not os.path.exists("frontend"):
        print("Error: frontend directory not found!")
        return None
    
    # Change to the frontend directory
    os.chdir("frontend")
    
    # Verify if node_modules exists, if not run npm install
    if not os.path.exists("node_modules"):
        print("Node modules not found, running npm install...")
        subprocess.run(["npm", "install"], check=True)
    
    frontend_cmd = ["npm", "start"]
    frontend_process = subprocess.Popen(
        frontend_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1
    )
    processes.append(frontend_process)
    os.chdir("..")
    return frontend_process

def main():
    """Main function to start all services"""
    # Make sure we're in the project root directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("Starting StateSet Data Studio...")
    print("Project directory:", os.getcwd())
    
    # Check for required packages
    print("Checking required packages...")
    try:
        import synthetic_data_kit
        print("Synthetic Data Kit is installed.")
    except ImportError:
        print("Installing Synthetic Data Kit package...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"], check=True)
    
    # Check if synthetic-data-kit command is available
    try:
        subprocess.run(["synthetic-data-kit", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("Synthetic Data Kit command is available.")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Installing Synthetic Data Kit command-line tool...")
        subprocess.run([sys.executable, "-m", "pip", "install", "synthetic-data-kit"], check=True)
    
    # Ensure the necessary directories exist
    print("Creating necessary directories...")
    os.makedirs("data/uploads", exist_ok=True)
    os.makedirs("data/output", exist_ok=True)
    os.makedirs("data/generated", exist_ok=True)
    os.makedirs("data/cleaned", exist_ok=True)
    os.makedirs("data/final", exist_ok=True)
    os.makedirs("data/pdf", exist_ok=True)
    os.makedirs("data/docx", exist_ok=True)
    os.makedirs("data/html", exist_ok=True)
    os.makedirs("data/txt", exist_ok=True)
    os.makedirs("data/youtube", exist_ok=True)
    os.makedirs("configs", exist_ok=True)
    
    # Create default config if it doesn't exist
    if not os.path.exists("configs/config.yaml"):
        print("Creating default configuration...")
        default_config = {
            "vllm": {
                "api_base": "http://localhost:8001/v1",  # Changed port to 8001 for mock vLLM server
                "model": "meta-llama/Llama-3.3-70B-Instruct"
            },
            "generation": {
                "temperature": 0.7,
                "chunk_size": 4000,
                "num_pairs": 25
            },
            "curate": {
                "threshold": 7.0,
                "batch_size": 8
            }
        }
        import yaml
        with open("configs/config.yaml", "w") as f:
            yaml.dump(default_config, f)
    else:
        # Update existing config to point to mock vLLM server
        try:
            import yaml
            with open("configs/config.yaml", "r") as f:
                existing_config = yaml.safe_load(f)
            
            # Update the vLLM API base URL if it's pointing to port 8000
            if "vllm" in existing_config and "api_base" in existing_config["vllm"]:
                current_api_base = existing_config["vllm"]["api_base"]
                if "localhost:8000" in current_api_base:
                    existing_config["vllm"]["api_base"] = current_api_base.replace("localhost:8000", "localhost:8001")
                    print("Updating config to use mock vLLM server on port 8001")
                    with open("configs/config.yaml", "w") as f:
                        yaml.dump(existing_config, f)
        except Exception as e:
            print(f"Warning: Could not update config file: {e}")
    
    # Start mock vLLM server first
    print("\n=== Starting Mock vLLM Server ===")
    vllm_process = start_mock_vllm()
    if vllm_process:
        print("Mock vLLM server started")
        # Give it time to initialize
        print("Waiting for mock vLLM server to initialize...")
        time.sleep(2)
    
    # Start backend
    print("\n=== Starting Backend ===")
    backend_process = start_backend()
    if backend_process:
        print("Backend server started on http://localhost:8000")
    else:
        print("Failed to start backend server!")
        return
    
    # Wait a bit for the backend to initialize
    print("Waiting for backend to initialize...")
    time.sleep(5)
    
    # Start frontend
    print("\n=== Starting Frontend ===")
    frontend_process = start_frontend()
    if frontend_process:
        print("Frontend server started on http://localhost:3000")
    else:
        print("Failed to start frontend server!")
        # Continue anyway as the backend can still be used via API

    # Print logs from all processes
    try:
        print("\n=== Services Started Successfully ===")
        print("- Frontend: http://localhost:3000")
        print("- Backend API: http://localhost:8000")
        print("\nPress Ctrl+C to stop all services\n")
        
        while True:
            # Check if processes are still running
            if vllm_process and vllm_process.poll() is not None:
                print("Mock vLLM server terminated unexpectedly")
                stderr = vllm_process.stderr.read()
                if stderr:
                    print(f"Mock vLLM error: {stderr}")
                break
                
            if backend_process.poll() is not None:
                print("Backend process terminated unexpectedly")
                # Print error output if available
                stderr = backend_process.stderr.read()
                if stderr:
                    print(f"Backend error: {stderr}")
                break
                
            if frontend_process and frontend_process.poll() is not None:
                print("Frontend process terminated unexpectedly")
                stderr = frontend_process.stderr.read()
                if stderr:
                    print(f"Frontend error: {stderr}")
                break
            
            # Read and print vLLM output if running
            if vllm_process:
                vllm_out = vllm_process.stdout.readline().strip()
                if vllm_out:
                    print(f"[vLLM] {vllm_out}")
                
                vllm_err = vllm_process.stderr.readline().strip()
                if vllm_err:
                    print(f"[vLLM ERROR] {vllm_err}")
                
            # Read and print backend output
            backend_out = backend_process.stdout.readline().strip()
            if backend_out:
                print(f"[Backend] {backend_out}")
                
            backend_err = backend_process.stderr.readline().strip()
            if backend_err:
                print(f"[Backend ERROR] {backend_err}")
                
            # Read and print frontend output if running
            if frontend_process:
                frontend_out = frontend_process.stdout.readline().strip()
                if frontend_out:
                    print(f"[Frontend] {frontend_out}")
                    
                frontend_err = frontend_process.stderr.readline().strip()
                if frontend_err:
                    print(f"[Frontend ERROR] {frontend_err}")
                
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Shutting down services...")
    finally:
        cleanup()

if __name__ == "__main__":
    main()