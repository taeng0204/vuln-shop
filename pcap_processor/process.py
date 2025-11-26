import os
import time
import subprocess
from pathlib import Path

PCAP_DIR = Path('/data/pcap')
CSV_DIR = Path('/data/csv')
MAX_PENDING_FILES = 50 # Maximum number of pcap files to keep in queue


def convert_pcap_to_csv(pcap_file):
    try:
        print(f"Processing {pcap_file}...")
        # cicflowmeter -f <pcap_file> -c <csv_dir>
        # It seems cicflowmeter tries to write to the path specified by -c.
        # If -c is a directory, it fails. Let's specify the full output path.
        csv_filename = pcap_file.stem + '.csv'
        csv_output_path = CSV_DIR / csv_filename
        
        # Note: cicflowmeter might append .csv automatically or behave differently.
        # Let's try passing the directory again but ensure we are using it right.
        # If the error is "Is a directory", it means it tried to open the path we gave it.
        # So we should give it the full file path.
        subprocess.run(['cicflowmeter', '-f', str(pcap_file), '-c', str(csv_output_path)], check=True)
        print(f"Successfully converted {pcap_file} to CSV.")
        
        # Auto-delete processed pcap file to save space
        try:
            pcap_file.unlink()
            print(f"Deleted processed file: {pcap_file}")
        except Exception as e:
            print(f"Failed to delete {pcap_file}: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Error converting {pcap_file}: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def main():
    print("Starting PCAP Processor...")
    
    # Ensure CSV directory exists
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    
    processed_files = set()
    
    # Initial scan to mark existing files as processed (optional, or process them)
    # For now, let's process everything that doesn't have a corresponding CSV
    
    while True:
        try:
            cleanup_old_files(processed_files)
            
            if PCAP_DIR.exists():
                for pcap_file in PCAP_DIR.glob('*.pcap'):
                    # Check if CSV already exists
                    csv_filename = pcap_file.stem + '.csv'
                    csv_file = CSV_DIR / csv_filename
                    
                    if not csv_file.exists() and pcap_file not in processed_files:
                        # Check if file is being written to (modified in last 10 seconds)
                        # This prevents reading incomplete pcap files
                        if time.time() - pcap_file.stat().st_mtime < 10:
                            continue
                            
                        # Wait a bit to ensure file write is complete (simple heuristic)
                        # A better way would be to check file modification time or use inotify
                        # time.sleep(1) 
                        convert_pcap_to_csv(pcap_file)
                        processed_files.add(pcap_file)
            
            time.sleep(10) # Check every 10 seconds
            

        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(10)

def cleanup_old_files(processed_files):
    """
    Remove old pcap files if queue is too large to prevent disk fill-up during attacks.
    """
    try:
        if not PCAP_DIR.exists():
            return

        pcap_files = sorted(list(PCAP_DIR.glob('*.pcap')), key=lambda f: f.stat().st_mtime)
        
        # Identify unprocessed files
        unprocessed = []
        for pcap in pcap_files:
            csv_file = CSV_DIR / (pcap.stem + '.csv')
            if not csv_file.exists() and pcap not in processed_files:
                unprocessed.append(pcap)
        
        # If backlog is too big, delete oldest unprocessed files
        if len(unprocessed) > MAX_PENDING_FILES:
            files_to_delete = unprocessed[:-MAX_PENDING_FILES]
            print(f"WARNING: System under high load. Dropping {len(files_to_delete)} old pcap files.")
            for f in files_to_delete:
                try:
                    f.unlink()
                    processed_files.add(f) # Mark as 'processed' so we don't try again
                except Exception as e:
                    print(f"Failed to delete {f}: {e}")
                    
    except Exception as e:
        print(f"Error during cleanup: {e}")


if __name__ == "__main__":
    main()
