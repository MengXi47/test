#!/usr/bin/env python3
import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

URL = "https://113.61.152.89:30678/edge/register"
JSON_PAYLOAD = {"version": "RED-AAAAAABB", "serial_number": "1.0.0"}
TOTAL_REQUESTS = 30   # 總共要發送的請求數
CONCURRENCY = 1       # 同時併發的執行緒數

def make_request(session: requests.Session, idx: int):
    try:
        # post 時自動使用 session 維持的連線（不會每次握手）
        r = session.post(URL, json=JSON_PAYLOAD, timeout=10)
        return r.status_code, r.text
    except Exception as e:
        return None, str(e)

def main():
    # 允許 urllib3 重用連線
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=CONCURRENCY,
        pool_maxsize=CONCURRENCY,
        max_retries=0,
        pool_block=True
    )
    session.mount("https://", adapter)
    session.verify = False  # 若是自簽證書，可關閉驗證；正式環境請改正憑證

    start = time.perf_counter()

    # 使用 ThreadPoolExecutor 來排並發請求
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = [
            executor.submit(make_request, session, i)
            for i in range(TOTAL_REQUESTS)
        ]
        # 可視需要印出結果或錯誤
        for future in as_completed(futures):
            status, body = future.result()
            # if status is None:
            #     print("Error:", body)
            # else:
            #     print("OK:", status)

    duration = time.perf_counter() - start
    print(f"Completed {TOTAL_REQUESTS} requests in {duration:.2f}s "
          f"({TOTAL_REQUESTS/duration:.1f} RPS)")

main()