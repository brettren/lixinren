import csv
import os
from datetime import datetime
from .storage import query_week

REPORT_PATH = os.path.join(os.path.dirname(__file__), "weekly_news_report.csv")


def generate_weekly_report(week_label=None):
    if week_label is None:
        today = datetime.now()
        year, week, _ = today.isocalendar()
        week_label = f"{year}-W{week:02d}"

    rows = query_week(week_label)
    if not rows:
        print(f"[{week_label}] 无新闻数据")
        return None

    with open(REPORT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["week", "keyword", "source", "title", "publish_time", "url"])
        for row in rows:
            writer.writerow([week_label, row["keyword"], row["source"], row["title"], row["publish_time"], row["url"]])

    print(f"周报已生成: {REPORT_PATH} ({len(rows)} 条)")
    return REPORT_PATH
