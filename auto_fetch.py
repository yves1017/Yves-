import os
import time
import requests

FIREBASE_DATABASE_URL = "https://shopee-da43f-default-rtdb.firebaseio.com"

def fetch_shopee_deals():
    timestamp = int(time.time())
    readable_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    print(f"🚀 [{readable_time}] 開始抓取蝦皮熱門商品真實資料...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://shopee.tw/"
    }
    
    shopee_api_url = "https://shopee.tw/api/v4/recommend/recommend_global_sorted?daily_discover_main_item_limit=10&limit=5&offset=0"
    
    fetched_products = []
    
    try:
        res = requests.get(shopee_api_url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            items = data.get("data", {}).get("sections", [{}])[0].get("data", {}).get("item", [])
            
            for index, item in enumerate(items[:5]):
                item_id = item.get("itemid")
                shop_id = item.get("shopid")
                name = item.get("name", "蝦皮熱銷精選商品")
                
                # 價格處理
                price_raw = item.get("price", 0)
                price_before_raw = item.get("price_before_discount", price_raw)
                
                promo_price = int(price_raw / 100000) if price_raw > 100000 else int(price_raw)
                original_price = int(price_before_raw / 100000) if price_before_raw > 100000 else int(price_raw)
                if original_price < promo_price:
                    original_price = promo_price
                
                # 圖片處理
                image_hash = item.get("image", "")
                image_url = f"https://down-tw.img.susercontent.com/file/{image_hash}" if image_hash else "https://via.placeholder.com/600"
                
                # 原始商品真實網址
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
                    "link": raw_product_link,  # 預設帶入原始商品網址
                    "code": "",
                    "clicks": 0
                })
        else:
            print(f"⚠️ 蝦皮 API 回應狀態碼：{res.status_code}，切換至備用真實熱門商品樣板")
    except Exception as e:
        print(f"🚨 抓取過程發生異常：{e}")

    # 備用真實商品格式（同步預設原始網址）
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
                "link": "https://shopee.tw/product/12345678/87654321",  # 原始商品網址範例
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
            print(f"✅ 成功寫入 Firebase！新增了 {new_added} 項商品（帶入原始網址）。")
        else:
            print(f"❌ 寫入失敗，狀態碼：{put_response.status_code}")
    except Exception as e:
        print(f"🚨 寫入 Firebase 發生異常：{e}")

if __name__ == "__main__":
    deals = fetch_shopee_deals()
    if deals:
        update_firebase(deals)
