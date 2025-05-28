import requests
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

import threading
_thread_local = threading.local()

MODE = int(input("Enter mode (1 for URL1, 2 for URL2): "))

def get_session():
    if not hasattr(_thread_local, 'session'):
        s = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=1,
            pool_maxsize=1,
            max_retries=0,
            pool_block=True
        )
        s.mount("https://", adapter)
        s.verify = False
        _thread_local.session = s
    return _thread_local.session

URL1 = "https://127.0.0.1/edge/signin"
URL2 = "https://113.61.152.89:30678/edge/signup"
TOTAL_REQUESTS = 10000 
CONCURRENCY = 20      

def generate_serial_number() -> str:
    """產生格式 RED-XXXXXXXX 的隨機大寫十六進位序號。"""
    hex_chars = "0123456789ABCDEF"
    body = ''.join(random.choice(hex_chars) for _ in range(8))
    return f"RED-{body}"

def make_request(idx: int):
    payload = {
        "version": "1.0.0",
        "serial_number": generate_serial_number()
    }
    try:
        session = get_session()
        if MODE == 1:
            r = session.post(URL1, json=payload, timeout=10)
        elif MODE == 2:
            r = session.post(URL2, json=payload, timeout=10)
        else:
            # default to URL1 if invalid mode
            r = session.post(URL1, json=payload, timeout=10)
        return r.status_code, r.text
    except Exception as e:
        return None, str(e)

def main():
    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = [
            executor.submit(make_request, i)
            for i in range(TOTAL_REQUESTS)
        ]
        for future in as_completed(futures):
            status, body = future.result()
            
            if status is None:
                print("Error:", body)
            else:
                print("OK:", status, body)

    duration = time.perf_counter() - start
    print(f"Completed {TOTAL_REQUESTS} requests in {duration:.2f}s "
          f"({TOTAL_REQUESTS/duration:.1f} RPS)")

main()