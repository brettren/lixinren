import requests
import time
from .base import NewsItem

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://so.eastmoney.com/",
}

SEARCH_URL = "https://search-api-web.eastmoney.com/search/jsonp"


class EastMoneyCollector:
    name = "东方财富"

    @staticmethod
    def collect(keyword, start_date, end_date):
        items = []
        try:
            params = {
                "cb": "jQuery_callback",
                "param": f'{{"uid":"","keyword":"{keyword}","type":["cmsArticleWebOld"],"client":"web","clientType":"web","clientVersion":"curr","param":{{"cmsArticleWebOld":{{"searchScope":"default","sort":"default","pageIndex":1,"pageSize":20,"preTag":"<em>","postTag":"</em>"}}}}}}',
            }
            resp = requests.get(SEARCH_URL, headers=HEADERS, params=params, timeout=15)
            resp.raise_for_status()
            text = resp.text
            json_str = text[text.index("(") + 1:text.rindex(")")]
            import json
            data = json.loads(json_str)
            articles = data.get("result", {}).get("cmsArticleWebOld", [])
            if isinstance(articles, dict):
                articles = articles.get("list", [])
            for art in articles[:20]:
                title = art.get("title", "").replace("<em>", "").replace("</em>", "")
                pub_date = art.get("date", "")[:10]
                url = art.get("url", "")
                content = art.get("content", "")[:200] if art.get("content") else None
                if title and url:
                    items.append(NewsItem(
                        title=title,
                        publish_time=pub_date,
                        source="东方财富",
                        url=url,
                        keyword=keyword,
                        content_snippet=content
                    ))
        except Exception as e:
            print(f"[东方财富] 采集'{keyword}'失败: {e}")
        time.sleep(3)
        return items
