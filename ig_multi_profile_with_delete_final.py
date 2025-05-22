
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import configparser
import tkinter as tk
import threading
import os
import time
from webdriver_manager.chrome import ChromeDriverManager

CONFIG_FILE = "credentials.txt"
is_paused = False
status_label = None

def load_profiles(config_file):
    config = configparser.ConfigParser()
    config.read(config_file, encoding='utf-8')
    return config

def input_or_keep(prompt, default):
    val = input(f"{prompt}（按 Enter 保留目前值：{default}）：").strip()
    return val if val else default

def edit_profile(config):
    print("\n✏️ 可編輯帳號：")
    for i, section in enumerate(config.sections()):
        print(f"{i+1}. {section}")
    idx = input("請選擇要編輯的帳號編號：").strip()
    if not idx.isdigit() or int(idx) < 1 or int(idx) > len(config.sections()):
        print("❌ 無效選擇")
        return
    section = config.sections()[int(idx)-1]
    data = config[section]
    print(f"正在編輯 [{section}] ...")
    data["username"] = input_or_keep("Instagram 帳號", data.get("username", ""))
    data["password"] = input_or_keep("Instagram 密碼", data.get("password", ""))
    data["dm_url"] = input_or_keep("聊天室 URL", data.get("dm_url", ""))
    data["dm_note"] = input_or_keep("聊天室說明（選填）", data.get("dm_note", ""))
    data["message"] = input_or_keep("發送訊息內容", data.get("message", ""))

    with open(CONFIG_FILE, "w", encoding='utf-8') as f:
        config.write(f)
    print("✅ 編輯完成，請重新選擇設定檔")

def delete_profile(config):
    print("\n🗑️ 可刪除帳號：")
    for i, section in enumerate(config.sections()):
        print(f"{i+1}. {section}")
    idx = input("請選擇要刪除的帳號編號：").strip()
    if not idx.isdigit() or int(idx) < 1 or int(idx) > len(config.sections()):
        print("❌ 無效選擇")
        return
    section = config.sections()[int(idx)-1]
    confirm = input(f"⚠️ 確定要刪除 [{section}]？輸入 yes 確認：").strip().lower()
    if confirm == "yes":
        config.remove_section(section)
        with open(CONFIG_FILE, "w", encoding='utf-8') as f:
            config.write(f)
        print("✅ 已刪除設定檔")
    else:
        print("❌ 取消刪除")

def create_new_profile(config):
    section_name = input("請輸入新設定檔名稱：").strip()
    if section_name in config.sections():
        print("❗ 此名稱已存在")
        return
    username = input("Instagram 帳號：").strip()
    password = input("Instagram 密碼：").strip()
    dm_url = input("聊天室 URL：https://www.instagram.com/direct/t/...：").strip()
    dm_note = input("聊天室說明（選填）：").strip()
    message = input("要發送的訊息內容：").strip()

    config[section_name] = {
        "username": username,
        "password": password,
        "dm_url": dm_url,
        "dm_note": dm_note,
        "message": message
    }

    with open(CONFIG_FILE, "w", encoding='utf-8') as configfile:
        config.write(configfile)
    print("✅ 新設定檔已儲存")

def select_profile(config):
    while True:
        print("\n💼 可用帳號清單：")
        for i, section in enumerate(config.sections()):
            note = f"（{config[section].get('dm_note', '')}）" if config[section].get("dm_note") else ""
            print(f"{i+1}. {section} {note}")
        print(f"{len(config.sections())+1}. ➕ 新增設定檔")
        print(f"{len(config.sections())+2}. ✏️ 編輯設定檔")
        print(f"{len(config.sections())+3}. 🗑️ 刪除設定檔")

        choice = input("\n請輸入要使用的編號：").strip()
        if choice == str(len(config.sections())+1):
            create_new_profile(config)
        elif choice == str(len(config.sections())+2):
            edit_profile(config)
        elif choice == str(len(config.sections())+3):
            delete_profile(config)
        elif choice.isdigit() and 1 <= int(choice) <= len(config.sections()):
            return config[config.sections()[int(choice)-1]]
        else:
            print("❌ 無效選擇，請重試")

def pause():
    global is_paused
    is_paused = True
    status_label.config(text="狀態：暫停中")

def resume():
    global is_paused
    is_paused = False
    status_label.config(text="狀態：運行中")

def handle_notification_popup(driver):
    try:
        not_now_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '稍後再說') or contains(text(), 'Not Now')]"))
        )
        not_now_btn.click()
        time.sleep(2)
    except:
        pass

def send_dm(profile):
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get("https://www.instagram.com/")
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "username")))
    driver.find_element(By.NAME, "username").send_keys(profile["username"])
    driver.find_element(By.NAME, "password").send_keys(profile["password"] + Keys.RETURN)
    time.sleep(5)

    driver.get(profile["dm_url"])
    WebDriverWait(driver, 20).until(EC.url_contains("direct/t/"))
    time.sleep(2)
    handle_notification_popup(driver)

    msg_count = 0
    while True:
        if is_paused:
            time.sleep(1)
            continue
        msg_count += 1
        try:
            box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='textbox' and @aria-label='訊息']"))
            )
            box.send_keys(profile["message"])
            send_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and text()='Send']"))
            )
            send_btn.click()
            print(f"✅ 發送第 {msg_count} 條訊息")
        except Exception as e:
            print(f"❌ 發送失敗：{e}")
            break

def launch_gui(profile):
    global status_label
    root = tk.Tk()
    root.title("IG 發送控制器")
    root.geometry("240x120")
    tk.Button(root, text="暫停", command=pause).pack(pady=5)
    tk.Button(root, text="繼續", command=resume).pack(pady=5)
    status_label = tk.Label(root, text="狀態：運行中")
    status_label.pack(pady=5)
    threading.Thread(target=send_dm, args=(profile,), daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    config = load_profiles(CONFIG_FILE)
    selected = select_profile(config)
    launch_gui(selected)
