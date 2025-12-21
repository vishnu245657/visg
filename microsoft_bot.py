import requests
import os

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_ID")
CHAT_ID = os.environ.get("CHAT_ID")
STATE_FILE = "state_microsoft.txt"

def get_seen_jobs():
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_seen_jobs(seen_jobs):
    with open(STATE_FILE, "w") as f:
        for job_id in seen_jobs:
            f.write(f"{job_id}\n")

def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram secrets missing.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def check_microsoft():
    print("Checking Microsoft...")
    seen_jobs = get_seen_jobs()
    
    # Filters: Software Engineering | Entry/Intern | Sort by Newest
    url = "https://gcsservices.careers.microsoft.com/search/api/v1/search?q=&filters=profession:software%20engineering;seniority:Entry,Intern&sort=timestamp&l=en_us&pg=1&pgSz=20"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code == 200:
            jobs = resp.json().get("operationResult", {}).get("result", {}).get("jobs", [])
            new_found = False
            
            for job in jobs:
                job_id = str(job['jobId'])
                if job_id not in seen_jobs:
                    title = job.get('title')
                    location = job.get('location')
                    link = f"https://jobs.careers.microsoft.com/global/en/job/{job_id}"
                    
                    msg = f"🪟 **Microsoft**\n{title}\n📍 {location}\n[Apply Here]({link})"
                    send_telegram(msg)
                    
                    seen_jobs.add(job_id)
                    new_found = True
            
            if new_found:
                save_seen_jobs(seen_jobs)
                print("New Microsoft jobs saved.")
        else:
            print(f"Microsoft API Status: {resp.status_code}")
            
    except Exception as e:
        print(f"Microsoft Error: {e}")

if __name__ == "__main__":
    check_microsoft()
