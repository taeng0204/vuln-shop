#!/usr/bin/env python3
"""
merge_logs.py - L7 Application Logs + L3/4 Network Logs Merger

This script merges application-level logs (HTTP requests) with network-level logs
(packet flows) based on (src_ip, src_port, timestamp) correlation.
It also labels traffic as 'attack' or 'normal' based on source IP.
"""

import os
import json
import csv
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Default paths
LOGS_DIR = Path('./logs')
CSV_DIR = Path('./csv')
OUTPUT_DIR = Path('./output')


def load_l7_logs(logs_dir: Path) -> list:
    """Load L7 application logs from JSON log files."""
    l7_logs = []
    
    for log_file in sorted(logs_dir.glob('traffic-*.log')):
        print(f"Loading L7 log: {log_file}")
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    if 'message' in log_entry and log_entry.get('message') == 'Traffic Log':
                        l7_logs.append(log_entry)
                except json.JSONDecodeError:
                    continue
    
    print(f"Loaded {len(l7_logs)} L7 log entries")
    return l7_logs


def load_l3l4_logs(csv_dir: Path) -> list:
    """Load L3/4 network flow logs from CSV files."""
    l3l4_logs = []
    
    for csv_file in sorted(csv_dir.glob('*.csv')):
        print(f"Loading L3/4 log: {csv_file}")
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                l3l4_logs.append(row)
    
    print(f"Loaded {len(l3l4_logs)} L3/4 flow entries")
    return l3l4_logs


def parse_timestamp(ts_str: str) -> datetime:
    """Parse ISO format timestamp, returning offset-naive datetime."""
    try:
        if not ts_str:
            return None
        # Handle various ISO formats
        if 'T' in ts_str:
            dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            # Convert to naive datetime for consistent comparison
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        return datetime.fromisoformat(ts_str)
    except:
        return None


def extract_ip(ip_str: str) -> str:
    """Extract clean IP address (handle ::ffff: prefix)."""
    if ip_str and ip_str.startswith('::ffff:'):
        return ip_str[7:]
    return ip_str


def build_flow_index(l3l4_logs: list) -> dict:
    """Build index of L3/4 flows by (src_ip, src_port) for quick lookup."""
    index = defaultdict(list)
    
    for flow in l3l4_logs:
        src_ip = flow.get('src_ip', '')
        src_port = flow.get('src_port', '')
        dst_ip = flow.get('dst_ip', '')
        dst_port = flow.get('dst_port', '')
        
        # Index by both directions since flow might be recorded either way
        index[(src_ip, src_port)].append(flow)
        index[(dst_ip, dst_port)].append(flow)
    
    return index


def find_matching_flow(l7_log: dict, flow_index: dict, time_tolerance_ms: int = 5000) -> dict:
    """Find L3/4 flow matching the L7 log entry."""
    src_ip = extract_ip(l7_log.get('ip', ''))
    src_port = str(l7_log.get('src_port', ''))
    l7_time = parse_timestamp(l7_log.get('timestamp', ''))
    
    if not l7_time:
        return None
    
    candidates = flow_index.get((src_ip, src_port), [])
    
    best_match = None
    min_diff = float('inf')
    
    for flow in candidates:
        flow_start = parse_timestamp(flow.get('start_time', ''))
        flow_end = parse_timestamp(flow.get('end_time', ''))
        
        if not flow_start:
            continue
        
        # Check if L7 timestamp falls within flow time range (with tolerance)
        tolerance = timedelta(milliseconds=time_tolerance_ms)
        
        if flow_start and flow_end:
            if flow_start - tolerance <= l7_time <= flow_end + tolerance:
                diff = abs((l7_time - flow_start).total_seconds())
                if diff < min_diff:
                    min_diff = diff
                    best_match = flow
    
    return best_match


def label_traffic(src_ip: str, attacker_ip: str, normal_ip: str) -> str:
    """Label traffic based on source IP."""
    src_ip = extract_ip(src_ip)
    
    # Handle comma-separated IPs
    attacker_ips = [ip.strip() for ip in attacker_ip.split(',') if ip.strip()]
    normal_ips = [ip.strip() for ip in normal_ip.split(',') if ip.strip()]
    
    if src_ip in attacker_ips:
        return 'attack'
    elif src_ip in normal_ips:
        return 'normal'
    else:
        return 'unknown'


def port_to_service(port: int) -> str:
    """Convert port number to NSL-KDD service name."""
    service_map = {
        20: 'ftp_data', 21: 'ftp', 22: 'ssh', 23: 'telnet', 25: 'smtp',
        53: 'domain', 67: 'domain_u', 68: 'domain_u', 
        80: 'http', 110: 'pop_3', 119: 'nntp', 123: 'ntp_u', 
        143: 'imap4', 161: 'snmp', 162: 'snmp',
        443: 'http_443', 993: 'imap4', 995: 'pop_3',
        3000: 'http', 8000: 'http_8001', 8080: 'http', 8443: 'http_443'
    }
    return service_map.get(port, 'other')


def merge_logs(l7_logs: list, l3l4_logs: list, attacker_ip: str, normal_ip: str) -> list:
    """Merge L7 and L3/4 logs into unified records."""
    print("Building flow index...")
    flow_index = build_flow_index(l3l4_logs)
    
    print("Merging logs...")
    merged = []
    matched_count = 0
    
    for l7 in l7_logs:
        # Find matching L3/4 flow
        flow = find_matching_flow(l7, flow_index)
        
        if flow:
            matched_count += 1
        
        # Build merged record
        src_ip = extract_ip(l7.get('ip', ''))
        user = l7.get('user', 'anonymous')
        response_status = l7.get('response_status', 0)
        
        # NSL-KDD: service (derived from dst_port)
        dst_port_val = int(flow.get('dst_port', 0)) if flow and flow.get('dst_port') else 3000
        service = port_to_service(dst_port_val)
        
        # NSL-KDD: logged_in (1 if user is not anonymous, else 0)
        logged_in = 1 if user and user != 'anonymous' else 0
        
        # NSL-KDD: is_guest_login (1 if user is guest, else 0)
        is_guest_login = 1 if user and user.lower() == 'guest' else 0
        
        # NSL-KDD: num_failed_logins (1 if login failed - status 401 or login page with error)
        is_login_url = '/login' in l7.get('url', '')
        num_failed_logins = 1 if is_login_url and response_status in [401, 200] and not logged_in else 0
        
        record = {
            # L7 fields
            'timestamp': l7.get('timestamp', ''),
            'request_id': l7.get('request_id', ''),
            'src_ip': src_ip,
            'src_port': l7.get('src_port', 0),
            'method': l7.get('method', ''),
            'url': l7.get('url', ''),
            'response_status': response_status,
            'duration_ms': l7.get('duration_ms', 0),
            'user': user,
            'security_level': l7.get('security_level', ''),
            'response_size': l7.get('response_size', 0),
            'user_agent': l7.get('user_agent', ''),
            'num_headers': l7.get('num_headers', 0),
            'num_query_params': l7.get('num_query_params', 0),
            'num_body_keys': l7.get('num_body_keys', 0),
            'request_content_length': l7.get('request_content_length', 0),
            'request_body': json.dumps(l7.get('body', {})) if l7.get('body') else '',
            
            # L3/4 fields (from matched flow or empty)
            'dst_port': flow.get('dst_port', '') if flow else '',
            'protocol': flow.get('protocol', '') if flow else '',
            'protocol_type': flow.get('protocol_type', '') if flow else '',  # NSL-KDD
            'flow_start_time': flow.get('start_time', '') if flow else '',
            'flow_end_time': flow.get('end_time', '') if flow else '',
            'flow_duration': flow.get('duration', '') if flow else '',
            'total_packets': flow.get('total_packets', '') if flow else '',
            'total_bytes': flow.get('total_bytes', '') if flow else '',
            'src_bytes': flow.get('src_bytes', '') if flow else '',  # NSL-KDD
            'dst_bytes': flow.get('dst_bytes', '') if flow else '',  # NSL-KDD
            'land': flow.get('land', 0) if flow else 0,  # NSL-KDD
            
            # NSL-KDD derived features
            'service': service,  # NSL-KDD: service type
            'logged_in': logged_in,  # NSL-KDD: logged_in flag
            'is_guest_login': is_guest_login,  # NSL-KDD: is_guest_login flag
            'num_failed_logins': num_failed_logins,  # NSL-KDD: num_failed_logins
            
            # Label
            'label': label_traffic(src_ip, attacker_ip, normal_ip)
        }
        
        merged.append(record)
    
    print(f"Merged {len(merged)} records ({matched_count} matched with L3/4 flows)")
    return merged


def save_merged_csv(merged: list, output_path: Path):
    """Save merged records to CSV."""
    if not merged:
        print("No records to save.")
        return
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = list(merged[0].keys())
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged)
    
    print(f"Saved {len(merged)} records to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Merge L7 and L3/4 logs with IP-based labeling')
    parser.add_argument('--logs-dir', type=str, default='./logs', help='L7 logs directory')
    parser.add_argument('--csv-dir', type=str, default='./csv', help='L3/4 CSV directory')
    parser.add_argument('--output', type=str, default='./output/merged_traffic.csv', help='Output CSV path')
    parser.add_argument('--attacker-ip', type=str, default=os.getenv('ATTACKER_IP', ''), 
                        help='Attacker IP(s), comma-separated')
    parser.add_argument('--normal-ip', type=str, default=os.getenv('NORMAL_IP', ''), 
                        help='Normal traffic IP(s), comma-separated')
    
    args = parser.parse_args()
    
    logs_dir = Path(args.logs_dir)
    csv_dir = Path(args.csv_dir)
    output_path = Path(args.output)
    
    print(f"L7 Logs Dir: {logs_dir}")
    print(f"L3/4 CSV Dir: {csv_dir}")
    print(f"Output: {output_path}")
    print(f"Attacker IP: {args.attacker_ip or '(not set)'}")
    print(f"Normal IP: {args.normal_ip or '(not set)'}")
    print()
    
    # Load logs
    l7_logs = load_l7_logs(logs_dir)
    l3l4_logs = load_l3l4_logs(csv_dir)
    
    # Merge and label
    merged = merge_logs(l7_logs, l3l4_logs, args.attacker_ip, args.normal_ip)
    
    # Save
    save_merged_csv(merged, output_path)
    
    # Print label statistics
    if merged:
        labels = defaultdict(int)
        for r in merged:
            labels[r['label']] += 1
        print("\nLabel Distribution:")
        for label, count in sorted(labels.items()):
            print(f"  {label}: {count} ({100*count/len(merged):.1f}%)")


if __name__ == '__main__':
    main()
