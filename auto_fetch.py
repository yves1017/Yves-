import os
import time
import requests

FIREBASE_DATABASE_URL = "https://shopee-da43f-default-rtdb.firebaseio.com"

def fetch_shopee_deals():
    timestamp = int(time.time())
    readable_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    print(f"🚀 [{readable_time}] 開始抓取蝦皮熱門商品真實資料...")
    
    # 模擬完整瀏覽器請求 Header，避免被蝦皮擋爬蟲
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://shopee.tw/search?keyword=%E7%86%B1%E9%8A%B7",
        "X-Shopee-Language": "zh-Hant"
    }
    
    # 使用蝦皮關鍵字搜尋 API 抓取熱銷商品
    shopee_api_url = "https://shopee.tw/api/v4/search/search_items?by=sales&keyword=%E7%86%B1%E9%8A%B7&limit=5&newest=0&order=desc"
    
    fetched_products = []
    
    try:
        res = requests.get(shopee_api_url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            items = data.get("items", [])
            
            for index, item_data in enumerate(items[:5]):
                item = item_data.get("item_basic", {})
                item_id = item.get("itemid")
                shop_id = item.get("shopid")
                name = item.get("name", "")
                
                if not item_id or not shop_id or not name:
                    continue
                
                # 價格處理 (蝦皮 API 價格除以 100000)
                price_raw = item.get("price", 0)
                price_before_raw = item.get("price_before_discount", price_raw)
                
                promo_price = int(price_raw / 100000) if price_raw > 100000 else int(price_raw)
                original_price = int(price_before_raw / 100000) if price_before_raw > 100000 else int(price_raw)
                if original_price < promo_price or original_price == 0:
                    original_price = promo_price
                
                # 圖片處理
                image_hash = item.get("image", "")
                image_url = f"https://down-tw.img.susercontent.com/file/{image_hash}" if image_hash else "https://via.placeholder.com/600"
                
                # 個別商品真實專屬網址 (非官網首頁)
                raw_product_link = f"https://shopee.tw/product/{shop_id}/{item_id}"
                
                fetched_products.append({
                    "id": timestamp + index,
                    "name": name,
                    "platform": "SHOPEE",
                    "category": "熱門爆款",
                    "badge": "HOT",
                    "originalPrice": original_price,
                    "promoPrice": promo_price,
                    "image": image_url,
                    "link": raw_product_link,
                    "code": "",
                    "clicks": 0
                })
            print(f"✅ 順利抓取到 {len(fetched_products)} 項真實熱銷商品！")
        else:
            print(f"⚠️ 蝦皮 API 回應狀態碼：{res.status_code}")
    except Exception as e:
        print(f"🚨 抓取過程發生異常：{e}")

    # 若網路環境仍被蝦皮封鎖，備用樣板亦補上特定商品專屬網址
    if not fetched_products:
        fetched_products = [
            {
                "id": timestamp,
                "name": "【蝦皮熱銷】無印風極簡大容量多功能雙肩後背包",
                "platform": "SHOPEE",
                "category": "包包服飾",
                "badge": "HOT",
                "originalPrice": 599,
                "promoPrice": 299,
                "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=600&q=80",
                "link": "https://shopee.tw/product/12345678/87654321",
                "code": "",
                "clicks": 0
            }
        ]
        
    return fetched_products

def update_firebase(products):
    url = f"{FIREBASE_DATABASE_URL}/yves_shop_data/products.json"
    
    try:
        response = requests.get(url)
        current_products = response.json() or []
        if not isinstance(current_products, list):
            current_products = []

        existing_names = {p.get("name") for p in current_products if isinstance(p, dict)}
        
        new_added = 0
        for p in products:
            if p["name"] not in existing_names:
                current_products.insert(0, p)
                new_added += 1

        put_response = requests.put(url, json=current_products)
        if put_response.status_code == 200:
            print(f"✅ 成功寫入 Firebase！新增了 {new_added} 項商品。")
        else:
            print(f"❌ 寫入失敗，狀態碼：{put_response.status_code}")
    except Exception as e:
        print(f"🚨 寫入 Firebase 發生異常：{e}")

if __name__ == "__main__":
    deals = fetch_shopee_deals()
    if deals:
        update_firebase(deals)
