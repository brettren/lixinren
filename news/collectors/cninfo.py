import requests
import time
from .base import NewsItem

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

BASE_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"


class CninfoCollector:
    name = "巨潮资讯"

    @staticmethod
    def collect(keyword, start_date, end_date):
        items = []
        try:
            data = {
                "pageNum": 1,
                "pageSize": 30,
                "column": "szse",
                "tabName": "fulltext",
                "plate": "",
                "stock": "",
                "searchkey": keyword,
                "seDate": f"{start_date}~{end_date}",
                "secid": "",
                "category": "",
                "trade": "",
                "isHLtitle": "true",
            }
            resp = requests.post(BASE_URL, headers=HEADERS, data=data, timeout=15)
            resp.raise_for_status()
            result = resp.json()
            announcements = result.get("announcements") or []
            for ann in announcements[:20]:
                title = ann.get("announcementTitle", "").replace("<em>", "").replace("</em>", "")
                ann_id = ann.get("announcementId", "")
                org_id = ann.get("orgId", "")
                ann_time = ann.get("announcementTime", "")
                if ann_time:
                    from datetime import datetime
                    ann_time = datetime.fromtimestamp(ann_time / 1000).strftime("%Y-%m-%d")
                url = f"https://www.cninfo.com.cn/new/disclosure/detail?announcementId={ann_id}&orgId={org_id}"
                sec_name = ann.get("secName", "").replace("<em>", "").replace("</em>", "")
                items.append(NewsItem(
                    title=f"[{sec_name}] {title}" if sec_name else title,
                    publish_time=ann_time,
                    source="巨潮资讯",
                    url=url,
                    keyword=keyword,
                    content_snippet=ann.get("announcementContent", "")[:200] if ann.get("announcementContent") else None
                ))
        except Exception as e:
            print(f"[巨潮资讯] 采集'{keyword}'失败: {e}")
        time.sleep(3)
        return items
