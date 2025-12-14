#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ip_pub_updater.py
- وقتی اجرا شود: صبر می‌کند تا اتصال اینترنت برقرار شود.
- آی‌پی پابلیک را می‌گیرد.
- در همان پوشه‌ای که این اسکریپت قرار دارد فایل‌هایی با الگوی
  IP-Public{n}.txt ایجاد/بروزرسانی می‌کند.
- اگر آی‌پی تغییریافته باشد، فایل‌های قبلی (مطابق الگو) حذف شده
  و فایلی با شماره‌ی بعدی ساخته می‌شود.
"""
from __future__ import annotations
import os
import re
import time
import socket
import urllib.request
from pathlib import Path
from typing import Optional

# تنظیمات
FILENAME_PREFIX = "IP-Public"   # طبق خواستهٔ تو (نگه‌داشتمش همانطور)
FILENAME_EXT = ".txt"
CHECK_INTERVAL = 5              # ثانیه بین تلاش‌ها برای اینترنت
HTTP_TIMEOUT = 8                # ثانیه تایم‌اوت برای درخواست آی‌پی
IP_SERVICES = [
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "https://icanhazip.com",
    "https://ifconfig.co/ip",
]

def get_script_folder() -> Path:
    # همان پوشه‌ای که اسکریپت در آن قرار دارد
    return Path(__file__).resolve().parent

def fetch_public_ip() -> Optional[str]:
    """سعی می‌کند آی‌پی پابلیک را از لیست سرویس‌ها بگیرد.
    اگر نتوانست None برمی‌گرداند."""
    for url in IP_SERVICES:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ip-pub-updater/1.0"})
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                raw = resp.read().decode('utf-8', errors='ignore').strip()
                # ساده‌سازی و اعتبارسنجی اولیه آی‌پی (IPv4 یا IPv6)
                if raw:
                    ip = raw.splitlines()[0].strip()
                    # حذف فضای اضافی
                    if validate_ip(ip):
                        return ip
        except Exception:
            # ناتوانی در دسترسی به این سرویس — سراغ بعدی می‌رویم
            continue
    return None

def validate_ip(ip: str) -> bool:
    """اعتبارسنجی ساده برای IPv4 یا IPv6"""
    # تلاش برای تبدیل با socket
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except OSError:
        try:
            socket.inet_pton(socket.AF_INET6, ip)
            return True
        except OSError:
            return False

def list_existing_files(folder: Path):
    """فایل‌های مطابق الگو را لیست می‌کند و شماره‌هایشان را برمی‌گرداند."""
    pattern = re.compile(rf'^{re.escape(FILENAME_PREFIX)}(\d+)(?:{re.escape(FILENAME_EXT)})?$')
    found = []
    for p in folder.iterdir():
        if p.is_file():
            m = pattern.match(p.name)
            if m:
                idx = int(m.group(1))
                found.append((idx, p))
    found.sort(key=lambda x: x[0])
    return found

def read_ip_from_file(path: Path) -> Optional[str]:
    try:
        txt = path.read_text(encoding='utf-8').strip()
        if txt:
            # اولین خط را بر می‌گردانیم
            return txt.splitlines()[0].strip()
    except Exception:
        return None
    return None

def write_ip_file(folder: Path, idx: int, ip: str) -> Path:
    fname = f"{FILENAME_PREFIX}{idx}{FILENAME_EXT}"
    p = folder / fname
    p.write_text(ip + "\n", encoding='utf-8')
    return p

def delete_files(files):
    for _, p in files:
        try:
            p.unlink()
        except Exception:
            pass

def main_once():
    folder = get_script_folder()
    # منتظر می‌مانیم تا اینترنت در دسترس شود (fetch_public_ip موفق شود)
    ip = None
    while True:
        ip = fetch_public_ip()
        if ip:
            break
        time.sleep(CHECK_INTERVAL)

    existing = list_existing_files(folder)
    if not existing:
        # هیچ فایلی وجود ندارد: بساز IP-Public1.txt
        newpath = write_ip_file(folder, 1, ip)
        print(f"No previous file. Created {newpath.name} with IP {ip}")
        return

    # فایل با بیشترین شماره را انتخاب می‌کنیم (آخرین)
    last_idx, last_path = existing[-1]
    last_ip = read_ip_from_file(last_path)

    if last_ip == ip:
        print(f"Public IP unchanged ({ip}). No action taken.")
        return

    # آی‌پی تغییر کرده: حذف همه فایل‌های قدیمی مطابق الگو و ساخت فایل جدید با شماره+1
    delete_files(existing)
    new_idx = last_idx + 1
    newpath = write_ip_file(folder, new_idx, ip)
    print(f"IP changed: old={last_ip!r}, new={ip!r}. Created {newpath.name}")

if __name__ == "__main__":
    main_once()
