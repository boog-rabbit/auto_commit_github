from git import Repo
from os import urandom
from datetime import datetime, timedelta
import random
import time
import requests
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading

# ========== CORE FUNCTIONS ==========

def random_hex_string(length=3):
    return urandom(length).hex()


def git_add_commit_push(path_of_git_repo, commit_message, log_callback=None):
    """Adds, commits, and pushes all changes to origin/main."""
    try:
        repo = Repo(path_of_git_repo)
        origin = repo.remote(name='origin')

        repo.git.add(all=True)
        if log_callback:
            log_callback("[*] git add .")

        repo.index.commit(commit_message)
        if log_callback:
            log_callback(f"[*] git commit -m {commit_message}")

        origin.push()
        if log_callback:
            log_callback(f"[*] git push -u origin main\n")
        return True
    except Exception as e:
        error_msg = f"[!] Error in git_add_commit_push(): {e}\n"
        if log_callback:
            log_callback(error_msg)
        return False


def verify_github_profile(github_profile_url, log_callback=None):
    """Verifies GitHub profile URL is accessible."""
    try:
        response = requests.get(github_profile_url, timeout=10)
        if response.status_code == 200:
            if log_callback:
                log_callback("[*] Successfully connected to GitHub profile.")
            return True
        else:
            if log_callback:
                log_callback("[!] Could not verify GitHub profile.")
            return False
    except Exception as e:
        error_msg = f"[!] Failed to fetch GitHub profile: {e}"
        if log_callback:
            log_callback(error_msg)
        return False


def run_commit_sequence(
    path_of_git_repo,
    github_profile_url,
    start_date_str,
    end_date_str,
    max_loop,
    min_minutes,
    max_minutes,
    log_callback=None,
    progress_callback=None,
    stop_event=None
):
    """Main function to run the commit sequence."""
    try:
        # Parse dates
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        else:
            start_date = datetime.now()

        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        else:
            end_date = datetime.now() - timedelta(days=1)

        run_id = random_hex_string()
        current_date = f"{start_date:%m.%d.%Y}"

        if log_callback:
            log_callback(f"\n[***] Starting commit sequence at {start_date} | Run ID: {run_id}\n")
            log_callback(f"[***] End date: {end_date.date()}\n")
            log_callback(f"[***] Random minutes range: {min_minutes} - {max_minutes}\n\n")

        # Verify GitHub profile
        verify_github_profile(github_profile_url, log_callback)

        # Main Loop
        total_minutes = 0
        successful_commits = 0
        
        for run in range(max_loop):
            if stop_event and stop_event.is_set():
                if log_callback:
                    log_callback(f"[!] Stopped by user at run {run+1}.\n")
                break

            try:
                # Random step between min_minutes and max_minutes
                step_minutes = random.randint(min_minutes, max_minutes)
                total_minutes += step_minutes

                commit_time = start_date + timedelta(minutes=total_minutes)
                commit_message = f"AutoCommit_{random_hex_string()}"
                timestamp_str = f"{commit_time:%H.%M.%S_%m.%d.%Y}"

                # Stop condition: commit_time reached end_date
                if commit_time.date() >= end_date.date():
                    if log_callback:
                        log_callback(f"[!] STOPPING — commit time {commit_time.date()} reached end date ({end_date.date()}).\n")
                    break

                if log_callback:
                    log_callback(f"[***] Run {run+1}/{max_loop} | Commit Time: {timestamp_str} | Step: {step_minutes} min")

                # Write log
                os.makedirs("log_files", exist_ok=True)
                with open(f"log_files/GITHUB_BOT_{run_id}_{current_date}.txt", 'a') as f:
                    f.write(
                        f"COMMIT_MESSAGE:{commit_message} [Run {run+1}] "
                        f"[Time:{timestamp_str}] [Step:{step_minutes}min] [Run_ID:{run_id}]\n"
                    )

                # Set commit timestamps for Git history
                os.environ["GIT_AUTHOR_DATE"] = commit_time.isoformat()
                os.environ["GIT_COMMITTER_DATE"] = commit_time.isoformat()

                if git_add_commit_push(path_of_git_repo, commit_message, log_callback):
                    successful_commits += 1

                if progress_callback:
                    progress_callback(run + 1, max_loop)

            except Exception as e:
                error_msg = f"[!] Error in run {run+1}: {e}\n"
                if log_callback:
                    log_callback(error_msg)

        if log_callback:
            log_callback(f"\n[***] Completed! Successful commits: {successful_commits}/{run+1}\n")
        
        return successful_commits

    except Exception as e:
        error_msg = f"[!] Fatal error: {e}\n"
        if log_callback:
            log_callback(error_msg)
        return 0


# ========== GUI APPLICATION ==========

class GitBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Commit Bot")
        self.root.geometry("800x700")
        self.root.resizable(True, True)

        # Variables
        self.is_running = False
        self.stop_event = None
        self.worker_thread = None

        # Style
        style = ttk.Style()
        style.theme_use('clam')

        # Main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="GitHub Commit Bot", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Path of Git Repo
        ttk.Label(main_frame, text="Git Repo Path:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.repo_path_var = tk.StringVar(value=r'C:\Users\BOOG\Documents\chatting_application\.git')
        repo_frame = ttk.Frame(main_frame)
        repo_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        repo_frame.columnconfigure(0, weight=1)
        self.repo_path_entry = ttk.Entry(repo_frame, textvariable=self.repo_path_var, width=50)
        self.repo_path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(repo_frame, text="Browse", command=self.browse_repo_path).grid(row=0, column=1)

        # GitHub Profile URL
        ttk.Label(main_frame, text="GitHub Profile URL:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.github_url_var = tk.StringVar(value="https://github.com/vladyslavfilippov-77")
        ttk.Entry(main_frame, textvariable=self.github_url_var, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)

        # Start Date
        ttk.Label(main_frame, text="Start Date (YYYY-MM-DD):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.start_date_var = tk.StringVar(value="2025-09-25")
        ttk.Entry(main_frame, textvariable=self.start_date_var, width=50).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(main_frame, text="(Leave empty for today)", font=("Arial", 8)).grid(row=4, column=1, sticky=tk.W)

        # End Date
        ttk.Label(main_frame, text="End Date (YYYY-MM-DD):").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.end_date_var = tk.StringVar(value="")
        ttk.Entry(main_frame, textvariable=self.end_date_var, width=50).grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(main_frame, text="(Leave empty for yesterday)", font=("Arial", 8)).grid(row=6, column=1, sticky=tk.W)

        # Max Loop
        ttk.Label(main_frame, text="Max Commits:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.max_loop_var = tk.StringVar(value="50")
        ttk.Entry(main_frame, textvariable=self.max_loop_var, width=50).grid(row=7, column=1, sticky=(tk.W, tk.E), pady=5)

        # Random Minutes Range
        ttk.Label(main_frame, text="Random Minutes Range:").grid(row=8, column=0, sticky=tk.W, pady=5)
        range_frame = ttk.Frame(main_frame)
        range_frame.grid(row=8, column=1, sticky=(tk.W, tk.E), pady=5)
        self.min_minutes_var = tk.StringVar(value="100")
        self.max_minutes_var = tk.StringVar(value="3000")
        ttk.Label(range_frame, text="Min:").grid(row=0, column=0, padx=(0, 5))
        ttk.Entry(range_frame, textvariable=self.min_minutes_var, width=15).grid(row=0, column=1, padx=(0, 10))
        ttk.Label(range_frame, text="Max:").grid(row=0, column=2, padx=(0, 5))
        ttk.Entry(range_frame, textvariable=self.max_minutes_var, width=15).grid(row=0, column=3)

        # Progress Bar
        ttk.Label(main_frame, text="Progress:").grid(row=9, column=0, sticky=tk.W, pady=5)
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_label = ttk.Label(main_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=9, column=1, sticky=tk.W, pady=5)
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=11, column=0, columnspan=2, pady=10)
        self.start_button = ttk.Button(button_frame, text="Start", command=self.start_commit_sequence, width=15)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_commit_sequence, state=tk.DISABLED, width=15)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Log Output
        ttk.Label(main_frame, text="Log Output:").grid(row=12, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        self.log_text = scrolledtext.ScrolledText(main_frame, height=15, width=80, wrap=tk.WORD)
        self.log_text.grid(row=13, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(13, weight=1)

    def browse_repo_path(self):
        """Open file dialog to select .git folder."""
        path = filedialog.askdirectory(title="Select Git Repository Folder")
        if path:
            # Check if .git folder exists
            git_path = os.path.join(path, '.git')
            if os.path.exists(git_path):
                self.repo_path_var.set(git_path)
            else:
                # Try using the selected path as .git path
                if os.path.exists(path) and os.path.basename(path) == '.git':
                    self.repo_path_var.set(path)
                else:
                    messagebox.showwarning("Warning", "Selected folder doesn't contain a .git directory. Using selected path anyway.")

    def log(self, message):
        """Append message to log text area."""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def update_progress(self, current, total):
        """Update progress bar and label."""
        self.progress_var.set(f"Progress: {current}/{total}")
        self.progress_bar['maximum'] = total
        self.progress_bar['value'] = current
        self.root.update_idletasks()

    def validate_inputs(self):
        """Validate all input fields."""
        errors = []

        # Validate repo path
        repo_path = self.repo_path_var.get().strip()
        if not repo_path:
            errors.append("Git Repo Path is required")
        elif not os.path.exists(repo_path):
            errors.append(f"Git Repo Path does not exist: {repo_path}")

        # Validate GitHub URL
        github_url = self.github_url_var.get().strip()
        if not github_url:
            errors.append("GitHub Profile URL is required")
        elif not github_url.startswith("http"):
            errors.append("GitHub Profile URL must start with http:// or https://")

        # Validate dates
        start_date_str = self.start_date_var.get().strip()
        if start_date_str:
            try:
                datetime.strptime(start_date_str, "%Y-%m-%d")
            except ValueError:
                errors.append("Start Date must be in YYYY-MM-DD format")

        end_date_str = self.end_date_var.get().strip()
        if end_date_str:
            try:
                datetime.strptime(end_date_str, "%Y-%m-%d")
            except ValueError:
                errors.append("End Date must be in YYYY-MM-DD format")

        # Validate max loop
        try:
            max_loop = int(self.max_loop_var.get().strip())
            if max_loop <= 0:
                errors.append("Max Commits must be greater than 0")
        except ValueError:
            errors.append("Max Commits must be a valid number")

        # Validate minutes range
        try:
            min_minutes = int(self.min_minutes_var.get().strip())
            max_minutes = int(self.max_minutes_var.get().strip())
            if min_minutes < 0 or max_minutes < 0:
                errors.append("Minutes values must be non-negative")
            if min_minutes > max_minutes:
                errors.append("Min minutes must be less than or equal to max minutes")
        except ValueError:
            errors.append("Minutes range must be valid numbers")

        return errors

    def start_commit_sequence(self):
        """Start the commit sequence in a separate thread."""
        errors = self.validate_inputs()
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return

        self.is_running = True
        self.stop_event = threading.Event()
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.progress_bar['value'] = 0

        # Get values
        repo_path = self.repo_path_var.get().strip()
        github_url = self.github_url_var.get().strip()
        start_date_str = self.start_date_var.get().strip() or None
        end_date_str = self.end_date_var.get().strip() or None
        max_loop = int(self.max_loop_var.get().strip())
        min_minutes = int(self.min_minutes_var.get().strip())
        max_minutes = int(self.max_minutes_var.get().strip())

        # Start worker thread
        self.worker_thread = threading.Thread(
            target=run_commit_sequence,
            args=(
                repo_path,
                github_url,
                start_date_str,
                end_date_str,
                max_loop,
                min_minutes,
                max_minutes,
                self.log,
                self.update_progress,
                self.stop_event
            ),
            daemon=True
        )
        self.worker_thread.start()

        # Check thread completion
        self.check_thread_completion()

    def check_thread_completion(self):
        """Check if worker thread has completed."""
        if self.worker_thread and self.worker_thread.is_alive():
            self.root.after(100, self.check_thread_completion)
        else:
            self.is_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            if self.stop_event and not self.stop_event.is_set():
                self.log("\n[***] Commit sequence completed successfully!")

    def stop_commit_sequence(self):
        """Stop the commit sequence."""
        if self.stop_event:
            self.stop_event.set()
            self.log("\n[!] Stop requested. Waiting for current commit to finish...")
            self.stop_button.config(state=tk.DISABLED)


# ========== MAIN ENTRY POINT ==========

if __name__ == "__main__":
    root = tk.Tk()
    app = GitBotGUI(root)
    root.mainloop()
