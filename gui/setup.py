
"""
Installation and Setup Script for XIAO ESP32S3 GUI
This script helps install required dependencies and launch the GUI application.
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required Python packages"""
    requirements = [
        'pyserial',
        'bleak',
    ]
    
    print("Installing required packages...")
    for package in requirements:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✓ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {e}")
            return False
    
    return True

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"Error: Python 3.7+ required. Current version: {version.major}.{version.minor}")
        return False
    return True

def main():
    """Main setup function"""
    print("XIAO ESP32S3 GUI Setup")
    print("=" * 30)
    
    # Check Python version
    if not check_python_version():
        input("Press Enter to exit...")
        return
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install requirements
    if install_requirements():
        print("\n✓ All packages installed successfully!")
        print("\nYou can now run the GUI with:")
        print("  python esp32s3_gui.py")
        
        # Ask if user wants to launch now
        choice = input("\nWould you like to launch the GUI now? (y/n): ").lower()
        if choice in ['y', 'yes']:
            try:
                import esp32s3_gui
                esp32s3_gui.main()
            except Exception as e:
                print(f"Error launching GUI: {e}")
    else:
        print("\n✗ Setup failed. Please install packages manually:")
        print("  pip install pyserial bleak")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()