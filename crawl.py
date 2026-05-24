import requests
from bs4 import BeautifulSoup
import json
import time
import re

# 도적 + 법사 아이템 URL 목록
# 이 목록은 mapledb.kr/item.php에서 직업별 필터로 추출한 ID들
ITEM_IDS = {
    "thief": [],   # 도적 아이템 ID 목록 (아래에서 자동으로 채워짐)
    "mage": []     # 법사 아이템 ID 목록
}

# item.php에서 직업별 아이템 ID 추출
def get_item_ids(job_filter):
    """mapledb.kr/item.php에서 아이템 ID 목록 가져오기"""
    url = "https://mapledb.kr/item.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    resp = requests.get(url, headers=headers, timeout=10)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # 모든 아이템 링크 추출
    links = soup.find_all("a", href=re.compile(r"search\.php\?q=\d+&t=item"))
    ids = []
    for link in links:
        match = re.search(r"q=(\d+)", link["href"])
        if match:
            ids.append(match.group(1))
    
    print(f"총 {len(ids)}개 아이템 ID 추출")
    return ids

def get_item_info(item_id):
    """개별 아이템 상세 정보 크롤링"""
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
        
        # 기본 정보 박스 (레벨, 요구 DEX, 요구 LUK 등)
        info_boxes = soup.select(".search-page-info-content-box-default-box")
        for box in info_boxes:
            h4 = box.select_one("h4")
            span = box.select_one("span")
            if h4 and span:
                key = h4.text.strip()
                val = span.text.strip()
                if key == "LEVEL":
                    item["req_level"] = int(val) if val.isdigit() else 0
                elif key == "DEX":
                    item["req_dex"] = int(val) if val.isdigit() else 0
                elif key == "LUK":
                    item["req_luk"] = int(val) if val.isdigit() else 0
                elif key == "INT":
                    item["req_int"] = int(val) if val.isdigit() else 0
                elif key == "STR":
                    item["req_str"] = int(val) if val.isdigit() else 0
        
        # 세부 정보 (직업, 분류, 스탯 등)
        detail_boxes = soup.select(".search-page-info-content-box-detail")
        for box in detail_boxes:
            h4 = box.select_one("h4")
            span = box.select_one("span")
            if h4 and span:
                key = h4.text.strip()
                val = span.text.strip()
                if key == "직업":
                    item["job"] = val
                elif key == "분류":
                    item["category"] = val
                elif key == "주 카테고리":
                    item["main_category"] = val
                elif key == "부 카테고리":
                    item["sub_category"] = val
                elif key == "성별":
                    item["gender"] = val
                elif key == "STR":
                    item["str"] = parse_stat(val)
                elif key == "DEX":
                    item["dex"] = parse_stat(val)
                elif key == "INT":
                    item["int"] = parse_stat(val)
                elif key == "LUK":
                    item["luk"] = parse_stat(val)
                elif key == "공격력":
                    item["attack"] = parse_stat(val)
                elif key == "마력":
                    item["magic"] = parse_stat(val)
                elif key == "이동속도":
                    item["speed"] = parse_stat(val)
        
        return item
        
    except Exception as e:
        print(f"오류 [{item_id}]: {e}")
        return None

def parse_stat(val):
    """'4 (3-5)' 형태에서 기본값 추출"""
    match = re.match(r"(\d+)", val.strip())
    return int(match.group(1)) if match else 0

def main():
    print("mapledb.kr 크롤링 시작...")
    
    # 전체 아이템 ID 가져오기
    all_ids = get_item_ids("all")
    
    results = []
    total = len(all_ids)
    
    for i, item_id in enumerate(all_ids):
        print(f"[{i+1}/{total}] ID: {item_id} 크롤링 중...")
        
        item = get_item_info(item_id)
        if item and item.get("name"):
            # 도적 또는 법사 아이템만 저장
            job = item.get("job", "")
            if job in ["도적", "마법사", "공용"]:
                results.append(item)
                print(f"  → {item['name']} ({job}) 저장")
        
        # 서버 부하 방지
        time.sleep(0.3)
    
    # JSON 저장
    output = {
        "total": len(results),
        "items": results
    }
    
    with open("items.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n완료! 총 {len(results)}개 아이템 저장 → items.json")

if __name__ == "__main__":
    main()
