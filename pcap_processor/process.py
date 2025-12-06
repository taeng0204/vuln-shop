import os
import time
import csv
import subprocess
from pathlib import Path
from collections import defaultdict
from scapy.all import rdpcap, IP, TCP, UDP

PCAP_DIR = Path('/data/pcap')
CSV_DIR = Path('/data/csv')
MAX_PENDING_FILES = 50 # Maximum number of pcap files to keep in queue


def get_flow_key(pkt):
    if IP in pkt:
        src = pkt[IP].src
        dst = pkt[IP].dst
        proto = pkt[IP].proto
        sport = 0
        dport = 0
        if TCP in pkt:
            sport = pkt[TCP].sport
            dport = pkt[TCP].dport
        elif UDP in pkt:
            sport = pkt[UDP].sport
            dport = pkt[UDP].dport
        
        # Canonical key (sorted) to group bidirectional flows
        key = tuple(sorted([(src, sport), (dst, dport)]) + [proto])
        return key
    return None

def process_pcap(input_file, output_file):
    print(f"Reading {input_file}...")
    try:
        packets = rdpcap(str(input_file))
    except Exception as e:
        print(f"Error reading pcap: {e}")
        return

    flows = defaultdict(lambda: {
        'start_time': float('inf'),
        'end_time': 0,
        'src_ip': '',
        'dst_ip': '',
        'src_port': 0,
        'dst_port': 0,
        'protocol': 0,
        'total_packets': 0,
        'total_bytes': 0,
        # NSL-KDD compatible features
        'src_bytes': 0,  # bytes from src to dst
        'dst_bytes': 0,  # bytes from dst to src
    })

    print(f"Processing {len(packets)} packets...")
    for pkt in packets:
        if IP not in pkt:
            continue
            
        key = get_flow_key(pkt)
        if not key:
            continue
            
        flow = flows[key]
        
        # Initialize flow info from first packet
        if flow['total_packets'] == 0:
            flow['src_ip'] = pkt[IP].src
            flow['dst_ip'] = pkt[IP].dst
            flow['protocol'] = pkt[IP].proto
            if TCP in pkt:
                flow['src_port'] = pkt[TCP].sport
                flow['dst_port'] = pkt[TCP].dport
            elif UDP in pkt:
                flow['src_port'] = pkt[UDP].sport
                flow['dst_port'] = pkt[UDP].dport
        
        # Update stats
        flow['start_time'] = min(flow['start_time'], float(pkt.time))
        flow['end_time'] = max(flow['end_time'], float(pkt.time))
        flow['total_packets'] += 1
        flow['total_bytes'] += len(pkt)
        
        # Track directional bytes (NSL-KDD: src_bytes, dst_bytes)
        if pkt[IP].src == flow['src_ip']:
            flow['src_bytes'] += len(pkt)
        else:
            flow['dst_bytes'] += len(pkt)

    print(f"Found {len(flows)} flows. Writing to {output_file}...")
    
    # Protocol number to name mapping (NSL-KDD compatible)
    proto_map = {6: 'tcp', 17: 'udp', 1: 'icmp'}
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'src_ip', 'dst_ip', 'src_port', 'dst_port', 
            'protocol', 'protocol_type',  # NSL-KDD: protocol_type
            'start_time', 'end_time', 'duration', 
            'total_packets', 'total_bytes',
            'src_bytes', 'dst_bytes',  # NSL-KDD: src_bytes, dst_bytes
            'land'  # NSL-KDD: land (src_ip == dst_ip)
        ])
        
        for flow in flows.values():
            duration = flow['end_time'] - flow['start_time']
            # Convert timestamps to ISO format for easier correlation
            from datetime import datetime
            start_iso = datetime.fromtimestamp(flow['start_time']).isoformat() if flow['start_time'] != float('inf') else ''
            end_iso = datetime.fromtimestamp(flow['end_time']).isoformat() if flow['end_time'] != 0 else ''
            
            # NSL-KDD: protocol_type (tcp/udp/icmp)
            protocol_type = proto_map.get(flow['protocol'], 'other')
            
            # NSL-KDD: land (1 if src_ip == dst_ip, else 0)
            land = 1 if flow['src_ip'] == flow['dst_ip'] else 0
            
            writer.writerow([
                flow['src_ip'],
                flow['dst_ip'],
                flow['src_port'],
                flow['dst_port'],
                flow['protocol'],
                protocol_type,
                start_iso,
                end_iso,
                f"{duration:.6f}",
                flow['total_packets'],
                flow['total_bytes'],
                flow['src_bytes'],
                flow['dst_bytes'],
                land
            ])

def convert_pcap_to_csv(pcap_file):
    try:
        print(f"Processing {pcap_file}...")
        csv_filename = pcap_file.stem + '.csv'
        csv_output_path = CSV_DIR / csv_filename
        
        # Use internal function instead of subprocess
        process_pcap(pcap_file, csv_output_path)
        print(f"Successfully converted {pcap_file} to CSV.")
        
        # Auto-delete processed pcap file to save space
        try:
            pcap_file.unlink()
            print(f"Deleted processed file: {pcap_file}")
        except Exception as e:
            print(f"Failed to delete {pcap_file}: {e}")
    except Exception as e:
        print(f"Error converting {pcap_file}: {e}")

def main():
    print("Starting PCAP Processor...")
    
    # Ensure CSV directory exists
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    
    processed_files = set()
    
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
                        if time.time() - pcap_file.stat().st_mtime < 10:
                            continue
                            
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
