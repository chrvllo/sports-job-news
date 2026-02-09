import feedparser
import requests
from datetime import datetime, timedelta
import os
import time

# 깃허브에 숨겨둔 비밀번호 가져오기
NOTION_TOKEN = os.environ['NOTION_TOKEN']
DATABASE_ID = os.environ['NOTION_DATABASE_ID']

# 노션에 데이터를 쏘는 함수 (선택 속성 버전)
def create_notion_page(title, link, published_date, source_name):
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "제목": {"title": [{"text": {"content": title}}]},
            "링크": {"url": link},
            "날짜": {"date": {"start": published_date}},
            "출처": {"select": {"name": source_name}}  # 여기가 '선택' 속성용 코드입니다
        }
    }
    
    requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)

# 공식 홈페이지 4곳 지정 (가짜뉴스 원천 차단)
queries = [
    'site:sports.or.kr',      # 대한체육회
    'site:kspo.or.kr',        # 국민체육진흥공단
    'site:sportsafety.or.kr', # 스포츠안전재단
    'site:k-sec.or.kr'        # 스포츠윤리센터
]

def fetch_and_save():
    print("수집 시작...")
    # 3일 전 데이터까지만 수집
    three_days_ago = datetime.now() - timedelta(days=3)
    
    for query in queries:
        # 구글을 통해 공식 사이트의 새 글을 RSS로 받아옴
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(rss_url)
        
        for entry in feed.entries:
            try:
                published = datetime(*entry.published_parsed[:6])
                
                if published > three_days_ago:
                    # 링크를 보고 어느 기관인지 이름표 붙이기
                    source_name = "기타"
                    if "sports.or.kr" in entry.link: source_name = "대한체육회"
                    elif "kspo.or.kr" in entry.link: source_name = "국민체육진흥공단"
                    elif "sportsafety" in entry.link: source_name = "스포츠안전재단"
                    elif "k-sec.or.kr" in entry.link: source_name = "스포츠윤리센터"

                    print(f"[{source_name}] 저장: {entry.title}")
                    
                    iso_date = published.strftime("%Y-%m-%dT%H:%M:%S")
                    
                    create_notion_page(entry.title, entry.link, iso_date, source_name)
                    time.sleep(1) # 과부하 방지 1초 휴식
            except Exception:
                pass

if __name__ == "__main__":
    fetch_and_save()
