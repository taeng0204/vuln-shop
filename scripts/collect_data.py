#!/usr/bin/env python3
"""
collect_data.py - NIDS Training Data Collection Script

This script runs for a specified duration (default: 30 minutes),
then automatically merges L7 and L3/4 logs into a labeled CSV dataset.

Usage:
    python scripts/collect_data.py --duration 1800 --attacker-ip 192.168.1.100 --normal-ip 192.168.1.200
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta


def countdown(seconds: int):
    """Display countdown timer."""
    end_time = datetime.now() + timedelta(seconds=seconds)
    
    while datetime.now() < end_time:
        remaining = (end_time - datetime.now()).total_seconds()
        mins, secs = divmod(int(remaining), 60)
        hours, mins = divmod(mins, 60)
        
        print(f"\rCollecting data... Time remaining: {hours:02d}:{mins:02d}:{secs:02d}", end='', flush=True)
        time.sleep(1)
    
    print("\n")


def main():
    parser = argparse.ArgumentParser(description='Collect NIDS training data')
    parser.add_argument('--duration', type=int, default=1800, 
                        help='Collection duration in seconds (default: 1800 = 30 minutes)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output CSV path (default: output/traffic_YYYYMMDD_HHMMSS.csv)')
    parser.add_argument('--attacker-ip', type=str, default=os.getenv('ATTACKER_IP', ''),
                        help='Attacker IP(s), comma-separated')
    parser.add_argument('--normal-ip', type=str, default=os.getenv('NORMAL_IP', ''),
                        help='Normal traffic IP(s), comma-separated')
    parser.add_argument('--no-wait', action='store_true',
                        help='Skip waiting, process existing logs immediately')
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f'./output/traffic_{timestamp}.csv'
    
    print("=" * 60)
    print("NIDS Training Data Collection")
    print("=" * 60)
    print(f"Duration: {args.duration} seconds ({args.duration / 60:.1f} minutes)")
    print(f"Output: {output_path}")
    print(f"Attacker IP: {args.attacker_ip or '(not set - will label as unknown)'}")
    print(f"Normal IP: {args.normal_ip or '(not set - will label as unknown)'}")
    print("=" * 60)
    print()
    
    if not args.attacker_ip and not args.normal_ip:
        print("WARNING: No attacker or normal IPs specified.")
        print("         All traffic will be labeled as 'unknown'.")
        print("         Use --attacker-ip and --normal-ip to set labels.")
        print()
    
    if not args.no_wait:
        print(f"Starting data collection at {datetime.now().isoformat()}")
        print(f"Will finish at {(datetime.now() + timedelta(seconds=args.duration)).isoformat()}")
        print()
        print("Ensure the following are running:")
        print("  1. vuln-shop Docker containers (docker-compose up)")
        print("  2. Attack traffic from attacker PC")
        print("  3. Normal traffic from traffic-generator")
        print()
        
        # Wait for collection duration
        countdown(args.duration)
    
    print("Collection complete! Processing logs...")
    print()
    
    # Get script directory
    script_dir = Path(__file__).parent
    merge_script = script_dir / 'merge_logs.py'
    
    # Run merge script
    cmd = [
        sys.executable, str(merge_script),
        '--output', output_path
    ]
    
    if args.attacker_ip:
        cmd.extend(['--attacker-ip', args.attacker_ip])
    if args.normal_ip:
        cmd.extend(['--normal-ip', args.normal_ip])
    
    print(f"Running: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, cwd=script_dir.parent)
    
    if result.returncode == 0:
        print()
        print("=" * 60)
        print("Data collection complete!")
        print(f"Output saved to: {output_path}")
        print("=" * 60)
    else:
        print()
        print("ERROR: Log merging failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
