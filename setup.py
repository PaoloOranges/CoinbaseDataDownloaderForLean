#!/usr/bin/env python3
"""
Setup script for Coinbase Data Downloader
Creates virtual environment and installs dependencies
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(command, description):
    """Run a shell command and report status."""
    print(f"\n{'='*60}")
    print(f"▶ {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(command)}")
    print()
    
    try:
        result = subprocess.run(command, check=True)
        print(f"✓ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} - FAILED")
        print(f"Error: {e}")
        return False


def main():
    """Main setup routine."""
    print("\n" + "="*60)
    print("Coinbase Data Downloader - Setup Script")
    print("="*60)
    
    # Detect operating system
    is_windows = platform.system() == "Windows"
    python_cmd = sys.executable
    
    print(f"\nDetected OS: {platform.system()}")
    print(f"Python: {python_cmd}")
    print(f"Version: {sys.version}")
    
    # Step 1: Check Python version
    print("\n" + "="*60)
    print("Step 1: Checking Python version...")
    print("="*60)
    
    if sys.version_info < (3, 7):
        print("✗ Python 3.7 or higher is required!")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} is suitable")
    
    # Step 2: Create virtual environment
    venv_path = Path("venv")
    
    if venv_path.exists():
        print(f"\n✓ Virtual environment already exists at {venv_path}")
        use_existing = input("Use existing environment? (y/n): ").lower()
        if use_existing != 'y':
            import shutil
            print("Removing existing environment...")
            shutil.rmtree(venv_path)
            create_venv = True
        else:
            create_venv = False
    else:
        create_venv = True
    
    if create_venv:
        if not run_command(
            [python_cmd, "-m", "venv", str(venv_path)],
            "Creating virtual environment"
        ):
            sys.exit(1)
    
    # Step 3: Determine pip command
    if is_windows:
        pip_cmd = str(venv_path / "Scripts" / "pip.exe")
        python_venv_cmd = str(venv_path / "Scripts" / "python.exe")
    else:
        pip_cmd = str(venv_path / "bin" / "pip")
        python_venv_cmd = str(venv_path / "bin" / "python")
    
    # Step 4: Upgrade pip
    if not run_command(
        [pip_cmd, "install", "--upgrade", "pip"],
        "Upgrading pip"
    ):
        sys.exit(1)
    
    # Step 5: Install requirements
    if not run_command(
        [pip_cmd, "install", "-r", "requirements.txt"],
        "Installing dependencies from requirements.txt"
    ):
        sys.exit(1)
    
    # Step 6: Verify installation
    print("\n" + "="*60)
    print("Step 6: Verifying installation...")
    print("="*60)
    
    required_modules = ['requests']
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module} is installed")
        except ImportError:
            print(f"✗ {module} is NOT installed")
            sys.exit(1)
    
    # Step 7: Test the application
    print("\n" + "="*60)
    print("Step 7: Testing application...")
    print("="*60)
    
    test_cmd = [python_venv_cmd, "main.py", "--help"]
    print(f"Running: {' '.join(test_cmd)}\n")
    
    try:
        result = subprocess.run(test_cmd, capture_output=True, text=True, check=True)
        if "--help" in result.stdout:
            print("✓ Application is working correctly")
        else:
            print("✗ Application did not respond as expected")
    except subprocess.CalledProcessError as e:
        print(f"✗ Application test failed")
        print(f"Error: {e.stderr}")
    
    # Final instructions
    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60)
    print(f"""
Next steps:

1. Activate the virtual environment:
   
   Windows:  {venv_path}\\Scripts\\activate.bat
   Linux/Mac: source {venv_path}/bin/activate

2. Try the application:
   
   {python_venv_cmd} main.py list-symbols
   {python_venv_cmd} main.py --help

3. Start downloading data:
   
   {python_venv_cmd} main.py download BTC-USD --start 20240101-00:00:00 --end 20240107-23:59:59

For more information, see README_USAGE.md or QUICKSTART.md
""")


if __name__ == "__main__":
    main()
