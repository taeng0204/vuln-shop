#!/usr/bin/env python3
"""
user_agent.py - Realistic User Behavior Simulator

Simulates diverse user behaviors for NIDS training data generation.
Includes multiple personas, failure scenarios, and realistic browsing patterns.
"""

import requests
import time
import random
from faker import Faker
from bs4 import BeautifulSoup
import config

fake = Faker()


class UserAgent:
    """Base user agent that simulates realistic web browsing behavior."""
    
    def __init__(self, target_url=config.TARGET_URL, persona=None):
        self.target_url = target_url.rstrip('/')
        self.session = requests.Session()
        
        # Random User-Agent for variety
        self.user_agent = random.choice(config.USER_AGENTS)
        self.session.headers.update({
            'User-Agent': self.user_agent,
            # X-Forwarded-For for local testing with IP-based labeling
            'X-Forwarded-For': config.SIMULATED_IP
        })
        
        # User credentials
        self.username = fake.user_name()
        self.password = fake.password()
        self.email = fake.email()
        
        # Session state
        self.is_logged_in = False
        self.is_registered = False
        self.user_id = None
        
        # Persona determines behavior pattern
        self.persona = persona or self._choose_persona()
        
    def _choose_persona(self) -> str:
        """Choose a random persona based on configured weights."""
        personas = list(config.PERSONA_WEIGHTS.keys())
        weights = list(config.PERSONA_WEIGHTS.values())
        return random.choices(personas, weights=weights)[0]
    
    def log(self, message: str):
        """Log activity with persona context."""
        print(f"[{self.persona}:{self.username}] {message}")
    
    def wait(self, multiplier: float = 1.0):
        """Simulate human-like delay between actions."""
        delay = random.uniform(config.MIN_DELAY, config.MAX_DELAY) * multiplier
        time.sleep(delay)
    
    def _maybe_typo(self, text: str) -> str:
        """Occasionally introduce typos to simulate human error."""
        if random.random() < config.TYPO_RATE and len(text) > 3:
            pos = random.randint(1, len(text) - 2)
            return text[:pos] + random.choice('abcdefghijklmnopqrstuvwxyz') + text[pos+1:]
        return text
    
    # === Core Actions ===
    
    def browse_home(self) -> bool:
        """Visit the home page and view products."""
        try:
            self.log("Browsing home page...")
            response = self.session.get(f"{self.target_url}/")
            
            if response.status_code == 200:
                # Sometimes refresh the page (simulate reading)
                if random.random() < 0.3:
                    self.wait(0.5)
                    self.session.get(f"{self.target_url}/")
                    self.log("Refreshed home page")
                return True
            return False
        except Exception as e:
            self.log(f"Browsing error: {e}")
            return False
    
    def browse_board(self) -> bool:
        """Visit the Q&A board."""
        try:
            self.log("Browsing board...")
            response = self.session.get(f"{self.target_url}/board")
            return response.status_code == 200
        except Exception as e:
            self.log(f"Board browsing error: {e}")
            return False
    
    def visit_login_page(self) -> bool:
        """Visit the login page (without logging in)."""
        try:
            self.log("Visiting login page...")
            response = self.session.get(f"{self.target_url}/login")
            return response.status_code == 200
        except Exception as e:
            self.log(f"Login page error: {e}")
            return False
    
    def visit_signup_page(self) -> bool:
        """Visit the signup page (without signing up)."""
        try:
            self.log("Visiting signup page...")
            response = self.session.get(f"{self.target_url}/signup")
            return response.status_code == 200
        except Exception as e:
            self.log(f"Signup page error: {e}")
            return False
    
    def register(self, force_fail: bool = False) -> bool:
        """Attempt user registration."""
        url = f"{self.target_url}/signup"
        
        # Maybe use duplicate username to simulate failure
        if force_fail or random.random() < config.SIGNUP_DUPLICATE_RATE:
            username = random.choice(['guest', 'admin', 'test', self.username])
        else:
            username = self.username
        
        data = {
            "username": self._maybe_typo(username),
            "password": self.password,
            "email": self.email
        }
        
        try:
            self.log(f"Attempting registration as '{username}'...")
            response = self.session.post(url, data=data, allow_redirects=True)
            
            # Check if registration succeeded (redirected to login or success page)
            if response.status_code == 200:
                if 'already exists' in response.text.lower() or 'error' in response.text.lower():
                    self.log("Registration failed: Username exists")
                    return False
                self.is_registered = True
                self.log("Registration successful")
                return True
            return False
        except Exception as e:
            self.log(f"Registration error: {e}")
            return False
    
    def login(self, username: str = None, password: str = None, force_fail: bool = False) -> bool:
        """Attempt login with optional credential override."""
        url = f"{self.target_url}/login"
        
        # Use provided credentials or own
        login_user = username or self.username
        login_pass = password or self.password
        
        # Maybe use wrong password
        if force_fail or random.random() < config.LOGIN_FAIL_RATE:
            login_pass = fake.password()  # Wrong password
            self.log(f"Attempting login with WRONG password...")
        
        data = {
            "username": self._maybe_typo(login_user),
            "password": login_pass
        }
        
        try:
            self.log(f"Attempting login as '{login_user}'...")
            response = self.session.post(url, data=data, allow_redirects=True)
            
            # Check login result
            if response.status_code == 200:
                if 'invalid' in response.text.lower() or 'error' in response.text.lower():
                    self.log("Login failed: Invalid credentials")
                    return False
                
                # Check if we have user cookie
                if 'user' in self.session.cookies:
                    self.is_logged_in = True
                    self.log("Login successful")
                    return True
            return False
        except Exception as e:
            self.log(f"Login error: {e}")
            return False
    
    def logout(self) -> bool:
        """Logout from current session."""
        if not self.is_logged_in:
            return True
        
        try:
            self.log("Logging out...")
            response = self.session.get(f"{self.target_url}/logout", allow_redirects=True)
            self.is_logged_in = False
            return response.status_code == 200
        except Exception as e:
            self.log(f"Logout error: {e}")
            return False
    
    def write_post(self) -> bool:
        """Write a post on the board (requires login)."""
        if not self.is_logged_in:
            self.log("Cannot post: Not logged in")
            return False
        
        url = f"{self.target_url}/board"
        data = {
            "content": fake.paragraph(nb_sentences=random.randint(1, 5))
        }
        
        try:
            self.log("Writing a board post...")
            response = self.session.post(url, data=data, allow_redirects=True)
            if response.status_code == 200:
                self.log("Post created")
                return True
            return False
        except Exception as e:
            self.log(f"Posting error: {e}")
            return False
    
    def view_profile(self) -> bool:
        """View own profile page (requires login)."""
        if not self.is_logged_in:
            # Try to access anyway (will be redirected)
            pass
        
        try:
            self.log("Viewing profile...")
            response = self.session.get(f"{self.target_url}/profile", allow_redirects=True)
            return response.status_code == 200
        except Exception as e:
            self.log(f"Profile error: {e}")
            return False
    
    def view_orders(self) -> bool:
        """View order history (requires login)."""
        if not self.is_logged_in:
            pass
        
        try:
            self.log("Viewing orders...")
            response = self.session.get(f"{self.target_url}/order", allow_redirects=True)
            
            # Sometimes try to view a specific order
            if response.status_code == 200 and random.random() < 0.5:
                order_id = random.randint(1, 5)
                self.log(f"Viewing order #{order_id}...")
                self.session.get(f"{self.target_url}/order?id={order_id}")
            
            return response.status_code == 200
        except Exception as e:
            self.log(f"Orders error: {e}")
            return False
    
    # === Persona-based Simulation ===
    
    def simulate(self):
        """Run simulation based on assigned persona."""
        self.log(f"Starting simulation (User-Agent: {self.user_agent[:50]}...)")
        
        if self.persona == 'visitor':
            self._simulate_visitor()
        elif self.persona == 'new_user':
            self._simulate_new_user()
        elif self.persona == 'returning':
            self._simulate_returning_user()
        elif self.persona == 'active':
            self._simulate_active_user()
        elif self.persona == 'order_checker':
            self._simulate_order_checker()
        else:
            self._simulate_new_user()  # Default
        
        self.log("Simulation complete")
    
    def _simulate_visitor(self):
        """Visitor: Just browses without logging in."""
        self.log("Behavior: Visitor (browsing only)")
        
        actions = [
            self.browse_home,
            self.browse_board,
            self.visit_login_page,
            self.visit_signup_page,
        ]
        
        # Random number of page views (massively increased for high traffic)
        for _ in range(random.randint(50, 100)):
            action = random.choice(actions)
            action()
            self.wait()
    
    def _simulate_new_user(self):
        """New user: Signs up, logs in, explores."""
        self.log("Behavior: New User (signup → explore)")
        
        # Browse first
        self.browse_home()
        self.wait()
        
        # Try to signup (may fail if duplicate)
        if self.register():
            self.wait()
            if self.login():
                self.wait()
                
                # Explore as logged-in user
                actions = [
                    self.browse_home,
                    self.browse_board,
                    self.write_post,
                    self.view_profile,
                ]
                
                for _ in range(random.randint(50, 120)):
                    action = random.choice(actions)
                    action()
                    self.wait()
                
                # Maybe logout at the end
                if random.random() < 0.5:
                    self.logout()
    
    def _simulate_returning_user(self):
        """Returning user: Tries to login with existing credentials."""
        self.log("Behavior: Returning User (login attempt)")
        
        # Browse a bit
        self.browse_home()
        self.wait()
        
        # Try to login with existing user (may succeed or fail)
        existing = random.choice(config.EXISTING_USERS)
        
        self.visit_login_page()
        self.wait()
        
        if existing['valid']:
            # Use correct credentials
            if self.login(existing['username'], existing['password']):
                self.is_logged_in = True
                self.username = existing['username']
                
                # Do some activities
                for _ in range(random.randint(40, 80)):
                    action = random.choice([self.browse_home, self.browse_board, self.view_orders])
                    action()
                    self.wait()
        else:
            # Use wrong credentials (will fail)
            self.login(existing['username'], existing['password'])
            self.wait()
            
            # Maybe try again with different password
            if random.random() < 0.5:
                self.login(existing['username'], fake.password())
    
    def _simulate_active_user(self):
        """Active user: Heavy posting and profile activity."""
        self.log("Behavior: Active User (heavy activity)")
        
        # Register and login
        if self.register():
            self.wait()
            if self.login():
                self.wait()
                
                # Heavy activity (massively increased for high traffic)
                for _ in range(random.randint(80, 200)):
                    weights = [0.2, 0.3, 0.3, 0.15, 0.05]
                    actions = [
                        self.browse_home,
                        self.browse_board,
                        self.write_post,
                        self.view_profile,
                        lambda: (self.logout(), self.wait(), self.login())
                    ]
                    
                    action = random.choices(actions, weights=weights)[0]
                    if callable(action):
                        action()
                    self.wait()
    
    def _simulate_order_checker(self):
        """Order checker: Focuses on viewing order history."""
        self.log("Behavior: Order Checker (order focus)")
        
        # Try with existing user that might have orders
        existing = config.EXISTING_USERS[0]  # guest user
        
        self.browse_home()
        self.wait()
        self.visit_login_page()
        self.wait()
        
        if self.login(existing['username'], existing['password']):
            self.is_logged_in = True
            self.username = existing['username']
            
            # Focus on orders
            for _ in range(random.randint(40, 80)):
                self.view_orders()
                self.wait()
            
            # Maybe browse other pages too
            if random.random() < 0.5:
                self.browse_home()
                self.wait()
            if random.random() < 0.3:
                self.browse_board()


# For backwards compatibility
def create_user_agent(target_url=None, persona=None):
    """Factory function to create UserAgent instances."""
    return UserAgent(
        target_url=target_url or config.TARGET_URL,
        persona=persona
    )
