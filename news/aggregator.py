from .keyword_mapping import get_unique_keywords
from .collectors import ALL_COLLECTORS
from .storage import save_news_items, init_database


def run_collection(start_date, end_date):
    init_database()
    keywords = get_unique_keywords()
    total_saved = 0
    for keyword in keywords:
        print(f"--- 采集关键词: {keyword} ---")
        for CollectorClass in ALL_COLLECTORS:
            collector = CollectorClass()
            items = collector.collect(keyword, start_date, end_date)
            if items:
                saved = save_news_items(items)
                print(f"  [{collector.name}] 获取 {len(items)} 条, 新增 {saved} 条")
                total_saved += saved
            else:
                print(f"  [{collector.name}] 无结果")
    print(f"\n=== 采集完成, 共新增 {total_saved} 条资讯 ===")
    return total_saved
