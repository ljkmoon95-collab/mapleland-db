import requests
from bs4 import BeautifulSoup
import json
import time
import re

def get_item_ids():
    url = "https://mapledb.kr/item.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    links = soup.find_all("a", href=re.compile(r"search\.php\?q=\d+&t=item"))
    ids = []
    for link in links:
        match = re.search(r"q=(\d+)", link["href"])
        if match:
            ids.append(match.group(1))
    print(f"총 {len(ids)}개 아이템 ID 추출")
    return ids

def get_item_info(item_id):
    url = f"https://mapledb.kr/search.php?q={item_id}&t=item"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        item = {"id": item_id}

        # 아이템명
        name_el = soup.select_one(".search-page-title .text-bold.fs-5")
        item["name"] = name_el.text.strip() if name_el else ""

        if not item["name"]:
            return None

        # 기본 섹션 - 모든 key/value 저장
        basic = {}
        info_boxes = soup.select(".search-page-info-content-box-default-box")
        for box in info_boxes:
            h4 = box.select_one("h4")
            span = box.select_one("span")
            if h4 and span:
                key = h4.text.strip()
                val = span.text.strip()
                basic[key] = val

        # 기본 섹션 - detail 형태도 포함
        detail_in_basic = soup.select(".search-page-info-content-box-default")
        for box in detail_in_basic:
            h4 = box.select_one("h4")
            span = box.select_one("span")
            if h4 and span:
                key = h4.text.strip()
                val = span.text.strip()
                basic[key] = val

        item["기본"] = basic

        # 세부 섹션 - 모든 key/value 저장
        detail = {}
        # 두 번째 info-content-box가 세부
        info_content_boxes = soup.select(".search-page-info-content-box")
        if len(info_content_boxes) >= 2:
            detail_box = info_content_boxes[1]
            detail_items = detail_box.select(".search-page-info-content-box-detail")
            for box in detail_items:
                h4 = box.select_one("h4")
                span = box.select_one("span")
                if h4 and span:
                    key = h4.text.strip()
                    val = span.text.strip()
                    detail[key] = val

        item["세부"] = detail

        return item

    except Exception as e:
        print(f"오류 [{item_id}]: {e}")
        return None

def main():
    print("mapledb.kr 크롤링 시작...")
    all_ids = get_item_ids()
    results = []
    total = len(all_ids)

    for i, item_id in enumerate(all_ids):
        print(f"[{i+1}/{total}] ID: {item_id} 크롤링 중...")
        item = get_item_info(item_id)
        if item:
            results.append(item)
            print(f"  → {item['name']} 저장")
        time.sleep(0.3)

    output = {
        "total": len(results),
        "items": results
    }

    with open("items.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n완료! 총 {len(results)}개 아이템 저장 → items.json")

if __name__ == "__main__":
    main()
