import requests
import os
import hashlib
import json
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
# The specific Meta URL for University Grad - Engineering
URL = "https://www.metacareers.com/jobsearch?teams[0]=University%20Grad%20-%20Engineering%2C%20Tech%20%26%20Design"
MEMORY_FILE = "state_meta.txt"

# Telegram Secrets
BOT_TOKEN = os.environ['BOT_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

def send_alert(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Failed to send alert: {e}")

def get_job_fingerprint():
    # Meta requires headers to look like a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none"
    }

    try:
        response = requests.get(URL, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- STRATEGY ---
        # Meta's structure is dynamic, but job titles usually appear in links 
        # or headers. We capture all text that looks like a job title link.
        
        job_titles = []
        # Find all links that point to a job description page
        links = soup.find_all("a", href=True)
        
        for link in links:
            href = link['href']
            # Filter for job posts (usually containing /jobs/ and excluding login/generic links)
            if "/jobs/" in href and "login" not in href:
                title = link.get_text(" ", strip=True)
                if len(title) > 5: # Filter out icons or empty links
                    job_titles.append(title)

        if not job_titles:
            # Fallback: Hash the main text content if specific links aren't found
            # This ensures we still detect changes even if they change CSS classes
            text_content = soup.get_text()[:5000] 
            if "No jobs found" in text_content:
                return "NO_JOBS"
            return hashlib.md5(text_content.encode('utf-8')).hexdigest()

        # Create a fingerprint of the top 5 jobs
        content_to_hash = "||".join(job_titles[:5])
        return hashlib.md5(content_to_hash.encode('utf-8')).hexdigest()

    except Exception as e:
        print(f"Error checking Meta: {e}")
        return None

# --- EXECUTION ---
current_hash = get_job_fingerprint()

if current_hash:
    old_hash = ""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            old_hash = f.read().strip()
            
    if current_hash != old_hash:
        print(f"Change Detected! New Hash: {current_hash}")
        
        with open(MEMORY_FILE, "w") as f:
            f.write(current_hash)
            
        if old_hash != "":
            send_alert(f"🚨 <b>META JOB UPDATE</b>\n\nNew University Grad roles detected.\n<a href='{URL}'>Click here to check</a>")
    else:
        print("No changes found.")
