import requests
import os
import hashlib
import json

# --- CONFIGURATION ---
# The HIDDEN Workday API. 
# We derived this from the URL you provided: https://salesforce.wd12.myworkdayjobs.com/en-US/Futureforce_NewGradRoles
API_URL = "https://salesforce.wd12.myworkdayjobs.com/wday/cxs/salesforce/Futureforce_NewGradRoles/jobs"
MEMORY_FILE = "state_salesforce.txt"

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
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    # Payload to ask for the newest jobs
    payload = {
        "appliedFacets": {},
        "limit": 20,
        "offset": 0,
        "searchText": ""
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        job_items = data.get("jobPostings", [])
        
        if not job_items:
            return "NO_JOBS"

        # Create a fingerprint of the top 5 jobs
        # We use the 'bulletinField' (Job Title) and 'externalPath' (URL part)
        summary = []
        for job in job_items[:5]:
            title = job.get("title", "Unknown")
            summary.append(title)
            
        content = "||".join(summary)
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    except Exception as e:
        print(f"Error checking Salesforce: {e}")
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
            send_alert("🚨 <b>SALESFORCE JOBS UPDATE</b>\n\nNew Futureforce/Grad roles detected.\n<a href='https://salesforce.wd12.myworkdayjobs.com/en-US/Futureforce_NewGradRoles'>Click here to check</a>")
    else:
        print("No changes found.")
