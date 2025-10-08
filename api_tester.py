#!/usr/bin/env python3
"""
API Tester — Quick script to send GET or POST requests
"""
import json
import requests

def main():
    url = input("Enter API URL: ").strip()
    method = input("Method (GET/POST): ").strip().upper()

    if method == "POST":
        payload = input("Enter JSON payload: ")
        data = json.loads(payload)
        res = requests.post(url, json=data)
    else:
        res = requests.get(url)

    print("\n📡 Response:")
    print("Status:", res.status_code)
    print("Headers:", res.headers)
    print("Body:", res.text[:1000])

if __name__ == "__main__":
    main()
