from git import Repo
from os import urandom
from datetime import datetime, timedelta
import random
import time
import requests
import os

# ======= CONFIGURATION =======
PATH_OF_GIT_REPO = r'C:\Users\BOOG\Documents\shopify\.git'
GITHUB_PROFILE_URL = "https://github.com/boog-rabbit"
# ==============================


def random_hex_string(length=3):
    return urandom(length).hex()


def git_add_commit_push(COMMIT_MESSAGE):
    """Adds, commits, and pushes all changes to origin/main."""
    try:
        repo = Repo(PATH_OF_GIT_REPO)
        origin = repo.remote(name='origin')

        repo.git.add(all=True)
        print("[*] git add .")

        repo.index.commit(COMMIT_MESSAGE)
        print(f"[*] git commit -m {COMMIT_MESSAGE}")

        origin.push()
        print(f"[*] git push -u origin main\n")
    except Exception as e:
        print(f"[!] Error in git_add_commit_push(): {e}\n")


# ---- Optional: Get Current Commit Count ----
try:
    response = requests.get(GITHUB_PROFILE_URL)
    if response.status_code == 200:
        print("[*] Successfully connected to GitHub profile.")
    else:
        print("[!] Could not verify GitHub profile.")
except Exception as e:
    print(f"[!] Failed to fetch current commits: {e}")


# ---- User Inputs ----
max_loop = int(input("\nHow many commits do you want to make? "))
start_date_str = input("Enter start date (YYYY-MM-DD) or leave blank for today: ").strip()

if start_date_str:
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
else:
    start_date = datetime.now()

run_id = random_hex_string()
current_date = f"{start_date:%m.%d.%Y}"

print(f"\n[***] Starting commit sequence at {start_date} | Run ID: {run_id}\n")

# ---- Main Loop ----
total_minutes = 0
for run in range(max_loop):
    try:
        # Random step between 1000 and 3000 minutes
        step_minutes = random.randint(100, 3000)
        total_minutes += step_minutes

        commit_time = start_date + timedelta(minutes=total_minutes)
        commit_message = f"AutoCommit_{random_hex_string()}"
        timestamp_str = f"{commit_time:%H.%M.%S_%m.%d.%Y}"

        print(f"[***] Run {run+1}/{max_loop} | Commit Time: {timestamp_str} | Step: {step_minutes} min")

        # Write log
        os.makedirs("log_files", exist_ok=True)
        with open(f"log_files/GITHUB_BOT_{run_id}_{current_date}.txt", 'a') as f:
            f.write(f"COMMIT_MESSAGE:{commit_message} [Run {run+1}] [Time:{timestamp_str}] [Step:{step_minutes}min] [Run_ID:{run_id}]\n")

        # Set commit timestamps (for Git history)
        os.environ["GIT_AUTHOR_DATE"] = commit_time.isoformat()
        os.environ["GIT_COMMITTER_DATE"] = commit_time.isoformat()

        git_add_commit_push(commit_message)

    except KeyboardInterrupt:
        print(f"[!] Interrupted at run {run+1}. Exiting gracefully.")
        break
