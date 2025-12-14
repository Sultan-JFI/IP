import os
import json
import subprocess
import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime

CONFIG_FILE = ".git_autopush_config.json"

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    return result.stdout.strip(), result.stderr.strip()

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

def get_git_status():
    stdout, stderr = run_command("git status --porcelain")
    if stderr:
        return None
    return stdout

def ensure_git_initialized(config):
    if not os.path.exists('.git'):
        messagebox.showinfo("Git Setup", "مخزن گیت در این پوشه پیدا نشد. در حال راه‌اندازی...")
        run_command("git init")
        name = config.get('username') or simpledialog.askstring("Git Config", "نام کاربری گیت هاب خود را وارد کنید:")
        email = config.get('email') or simpledialog.askstring("Git Config", "ایمیل گیت هاب خود را وارد کنید:")
        run_command(f"git config user.name \"{name}\"")
        run_command(f"git config user.email \"{email}\"")
        repo_url = simpledialog.askstring("GitHub Repo", "نشانی (URL) مخزن گیت‌هاب را وارد کنید:")
        run_command(f"git remote add origin {repo_url}")
        config.update({'username': name, 'email': email, 'repo_url': repo_url})
        save_config(config)
        messagebox.showinfo("Git Initialized", "مخزن گیت راه‌اندازی شد و آماده استفاده است.")

def commit_and_push_changes(config):
    status = get_git_status()
    if status is None:
        messagebox.showerror("Error", "گیت در این پوشه فعال نیست.")
        return
    if not status:
        messagebox.showinfo("No Changes", "هیچ تغییری برای ثبت وجود ندارد.")
        return
    run_command("git add .")
    auto_message = f"به‌روزرسانی خودکار در {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    user_message = simpledialog.askstring("Commit Message", f"پیام پیش‌فرض: {auto_message}\nمی‌خواهید پیام دیگری بنویسید؟ (خالی بگذارید تا از پیش‌فرض استفاده شود)")
    commit_message = user_message if user_message else auto_message
    run_command(f'git commit -m "{commit_message}"')
    stdout, stderr = run_command("git push origin master")
    if stderr:
        messagebox.showerror("Push Error", f"خطا در پوش: {stderr}")
    else:
        messagebox.showinfo("Success", "تغییرات با موفقیت به گیت‌هاب ارسال شد.")

def main():
    root = tk.Tk()
    root.withdraw()
    config = load_config()
    ensure_git_initialized(config)
    commit_and_push_changes(config)
    root.destroy()

if __name__ == '__main__':
    main()
