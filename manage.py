#!/usr/bin/env python3

import argparse
import subprocess
import sys
import os
import time
import socket
from pathlib import Path
import shutil

# Paths
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / '.env'
DOCKER_COMPOSE_FILE = BASE_DIR / 'docker-compose.services.yml'
VENV_DIR = BASE_DIR / '.venv'

def run_command(command, cwd=None, env=None):
    """Run a system command."""
    result = subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        env=env or os.environ.copy()
    )
    if result.returncode != 0:
        sys.exit(result.returncode)

def check_python_version():
    """Check if Python 3.8 or higher is installed."""
    if sys.version_info < (3, 8):
        print("Python 3.8 or higher is required.")
        sys.exit(1)

def create_virtualenv():
    """Create a Python virtual environment."""
    if not VENV_DIR.exists():
        print("Creating virtual environment...")
        try:
            import venv
            venv.create(VENV_DIR, with_pip=True)
            print(f"Virtual environment created at {VENV_DIR}")
        except Exception as e:
            print(f"Failed to create virtual environment: {e}")
            sys.exit(1)
    else:
        print("Virtual environment already exists.")

def activate_virtualenv():
    """Activate the Python virtual environment."""
    if VENV_DIR.exists():
        activate_script = VENV_DIR / ('Scripts' if os.name == 'nt' else 'bin') / 'activate_this.py'
        if activate_script.exists():
            with open(activate_script) as f:
                code = compile(f.read(), str(activate_script), 'exec')
                exec(code, {'__file__': str(activate_script)})
        else:
            print("Cannot find activate_this.py. Please ensure the virtual environment was created correctly.")
            sys.exit(1)
    else:
        print("Virtual environment not found. Please create it using 'create-venv' command.")
        sys.exit(1)

def install():
    """Install project dependencies using pip."""
    print("Installing dependencies...")
    run_command(f"poetry install")

def validate_env():
    """Validate the .env file."""
    if not ENV_FILE.exists():
        raise Exception(".env file not found. Please create it.")
    else:
        print(".env file already exists.")

def start_services():
    """Start required services with Docker Compose."""
    if not DOCKER_COMPOSE_FILE.exists():
        raise Exception("docker-compose.services.yml not found. Please create it.")
    run_command(f"docker-compose -f {DOCKER_COMPOSE_FILE} up -d postgres redis")

def stop_services():
    """Stop services started by Docker Compose."""
    if DOCKER_COMPOSE_FILE.exists():
        print("Stopping services with Docker Compose...")
        run_command(f"docker-compose -f {DOCKER_COMPOSE_FILE} down")

def wait_services(timeout=30):
    """Wait for required services to be ready."""
    def wait_for_port(port, host='localhost', timeout=30):
        """Wait until a port starts accepting TCP connections."""
        start_time = time.time()
        while True:
            try:
                with socket.create_connection((host, port), timeout=1):
                    return True
            except OSError:
                if time.time() - start_time >= timeout:
                    return False
                time.sleep(1)

    # Load environment variables from .env file
    env_vars = {}
    if ENV_FILE.exists():
        with ENV_FILE.open() as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value

    postgres_port = int(env_vars.get('POSTGRES_PORT', '5432'))
    redis_port = int(env_vars.get('REDIS_PORT', '6379'))

    print("Waiting for PostgreSQL to be ready...")
    if wait_for_port(postgres_port, timeout=timeout):
        print("PostgreSQL is up!")
    else:
        print("Failed to connect to PostgreSQL.", file=sys.stderr)
        sys.exit(1)

    print("Waiting for Redis to be ready...")
    if wait_for_port(redis_port, timeout=timeout):
        print("Redis is up!")
    else:
        print("Failed to connect to Redis.", file=sys.stderr)
        sys.exit(1)

def run_app(host="0.0.0.0", port=8080):
    """Run the FastAPI application."""
    print(f"Running the FastAPI application on {host}:{port}...")
    run_command(f"{sys.executable} -m uvicorn websrc.main:app --host {host} --port {port} --reload")

def setup():
    """Run all setup steps."""
    check_python_version()
    create_virtualenv()
    activate_virtualenv()
    install()
    validate_env()
    start_services()
    wait_services()

def reset():
    """Delete and recreate the virtual environment, and restart services."""
    # Confirm action
    print("This will delete the virtual environment and reinstall all dependencies.")
    confirmation = input("Are you sure you want to continue? (yes/no): ").lower()
    if confirmation != 'yes':
        print("Factory reset cancelled.")
        sys.exit(0)

    # Stop services
    stop_services()

    # Remove virtual environment
    if VENV_DIR.exists():
        print("Deleting virtual environment...")
        shutil.rmtree(VENV_DIR)
        print("Virtual environment deleted.")
    else:
        print("Virtual environment does not exist.")

    # Recreate virtual environment and reinstall dependencies
    create_virtualenv()
    activate_virtualenv()
    install()
    print("Virtual environment recreated and dependencies reinstalled.")

    # Start services
    start_services()
    wait_services()
    print("Services restarted.")

def main():
    parser = argparse.ArgumentParser(description="Manage FastAPI Application")
    subparsers = parser.add_subparsers(dest='command')

    # Create Virtualenv Command
    parser_create_venv = subparsers.add_parser('create-venv', help='Create a virtual environment')

    # Activate Virtualenv Command
    parser_activate_venv = subparsers.add_parser('activate-venv', help='Activate the virtual environment')

    # Install Command
    parser_install = subparsers.add_parser('install', help='Install project dependencies')

    # Create Env Command
    parser_create_env = subparsers.add_parser('create-env', help='Create a default .env file')

    # Start Services Command
    parser_start_services = subparsers.add_parser('start-services', help='Start required services')

    # Stop Services Command
    parser_stop_services = subparsers.add_parser('stop-services', help='Stop services')

    # Wait Services Command
    parser_wait_services = subparsers.add_parser('wait-services', help='Wait for services to be ready')
    parser_wait_services.add_argument('--timeout', type=int, default=30, help='Timeout in seconds')

    # Run App Command
    parser_run_app = subparsers.add_parser('run-app', help='Run the FastAPI application')
    parser_run_app.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind')
    parser_run_app.add_argument('--port', type=int, default=8080, help='Port to bind')

    # Setup Command
    parser_setup = subparsers.add_parser('setup', help='Run all setup steps')

    # Run Command
    parser_run = subparsers.add_parser('run', help='Setup and run the application')
    parser_run.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind')
    parser_run.add_argument('--port', type=int, default=8080, help='Port to bind')

    # Factory Reset Command
    parser_reset = subparsers.add_parser('reset', help='Delete and recreate the virtual environment and restart services')

    args = parser.parse_args()

    if args.command == 'create-venv':
        create_virtualenv()
    elif args.command == 'activate-venv':
        activate_virtualenv()
    elif args.command == 'install':
        activate_virtualenv()
        install()
    elif args.command == 'create-env':
        validate_env()
    elif args.command == 'start-services':
        start_services()
    elif args.command == 'stop-services':
        stop_services()
    elif args.command == 'wait-services':
        wait_services(timeout=args.timeout)
    elif args.command == 'run-app':
        activate_virtualenv()
        run_app(host=args.host, port=args.port)
    elif args.command == 'setup':
        setup()
    elif args.command == 'run':
        setup()
        run_app(host=args.host, port=args.port)
    elif args.command == 'reset':
        reset()
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 