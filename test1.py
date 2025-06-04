"""
RED Safe API 互動測試腳本（依據 C++ Required Keys）

啟動後會列出可測試的 endpoint，輸入對應數字選擇，腳本將顯示每個 required key 的名稱，並提示輸入對應值。
可選欄位若留空則不加入請求。直接按 0 或輸入非數字結束程式。
"""

import os
import requests
import json
import sys

# 使用 Session 以自動管理 Cookie
session = requests.Session()

BASE_URL = os.getenv("REDSAFE_BASE_URL", "https://127.0.0.1")

# 全域快取，從 Set-Cookie 解析到的 refresh_token
CACHED_REFRESH_TOKEN: str | None = None

# 定義每個 endpoint 對應的 required 與 optional keys
ENDPOINT_KEY_CONFIG = {
    "/edge/signup": {
        "required": ["serial_number", "version"],
        "optional": []
    },
    "/user/signup": {
        "required": ["email", "user_name", "password"],
        "optional": []
    },
    "/user/signin": {
        "required": ["email", "password"],
        "optional": []
    },
    "/ios/signup": {
        "required": ["user_id", "apns_token"],
        "optional": ["ios_device_id", "device_name"]
    },
    "/ios/bind": {
        "required": ["user_id", "serial_number"],
        "optional": []
    },
    "/ios/unbind": {
        "required": ["user_id", "serial_number"],
        "optional": []
    },
    "/auth/refresh": {
        "required": [],
        "optional": []
    },
    "/auth/out": {
        "required": [],
        "optional": []
    },
    "/user/all": {
        "required": [],
        "optional": []
    },
}

ENDPOINTS = list(ENDPOINT_KEY_CONFIG.keys())

def _post(path: str, json_body: dict | None = None, token: str | None = None):
    """
    發送 POST 請求並完整列印 Raw HTTP Request / Response
    """
    # --------- 準備 Request -------------
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = requests.Request(
        method="POST",
        url=f"{BASE_URL}{path}",
        json=json_body or {},
        headers=headers,
    )
    prepared = session.prepare_request(req)

    # --------- 列印 Raw Request -------------
    from urllib.parse import urlparse
    parsed = urlparse(prepared.url)
    request_path = parsed.path or "/"
    if parsed.query:
        request_path += "?" + parsed.query
    print("\n" + prepared.method, request_path, "HTTP/1.1")
    # 依照 RFC2616，Host 必須第一行 header
    if "Host" in prepared.headers:
        print(f"Host: {prepared.headers['Host']}")
    # 其餘 Header 順序列印
    for k, v in prepared.headers.items():
        if k.lower() == "host":
            continue
        print(f"{k}: {v}")
    # Body
    print()
    body_to_print = prepared.body
    if isinstance(body_to_print, bytes):
        try:
            body_to_print = body_to_print.decode()
        except Exception:
            pass
    if body_to_print:
        try:
            parsed_json = json.loads(body_to_print)
            print(json.dumps(parsed_json, ensure_ascii=False, indent=2))
        except Exception:
            print(body_to_print)
    else:
        print("{}")
    print("----------------------------")

    # --------- 發送 -------------
    try:
        resp = session.send(prepared, timeout=10, verify=False)
    except Exception as e:
        print(f"Request error: {e}")
        return None

    # --------- 列印 Raw Response -------------
    reason = resp.reason or ""
    print(f"\nHTTP/1.1 {resp.status_code} {reason}")
    for k, v in resp.headers.items():
        print(f"{k}: {v}")
    print()
    try:
        parsed_body = resp.json()
        print(json.dumps(parsed_body, ensure_ascii=False, indent=2))
    except ValueError:
        print(resp.text)
    print("----------------------------")

    # --------- 快取 Refresh Token -------------
    rt = resp.cookies.get("refresh_token")
    if rt:
        global CACHED_REFRESH_TOKEN
        CACHED_REFRESH_TOKEN = rt
        print(f"[Info] Refresh Token cached: {rt}")

    return resp

def _get(path: str, token: str | None = None):
    """
    發送 GET 請求並完整列印 Raw HTTP Request / Response
    """
    # --------- 準備 Request -------------
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{BASE_URL}{path}"
    from urllib.parse import urlparse
    parsed = urlparse(url)
    request_path = parsed.path or "/"
    if parsed.query:
        request_path += "?" + parsed.query

    # 列印 Raw Request
    print("\nGET", request_path, "HTTP/1.1")
    if "Host" in parsed.netloc:
        host_header = parsed.netloc
    else:
        host_header = parsed.netloc
    print(f"Host: {host_header}")
    for k, v in headers.items():
        print(f"{k}: {v}")
    print()
    print("{}")
    print("----------------------------")

    # --------- 發送 -------------
    try:
        resp = session.get(url, headers=headers, timeout=10, verify=False)
    except Exception as e:
        print(f"Request error: {e}")
        return None

    # 列印 Raw Response
    reason = resp.reason or ""
    print(f"\nHTTP/1.1 {resp.status_code} {reason}")
    for k, v in resp.headers.items():
        print(f"{k}: {v}")
    print()
    try:
        parsed_body = resp.json()
        print(json.dumps(parsed_body, ensure_ascii=False, indent=2))
    except ValueError:
        print(resp.text)
    print("----------------------------")

    return resp

def prompt_for_keys(endpoint: str):
    """
    根據 ENDPOINT_KEY_CONFIG，提示使用者輸入 required/optional keys 的值
    回傳 dict，只包含非空值
    """
    config = ENDPOINT_KEY_CONFIG.get(endpoint, {})
    body = {}
    # 先處理 required keys
    for key in config.get("required", []):
        while True:
            value = input(f"請輸入 {key}（必要）: ").strip()
            if value == "":
                print(f"{key} 為必要欄位，請勿留空。")
            else:
                body[key] = value
                break
    # 處理 optional keys
    for key in config.get("optional", []):
        value = input(f"請輸入 {key}（選填，可留空）: ").strip()
        if value != "":
            body[key] = value
    return body

def main():
    print("=== RED Safe API 互動測試 ===")
    print(f"伺服器網址: {BASE_URL}")
    while True:
        print("\n可測試的 endpoint：")
        for idx, ep in enumerate(ENDPOINTS, start=1):
            print(f"  {idx}. {ep}")
        print("  0. 離開")

        choice = input("請輸入要測試的編號 (0 離開): ").strip()
        if not choice.isdigit():
            break
        choice_num = int(choice)
        if choice_num == 0:
            break
        if choice_num < 0 or choice_num > len(ENDPOINTS):
            print("無效的選擇，請重新輸入。")
            continue

        path = ENDPOINTS[choice_num - 1]

        # 處理 GET /user/all
        if path == "/user/all":
            token = input("請輸入 Bearer Token (必要): ").strip()
            if not token:
                print("Access Token 為必要欄位，請重新輸入。")
                continue
            _get(path, token)
            continue

        # 特殊處理 /auth/refresh，不需要 body，直接用 session cookie
        if path == "/auth/refresh":
            # 直接使用之前快取的 Cookie 自動帶 refresh_token，無需手動輸入
            if CACHED_REFRESH_TOKEN is None:
                print("目前沒有快取 Refresh Token，請先執行 signin 以獲取。")
                continue
            _post(path, None, None)
            continue

        # 特殊處理 /auth/out，不需要 body，直接帶 Cookie 登出
        if path == "/auth/out":
            # 使用 session cookie 自動帶 refresh_token
            _post(path, None, None)
            continue

        # 其他 endpoint 提示輸入欄位
        body = prompt_for_keys(path)
        token = input("請輸入 Bearer Token (選填，可留空): ").strip()
        _post(path, body, token or None)
    print("Bye.")

if __name__ == "__main__":
    main()