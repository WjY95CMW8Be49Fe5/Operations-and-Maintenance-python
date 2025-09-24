import os
import shutil
import subprocess
import datetime
import getpass
import tempfile
import logging
from pathlib import Path
import sys
import ctypes
import winreg

# Configure logging to capture all actions and errors
def setup_logging():
    current_user = getpass.getuser()
    log_dir = os.path.join(os.environ.get("TEMP", tempfile.gettempdir()), "SystemCleanupLogs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"cleanup_{current_user}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return log_file

# Check if the script is running with administrator privileges
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        logging.error(f"Error checking admin status: {str(e)}")
        return False

# Clean temporary files from user and system temp directories
def clean_temp_files():
    temp_dirs = [
        os.environ.get("TEMP", tempfile.gettempdir()),
        os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Temp")
    ]
    total_size = 0
    deleted_files = 0
    
    for temp_dir in temp_dirs:
        try:
            if os.path.exists(temp_dir):
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            size = os.path.getsize(item_path)
                            os.remove(item_path)
                            total_size += size
                            deleted_files += 1
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                            deleted_files += 1
                    except Exception as e:
                        logging.warning(f"Failed to delete {item_path}: {str(e)}")
        except Exception as e:
            logging.error(f"Error accessing temp directory {temp_dir}: {str(e)}")
    
    logging.info(f"Cleaned {deleted_files} items from temporary directories, freed {total_size / 1024:.2f} KB")
    return deleted_files, total_size

# Clean Windows update files using built-in cleanmgr utility
def clean_windows_update_files():
    try:
        # Run cleanmgr with predefined settings for Windows Update Cleanup
        cmd = "cleanmgr.exe /sagerun:1"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            logging.info("Successfully ran cleanmgr for Windows Update Cleanup")
            return True
        else:
            logging.error(f"Failed to run cleanmgr: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error running cleanmgr: {str(e)}")
        return False

# Clean system logs and event logs (safely)
def clean_system_logs():
    try:
        # Clear event logs using wevtutil (Windows built-in tool)
        cmd = "wevtutil el | ForEach-Object {wevtutil cl $_}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            logging.info("Successfully cleared system event logs")
            return True
        else:
            logging.error(f"Failed to clear event logs: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error clearing system logs: {str(e)}")
        return False

# Optimize system by disabling unnecessary startup programs (safe approach)
def optimize_startup():
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:           count = 0
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    logging.info(f"Found startup entry: {name} = {value}")
                    # Optionally disable non-critical entries (manual review recommended)
                    # This script logs entries for manual review instead of auto-disabling
                    count += 1
                    i += 1
                except OSError:
                    break
        logging.info(f"Found {count} startup entries for review")
        return True
    except Exception as e:
        logging.error(f"Error optimizing startup entries: {str(e)}")
        return False

# Perform basic security adjustments (e.g., disable SMBv1 if enabled on older systems)
def security_adjustments():
    try:
        # Disable SMBv1 (known vulnerability) using PowerShell
        cmd = "powershell -Command \"Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart\""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            logging.info("Successfully disabled SMBv1 protocol for security")
            return True
        else:
            logging.warning(f"Failed to disable SMBv1: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error during security adjustments: {str(e)}")
        return False

# Main function to orchestrate the cleanup and optimization process
def main():
    log_file = setup_logging()
    print(f"System Cleanup started. Log file: {log_file}")
    logging.info("System Cleanup process started")
    
    if not is_admin():
        logging.error("Script must be run as Administrator to perform system cleanup and optimization")
        print("Error: Please run this script as Administrator")
        return
    
    # Step 1: Clean temporary files
    print("Cleaning temporary files...")
    deleted_files, total_size = clean_temp_files()
    print(f"Cleaned {deleted_files} items, freed {total_size / 1024:.2f} KB")
    
    # Step 2: Clean Windows Update files
    print("Cleaning Windows Update files...")
    if clean_windows_update_files():
        print("Windows Update files cleaned successfully")
    else:
        print("Failed to clean Windows Update files. Check logs for details")
    
    # Step 3: Clean system logs
    print("Cleaning system logs...")
    if clean_system_logs():
        print("System logs cleaned successfully")
    else:
        print("Failed to clean system logs. Check logs for details")
    
    # Step 4: Optimize startup entries
    print("Optimizing startup programs...")
    if optimize_startup():
        print("Startup optimization completed. Check logs for details")
    else:
        print("Failed to optimize startup. Check logs for details")
    
    # Step 5: Perform security adjustments
    print("Performing security adjustments...")
    if security_adjustments():
        print("Security adjustments completed successfully")
    else:
        print("Failed to apply security adjustments. Check logs for details")
    
    logging.info("System Cleanup process completed")
    print("System Cleanup completed. Check the log file for detailed information")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Unexpected error in main process: {str(e)}")
        print(f"An unexpected error occurred: {str(e)}")
    finally:
        # Wait for user to review output before closing
        print("Press Enter to exit...")
        input()
