import argparse
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from news.aggregator import run_collection
from news.report import generate_weekly_report


def main():
    parser = argparse.ArgumentParser(description="采集行业新闻并生成周报")
    parser.add_argument("--days", type=int, default=7, help="采集最近N天的新闻 (默认7)")
    parser.add_argument("--start", type=str, help="起始日期 (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--report-only", action="store_true", help="仅生成报告，不采集")
    parser.add_argument("--week", type=str, help="指定周报周次 (如 2026-W19)")
    args = parser.parse_args()

    if not args.report_only:
        if args.start and args.end:
            start_date = args.start
            end_date = args.end
        else:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")

        print(f"采集日期范围: {start_date} ~ {end_date}")
        run_collection(start_date, end_date)

    generate_weekly_report(args.week)


if __name__ == "__main__":
    main()
