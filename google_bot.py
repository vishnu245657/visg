import requests
import os
import hashlib
import json
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
# The exact Google Careers URL you provided
URL = "https://www.google.com/about/careers/applications/jobs/results?degree=PURSUING_DEGREE&degree=BACHELORS&employment_type=TEMPORARY&employment_type=PART_TIME&employment_type=FULL_TIME&jlo=en&sort_by=date"
MEMORY_FILE = "state_google.txt"

# Telegram Secrets (From GitHub)
BOT_TOKEN = os.environ['BOT_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

def send_alert(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
        print("Alert Sent!")
    except Exception as e:
        print(f"Failed to send alert: {e}")

def get_job_hash():
    # Google requires headers that look exactly like a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1"
    }

    try:
        response = requests.get(URL, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- STRATEGY: Aria-Labels ---
        # Google uses aria-label="Learn more about [Job Title]" for screen readers.
        # This is the most stable way to extract job titles without guessing random class names.
        
        job_titles = []
        links = soup.find_all("a", attrs={"aria-label": True})
        
        for link in links:
            label = link["aria-label"]
            if label.startswith("Learn more about"):
                # Clean: "Learn more about Software Engineer" -> "Software Engineer"
                title = label.replace("Learn more about ", "").strip()
                job_titles.append(title)
        
        if not job_titles:
            # Fallback for mobile layout or different HTML structure
            headers = soup.find_all("h3")
            for h in headers:
                if len(h.get_text()) > 3:
                    job_titles.append(h.get_text(strip=True))

        if not job_titles:
            print("Warning: No jobs found. Google might be blocking the request.")
            return None

        # Create a unique fingerprint of the top 5 newest jobs
        # We only check the top 5 because we are sorting by date
        content_to_hash = "||".join(job_titles[:5])
        return hashlib.md5(content_to_hash.encode('utf-8')).hexdigest()

    except Exception as e:
        print(f"Error checking site: {e}")
        return None

# --- MAIN EXECUTION ---
current_hash = get_job_hash()

if current_hash:
    # 1. Read Old Hash
    old_hash = ""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            old_hash = f.read().strip()
            
    # 2. Compare
    if current_hash != old_hash:
        print(f"Change Detected! New Hash: {current_hash}")
        
        # Save New Hash
        with open(MEMORY_FILE, "w") as f:
            f.write(current_hash)
            
        # Alert (Skip on first run so you don't get spammed when you start)
        if old_hash != "":
            send_alert(f"🚨 <b>GOOGLE JOB UPDATE</b>\n\nNew roles detected on the Careers Page.\n<a href='{URL}'>Click here to check</a>")
    else:
        print("No changes found.")
