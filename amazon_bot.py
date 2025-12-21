import requests
import os
import hashlib
import json

# --- CONFIGURATION ---
# We use Amazon's internal API, not the public HTML page.
# This URL fetches "Student Programs" sorted by "Most Recent".
URL = "https://www.amazon.jobs/content/en/career-programs/university"
MEMORY_FILE = "state_amazon.txt"

# Telegram Secrets
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
    try:
        response = requests.get(URL)
        response.raise_for_status()
        
        data = response.json()
        jobs = data.get("jobs", [])
        
        if not jobs:
            return "NO_JOBS"

        # Create a clean list of the top 5 newest jobs
        job_summary = []
        for job in jobs[:5]:
            title = job.get("title", "Unknown Role")
            job_id = job.get("id_icims", "Unknown ID")
            job_summary.append(f"{job_id}:{title}")
            
        # Create a fingerprint of this list
        content = "||".join(job_summary)
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    except Exception as e:
        print(f"Error checking Amazon: {e}")
        return None

# --- EXECUTION ---
current_hash = get_job_hash()

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
            send_alert("🚨 <b>AMAZON JOBS UPDATE</b>\n\nNew Student/University roles detected.\n<a href='https://www.amazon.jobs/en/teams/internships-for-students'>Click here to check</a>")
    else:
        print("No changes found.")
