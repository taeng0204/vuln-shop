#!/usr/bin/env python3
"""
fast_pcap_processor.py - Stream-based PCAP to CSV converter
Uses scapy's PcapReader for memory-efficient streaming instead of loading entire file.
"""

import os
import csv
import sys
from collections import defaultdict
from datetime import datetime

try:
    from scapy.all import PcapReader, IP, TCP, UDP, ICMP
except ImportError:
    print("Error: scapy not installed. Run: pip install scapy")
    sys.exit(1)

PCAP_DIR = os.getenv('PCAP_DIR', './pcap')
CSV_DIR = os.getenv('CSV_DIR', './csv')

def get_flow_key(pkt):
    """Generate flow key from packet."""
    if IP not in pkt:
        return None
    
    ip = pkt[IP]
    src_ip = ip.src
    dst_ip = ip.dst
    proto = ip.proto
    
    src_port = dst_port = 0
    if TCP in pkt:
        src_port = pkt[TCP].sport
        dst_port = pkt[TCP].dport
    elif UDP in pkt:
        src_port = pkt[UDP].sport
        dst_port = pkt[UDP].dport
    
    # Normalize flow key (smaller IP first)
    if (src_ip, src_port) > (dst_ip, dst_port):
        return (dst_ip, src_ip, dst_port, src_port, proto)
    return (src_ip, dst_ip, src_port, dst_port, proto)

def process_pcap_streaming(input_file, output_file):
    """Process pcap file using streaming to avoid memory issues."""
    print(f"Processing: {input_file}")
    
    flows = defaultdict(lambda: {
        'src_ip': '', 'dst_ip': '',
        'src_port': 0, 'dst_port': 0,
        'protocol': 0,
        'start_time': None, 'end_time': None,
        'total_packets': 0, 'total_bytes': 0,
        'src_bytes': 0, 'dst_bytes': 0
    })
    
    packet_count = 0
    try:
        # Use PcapReader for streaming (memory efficient)
        with PcapReader(input_file) as reader:
            for pkt in reader:
                packet_count += 1
                if packet_count % 100000 == 0:
                    print(f"  Processed {packet_count:,} packets...")
                
                flow_key = get_flow_key(pkt)
                if flow_key is None:
                    continue
                
                flow = flows[flow_key]
                pkt_time = datetime.fromtimestamp(float(pkt.time))
                pkt_len = len(pkt)
                
                if IP in pkt:
                    ip = pkt[IP]
                    
                    if flow['total_packets'] == 0:
                        flow['src_ip'] = flow_key[0]
                        flow['dst_ip'] = flow_key[1]
                        flow['src_port'] = flow_key[2]
                        flow['dst_port'] = flow_key[3]
                        flow['protocol'] = flow_key[4]
                        flow['start_time'] = pkt_time
                    
                    flow['end_time'] = pkt_time
                    flow['total_packets'] += 1
                    flow['total_bytes'] += pkt_len
                    
                    # Track directional bytes
                    if ip.src == flow['src_ip']:
                        flow['src_bytes'] += pkt_len
                    else:
                        flow['dst_bytes'] += pkt_len
    
    except Exception as e:
        print(f"Error processing pcap: {e}")
        return
    
    print(f"  Total packets: {packet_count:,}")
    print(f"  Total flows: {len(flows):,}")
    
    # Write CSV
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
    
    proto_map = {6: 'tcp', 17: 'udp', 1: 'icmp'}
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'src_ip', 'dst_ip', 'src_port', 'dst_port', 'protocol', 'protocol_type',
            'start_time', 'end_time', 'duration', 'total_packets', 'total_bytes',
            'src_bytes', 'dst_bytes', 'land'
        ])
        
        for flow in flows.values():
            if flow['start_time'] and flow['end_time']:
                duration = (flow['end_time'] - flow['start_time']).total_seconds()
                protocol_type = proto_map.get(flow['protocol'], 'other')
                land = 1 if flow['src_ip'] == flow['dst_ip'] else 0
                
                writer.writerow([
                    flow['src_ip'], flow['dst_ip'],
                    flow['src_port'], flow['dst_port'],
                    flow['protocol'], protocol_type,
                    flow['start_time'].isoformat(),
                    flow['end_time'].isoformat(),
                    f"{duration:.6f}",
                    flow['total_packets'], flow['total_bytes'],
                    flow['src_bytes'], flow['dst_bytes'],
                    land
                ])
    
    print(f"  Saved to: {output_file}")

def main():
    print("Fast PCAP Processor (Streaming Mode)")
    print("=" * 40)
    
    pcap_files = [f for f in os.listdir(PCAP_DIR) if f.endswith('.pcap')]
    
    if not pcap_files:
        print("No pcap files found.")
        return
    
    for pcap_file in pcap_files:
        input_path = os.path.join(PCAP_DIR, pcap_file)
        output_name = pcap_file.replace('.pcap', '.csv')
        output_path = os.path.join(CSV_DIR, output_name)
        
        # Skip if already processed
        if os.path.exists(output_path):
            existing_size = os.path.getsize(output_path)
            if existing_size > 500:  # More than just header
                print(f"Skipping {pcap_file} (already processed)")
                continue
        
        process_pcap_streaming(input_path, output_path)
    
    print("\nDone!")

if __name__ == '__main__':
    main()
