#!/usr/bin/env python3
"""
main.py - Traffic Generator Entry Point

Generates realistic normal traffic for NIDS training data collection.
Simulates multiple concurrent users with diverse behavior patterns.
"""

import time
import threading
import random
from collections import Counter
import config
from user_agent import UserAgent


def user_session(user_id: int, stats: dict, lock: threading.Lock):
    """Run a single user session."""
    agent = UserAgent()
    
    with lock:
        stats['personas'][agent.persona] += 1
    
    print(f"[User {user_id}] Started as '{agent.persona}'")
    agent.simulate()
    print(f"[User {user_id}] Finished")
    
    with lock:
        stats['completed'] += 1


def main():
    print("=" * 60)
    print("Traffic Generator - NIDS Normal Traffic Simulator")
    print("=" * 60)
    print(f"Target: {config.TARGET_URL}")
    print(f"Duration: {config.DURATION} seconds ({config.DURATION / 60:.1f} minutes)")
    print(f"Max Concurrent Users: {config.MAX_USERS}")
    print(f"User-Agent Pool: {len(config.USER_AGENTS)} variants")
    print("=" * 60)
    print()

    start_time = time.time()
    active_threads = []
    user_count = 0
    
    # Statistics tracking
    stats = {
        'personas': Counter(),
        'completed': 0
    }
    stats_lock = threading.Lock()

    while time.time() - start_time < config.DURATION:
        # Clean up finished threads
        active_threads = [t for t in active_threads if t.is_alive()]
        
        if len(active_threads) < config.MAX_USERS:
            # Spawn new user
            user_count += 1
            t = threading.Thread(
                target=user_session, 
                args=(user_count, stats, stats_lock)
            )
            t.start()
            active_threads.append(t)
            
            # Random delay between spawning users
            time.sleep(random.uniform(0.5, 2.0))
        else:
            time.sleep(1)

    print()
    print("Time limit reached. Waiting for active users to finish...")
    for t in active_threads:
        t.join(timeout=30)
    
    # Print statistics
    print()
    print("=" * 60)
    print("Traffic Generation Complete!")
    print("=" * 60)
    print(f"Total Users Spawned: {user_count}")
    print(f"Completed Sessions: {stats['completed']}")
    print()
    print("Persona Distribution:")
    for persona, count in sorted(stats['personas'].items()):
        pct = 100 * count / user_count if user_count > 0 else 0
        print(f"  {persona}: {count} ({pct:.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    main()
