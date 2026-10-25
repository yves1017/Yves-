import os
import datetime
import requests

FIREBASE_URL = "https://shopee-da43f-default-rtdb.firebaseio.com/yves_shop_data.json"

def clean_expired():
    response = requests.get(FIREBASE_URL)
    if response.status_code != 200:
        print("Failed to fetch Firebase data")
        return

    data = response.json()
    if not data:
        return

    now = datetime.datetime.now(datetime.timezone.utc)
    products = data.get("products", [])
    valid_products = []

    for p in products:
        expiry = p.get("expiry")
        if expiry:
            try:
                expiry_dt = datetime.datetime.fromisoformat(expiry).replace(tzinfo=datetime.timezone.utc)
                if expiry_dt <= now:
                    print(f"Removing expired product: {p.get('name')}")
                    continue
            except Exception as e:
                pass
        valid_products.append(p)

    data["products"] = valid_products
    data["lastUpdated"] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M") + " (Auto Cleaned)"

    put_resp = requests.put(FIREBASE_URL, json=data)
    if put_resp.status_code == 200:
        print("Successfully cleaned expired items and updated Firebase.")

if __name__ == "__main__":
    clean_expired()