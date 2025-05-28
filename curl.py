#!/usr/bin/env python3
import json
import sys
import requests
from typing import Optional, List

VERIFY_SSL = False
BASE_URL = "https://113.61.152.89:30678"

# 固定參數
EDGE_SERIAL  = "RED-AAAAAABB"
EDGE_VERSION = "1.0.0"
APNS_TOKEN   = "3f2ab11e0b213d1e8f9a0a2c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e"
DEVICE_NAME  = "iPhone 1"
HEADERS      = {"Content-Type": "application/json"}

token: Optional[str] = None  # JWT from /user/login
serial_numbers: List[str] = []  # 存放登入後取得的序號清單

def die(msg: str, resp: Optional[requests.Response] = None) -> None:
    """列印錯誤訊息，不結束程式；按 Enter 回選單"""
    if resp is not None:
        msg += f"\nHTTP {resp.status_code}\n{resp.text}"
    print("\n=== 發生錯誤 ===", file=sys.stderr)
    print(msg, file=sys.stderr)
    input("按 Enter 回到選單...")

# 全域暫存 user_id 與 ios_device_id，方便後續步驟使用
user_id: Optional[str] = None
ios_device_id: Optional[str] = None
user_name_cached: Optional[str] = None

def edge_register() -> None:
    payload = {"version": EDGE_VERSION, "serial_number": EDGE_SERIAL}
    r = requests.post(f"{BASE_URL}/edge/signup",
                      headers=HEADERS, json=payload, verify=VERIFY_SSL)
    print(f"edge/register → HTTP {r.status_code}")
    print(r.text)

def user_register() -> None:
    global user_id
    global user_name_cached
    email      = input("Email: ")
    user_name  = input("User name: ")
    password   = input("Password: ")
    payload = {"email": email, "user_name": user_name, "password": password}
    r = requests.post(f"{BASE_URL}/user/signup",
                      headers=HEADERS, json=payload, verify=VERIFY_SSL)
    if not r.ok:
        die("user/register 失敗！", r)
        return
    user_id = r.json().get("user_id")
    user_name_cached = user_name
    print(f"user_id = {user_id}")

def ios_register() -> None:
    global ios_device_id
    if not user_id:
        print("請先完成 user/register 取得 user_id")
        return
    ios_device_id_input = input("iOS device id (留空表示初次註冊): ").strip()
    payload = {
        "ios_device_id": ios_device_id_input,
        "user_id":       user_id,
        "apns_token":    APNS_TOKEN,
        "device_name":   DEVICE_NAME
    }
    r = requests.post(f"{BASE_URL}/ios/signup",
                      headers=HEADERS, json=payload, verify=VERIFY_SSL)
    if not r.ok:
        die("ios/register 失敗！", r)
        return
    ios_device_id = r.json().get("ios_device_id")
    print(f"ios_device_id = {ios_device_id}")

def user_login() -> None:
    """登入並取得 JWT"""
    global user_id, token
    global user_name_cached
    email    = input("Email: ")
    password = input("Password: ")
    payload  = {"email": email, "password": password}
    r = requests.post(f"{BASE_URL}/user/signin",
                      headers=HEADERS, json=payload, verify=VERIFY_SSL)
    if not r.ok:
        die("user/login 失敗！", r)
        return
    data     = r.json()
    token    = data.get("token")
    user_id  = data.get("user_id")
    user_name_cached = data.get("user_name")
    serial_numbers[:] = data.get("serial_number", [])  # 取出序號陣列
    print("登入成功！")
    print(f"user_id   = {user_id}")
    if user_name_cached:
        print(f"user_name = {user_name_cached}")
    print(f"JWT      = {token}")
    if serial_numbers:
        print("已綁定 Edge 序號：")
        for sn in serial_numbers:
            print(f"  • {sn}")
    else:
        print("此帳號尚未綁定任何 Edge")

def ios_bind() -> None:
    if not (user_id and ios_device_id):
        print("請先完成 user 和 iOS 註冊")
        return
    payload = {"serial_number": EDGE_SERIAL, "user_id": user_id}
    r = requests.post(f"{BASE_URL}/ios/bind",
                      headers=HEADERS, json=payload, verify=VERIFY_SSL)
    if not r.ok:
        die("ios/bind 失敗！", r)
        return
    print("綁定成功！")

def menu() -> None:
    print(
        "\n=== API 測試選單 ===\n"
        "1) edge/register\n"
        "2) user/register\n"
        "3) ios/register\n"
        "4) ios/bind\n"
        "5) user/login\n"
        "6) 顯示目前序號清單\n"
        "q) 離開\n"
    )

def main() -> None:
    while True:
        menu()
        choice = input("請輸入選項: ").strip()
        if choice == "1":
            edge_register()
        elif choice == "2":
            user_register()
        elif choice == "3":
            ios_register()
        elif choice == "4":
            ios_bind()
        elif choice == "5":
            user_login()
        elif choice == "6":
            print("目前使用者資訊：")
            print(f"  user_id   : {user_id or '未知'}")
            print(f"  user_name : {user_name_cached or '未知'}")
            if serial_numbers:
                print("  序號清單：")
                for sn in serial_numbers:
                    print(f"    • {sn}")
            else:
                print("  尚無序號")
        elif choice.lower() == "q":
            print("Bye!")
            break
        else:
            print("無效選項，請重新輸入")

if __name__ == "__main__":
    main()