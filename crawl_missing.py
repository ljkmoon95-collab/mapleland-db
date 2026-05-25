import requests
from bs4 import BeautifulSoup
import json
import time
import re

def get_all_item_ids():
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
    print(f"전체 {len(ids)}개 아이템 ID 확인")
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

        name_el = soup.select_one(".search-page-title .text-bold.fs-5")
        item["name"] = name_el.text.strip() if name_el else ""

        if not item["name"]:
            return None

        basic = {}
        info_boxes = soup.select(".search-page-info-content-box-default-box")
        for box in info_boxes:
            h4 = box.select_one("h4")
            span = box.select_one("span")
            if h4 and span:
                basic[h4.text.strip()] = span.text.strip()

        detail_in_basic = soup.select(".search-page-info-content-box-default")
        for box in detail_in_basic:
            h4 = box.select_one("h4")
            span = box.select_one("span")
            if h4 and span:
                basic[h4.text.strip()] = span.text.strip()

        item["기본"] = basic

        detail = {}
        info_content_boxes = soup.select(".search-page-info-content-box")
        if len(info_content_boxes) >= 2:
            detail_box = info_content_boxes[1]
            detail_items = detail_box.select(".search-page-info-content-box-detail")
            for box in detail_items:
                h4 = box.select_one("h4")
                span = box.select_one("span")
                if h4 and span:
                    detail[h4.text.strip()] = span.text.strip()

        item["세부"] = detail

        return item

    except Exception as e:
        print(f"오류 [{item_id}]: {e}")
        return None

def main():
    # 기존 items.json 로드
    print("기존 items.json 로드 중...")
    with open("items.json", "r", encoding="utf-8") as f:
        existing_data = json.load(f)

    existing_ids = set(i["id"] for i in existing_data["items"])
    print(f"기존 저장된 아이템: {len(existing_ids)}개")

    # 전체 ID 목록 가져오기
    all_ids = get_all_item_ids()
    all_ids_set = set(all_ids)

    # 누락 ID 추출
    missing_ids = [id for id in all_ids if id not in existing_ids]
    print(f"누락된 아이템: {len(missing_ids)}개")
    print(f"누락 ID 목록: {missing_ids}")

    if not missing_ids:
        print("누락 아이템 없음!")
        return

    # 누락 아이템 크롤링
    new_items = []
    total = len(missing_ids)
    for i, item_id in enumerate(missing_ids):
        print(f"[{i+1}/{total}] ID: {item_id} 크롤링 중...")
        item = get_item_info(item_id)
        if item:
            new_items.append(item)
            print(f"  → {item['name']} 저장")
        else:
            print(f"  → 파싱 실패 (빈 아이템)")
        time.sleep(0.3)

    # 기존 + 신규 병합
    merged = existing_data["items"] + new_items
    
    # ID 기준 중복 제거 (혹시 몰라서)
    seen = set()
    unique = []
    for item in merged:
        if item["id"] not in seen:
            seen.add(item["id"])
            unique.append(item)

    # ID 순 정렬
    unique.sort(key=lambda x: x["id"])

    output = {
        "total": len(unique),
        "items": unique
    }

    with open("items.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n완료! 총 {len(unique)}개 아이템 저장 → items.json")
    print(f"신규 추가: {len(new_items)}개")

if __name__ == "__main__":
    main()
