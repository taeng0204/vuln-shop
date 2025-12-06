
# Configuration for Traffic Generator

import os

# Target URL (Default: https://professor.is-an.ai/)
TARGET_URL = os.getenv("TARGET_URL", "http://localhost:3000")

# Simulated IP for X-Forwarded-For header (for local testing with IP-based labeling)
# This IP will be used to identify traffic as "normal" in the NIDS dataset
SIMULATED_IP = os.getenv("SIMULATED_IP", "192.168.1.200")

# Duration of the simulation in seconds (1 hour = 3600 seconds)
DURATION = int(os.getenv("DURATION", 3600))

# Maximum number of concurrent users to simulate
MAX_USERS = int(os.getenv("MAX_USERS", 50))

# Delay ranges (in seconds) - simulates human reading/thinking time
MIN_DELAY = 1
MAX_DELAY = 5

# === Persona Configuration ===
# Different user types with varying behavior patterns
PERSONA_WEIGHTS = {
    'visitor': 0.20,       # Just browsing, no signup
    'new_user': 0.30,      # Signs up and explores
    'returning': 0.25,     # Tries to login with existing/wrong credentials
    'active': 0.15,        # Heavy activity (posts, profile updates)
    'order_checker': 0.10  # Checks order history
}

# === Failure Simulation ===
# Realistic failure rates for various actions
LOGIN_FAIL_RATE = 0.30        # 30% chance of login failure (wrong password)
SIGNUP_DUPLICATE_RATE = 0.20  # 20% chance of duplicate username
TYPO_RATE = 0.10              # 10% chance of typos in input

# === Action Weights ===
# Probability weights for different actions during a session
ACTION_WEIGHTS = {
    'browse_home': 0.25,
    'browse_board': 0.20,
    'write_post': 0.15,
    'view_profile': 0.15,
    'view_orders': 0.10,
    'logout_login': 0.10,
    'refresh_page': 0.05
}

# === User Agents ===
# Realistic browser User-Agent strings for variety
USER_AGENTS = [
    # Desktop - Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Desktop - Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.0; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Desktop - Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    # Desktop - Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Mobile - iPhone
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    # Mobile - Android
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    # Tablet - iPad
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    # Bot-like (occasional)
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
]

# === Existing User Pool ===
# Pre-defined users that "returning" personas can try to login as
# Some with correct passwords, some with wrong ones
EXISTING_USERS = [
    {"username": "guest", "password": "guest123", "valid": True},
    {"username": "testuser", "password": "wrongpass", "valid": False},
    {"username": "john_doe", "password": "password123", "valid": False},
    {"username": "alice", "password": "alice2024", "valid": False},
]
