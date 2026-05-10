# 巨潮+东方财富+雪球 资讯免费自动获取汇总方案（Python完整实现）

核心结论：**用「官方API+轻量爬虫+定时任务+本地存储」的组合，实现三大平台资讯的免费自动化采集与汇总**，无需付费终端，适合个人投资者与研究使用。以下是可直接落地的完整方案，包含代码模板与避坑指南。

---

## 一、整体架构设计（5层工作流）
```
数据源 → 采集层（API/爬虫）→ 处理层（清洗/去重/整合）→ 存储层（本地/数据库）→ 输出层（日报/提醒）
```
**核心依赖库**（提前安装）：
```bash
pip install requests beautifulsoup4 pandas sqlite3 apscheduler fake_useragent python-dotenv
```

---

## 二、分平台自动化采集方案（附完整代码）

### 1. 巨潮资讯（官方权威公告，优先用API）
**核心优势**：证监会指定披露平台，公告权威、无反爬限制，支持按板块/行业筛选

#### 关键API接口（免费无认证）
| 接口用途 | 请求URL | 请求方式 | 核心参数 |
|----------|---------|----------|----------|
| 公告列表 | https://www.cninfo.com.cn/new/hisAnnouncement/query | POST | stock：股票代码；category：公告类型；seDate：日期范围 |
| 公告详情 | https://www.cninfo.com.cn/new/disclosure/detail | GET | announcementId：公告ID；orgId：公司ID |

#### 采集代码（获取行业板块公告）
```python
import requests
import pandas as pd
import time
from fake_useragent import UserAgent

class CninfoSpider:
    def __init__(self):
        self.headers = {"User-Agent": UserAgent().random}
        self.base_url = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
    
    def get_industry_announcements(self, industry, start_date, end_date, page_num=1):
        """获取指定行业公告（如：银行业、医药生物）"""
        data = {
            "pageNum": page_num,
            "pageSize": 30,
            "column": "szse",
            "plate": industry,  # 行业板块名称
            "seDate": f"{start_date}~{end_date}",
            "isHLtitle": "true"
        }
        try:
            response = requests.post(self.base_url, headers=self.headers, data=data, timeout=10)
            response.raise_for_status()
            results = response.json()["announcements"]
            # 数据清洗
            df = pd.DataFrame(results)[["announcementTitle", "announcementTime", "secName", "orgId", "announcementId"]]
            df["source"] = "巨潮资讯"
            df["url"] = df.apply(lambda x: f"https://www.cninfo.com.cn/new/disclosure/detail?announcementId={x['announcementId']}&orgId={x['orgId']}", axis=1)
            return df[["announcementTitle", "announcementTime", "secName", "source", "url"]]
        except Exception as e:
            print(f"巨潮资讯采集失败: {e}")
            return pd.DataFrame()

# 使用示例：获取医药生物板块近3天公告
if __name__ == "__main__":
    spider = CninfoSpider()
    df = spider.get_industry_announcements("医药生物", "2026-05-07", "2026-05-10")
    print(df.head())
    time.sleep(5)  # 控制频率，避免触发反爬
```

---

### 2. 东方财富网（行业资讯+资金流向，API丰富）
**核心优势**：资讯全面、接口稳定、反爬宽松，适合批量采集

#### 关键API接口（免费无认证）
| 接口用途 | 请求URL | 请求方式 | 核心参数 |
|----------|---------|----------|----------|
| 行业资讯 | https://push2.eastmoney.com/api/qt/ulist.np/get | GET | fid：排序字段；po：页码；pz：条数；fields：返回字段 |
| 板块资金 | https://data.eastmoney.com/xg/kkpghy.html | GET | 需解析HTML表格 |

#### 采集代码（获取行业热点资讯）
```python
import requests
import pandas as pd
import json
import time
from fake_useragent import UserAgent

class EastMoneySpider:
    def __init__(self):
        self.headers = {"User-Agent": UserAgent().random}
        self.news_url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
    
    def get_industry_news(self, industry_code, page=1, pagesize=20):
        """获取行业热点资讯（industry_code：行业代码，如银行001、医药013）"""
        params = {
            "fltt": 2,
            "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152",
            "po": page,
            "pz": pagesize,
            "pn": page,
            "np": 1,
            "ut": "b2884a393a59ad64002292a3e90d46a5",
            "fs": f"m:90+t:{industry_code}"  # 90=行业，t=行业代码
        }
        try:
            response = requests.get(self.news_url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = json.loads(response.text.lstrip("var rankData = "))["data"]["diff"]
            df = pd.DataFrame(data)[["f14", "f12", "f15", "f16"]]  # 标题、日期、来源、链接
            df.columns = ["title", "publish_time", "source", "url"]
            df["source"] = "东方财富网"
            df["publish_time"] = pd.to_datetime(df["publish_time"], unit="s").dt.strftime("%Y-%m-%d %H:%M:%S")
            return df
        except Exception as e:
            print(f"东方财富采集失败: {e}")
            return pd.DataFrame()

# 使用示例：获取医药行业（013）最新资讯
if __name__ == "__main__":
    spider = EastMoneySpider()
    df = spider.get_industry_news("013")
    print(df.head())
    time.sleep(5)
```

---

### 3. 雪球（社区热点+投资者讨论，用API更高效）
**核心优势**：市场情绪指标、投资者观点，适合捕捉板块热度

#### 关键API接口（需模拟登录，轻量使用无需认证）
| 接口用途 | 请求URL | 请求方式 | 核心参数 |
|----------|---------|----------|----------|
| 板块帖子 | https://xueqiu.com/statuses/industry_timeline.json | GET | industry_id：行业ID；page：页码；count：条数 |
| 股票讨论 | https://xueqiu.com/statuses/search.json | GET | q：关键词；count：条数 |

#### 采集代码（获取板块热门讨论）
```python
import requests
import pandas as pd
import time
from fake_useragent import UserAgent

class XueqiuSpider:
    def __init__(self):
        self.headers = {
            "User-Agent": UserAgent().random,
            "Referer": "https://xueqiu.com/",
            "Cookie": "xq_a_token=你的雪球token（可选，登录后获取）"  # 无token也可获取公开内容
        }
        self.industry_url = "https://xueqiu.com/statuses/industry_timeline.json"
    
    def get_industry_discussions(self, industry_id, count=20):
        """获取板块热门讨论（industry_id：行业ID，如白酒105、医药102）"""
        params = {
            "industry_id": industry_id,
            "count": count,
            "page": 1
        }
        try:
            response = requests.get(self.industry_url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()["list"]
            results = []
            for item in data:
                results.append({
                    "title": item.get("title", ""),
                    "content": item.get("text", "")[:100] + "...",  # 截取前100字
                    "publish_time": item.get("created_at", ""),
                    "author": item.get("user", {}).get("screen_name", ""),
                    "source": "雪球",
                    "url": f"https://xueqiu.com{item.get('target', {}).get('id', '')}"
                })
            return pd.DataFrame(results)
        except Exception as e:
            print(f"雪球采集失败: {e}")
            return pd.DataFrame()

# 使用示例：获取医药行业（102）热门讨论
if __name__ == "__main__":
    spider = XueqiuSpider()
    df = spider.get_industry_discussions(102)
    print(df.head())
    time.sleep(5)
```

---

## 三、数据整合与自动化核心模块

### 1. 数据去重与标准化（避免重复资讯）
```python
import pandas as pd
import hashlib

def deduplicate_news(df):
    """基于标题+URL的哈希值去重"""
    if df.empty:
        return df
    # 生成唯一标识
    df["unique_id"] = df.apply(lambda x: hashlib.md5((str(x["title"]) + str(x["url"])).encode()).hexdigest(), axis=1)
    # 去重并保留最新记录
    df = df.drop_duplicates(subset=["unique_id"], keep="last")
    # 标准化字段
    standard_columns = ["title", "publish_time", "content", "source", "url", "unique_id"]
    for col in standard_columns:
        if col not in df.columns:
            df[col] = ""
    return df[standard_columns]

def combine_platform_data(cninfo_df, eastmoney_df, xueqiu_df):
    """合并三大平台数据"""
    combined = pd.concat([cninfo_df, eastmoney_df, xueqiu_df], ignore_index=True)
    combined = deduplicate_news(combined)
    # 按发布时间排序
    combined["publish_time"] = pd.to_datetime(combined["publish_time"], errors="coerce")
    combined = combined.sort_values("publish_time", ascending=False).reset_index(drop=True)
    return combined
```

### 2. 本地存储（SQLite，轻量免费）
```python
import sqlite3

def init_database(db_name="finance_news.db"):
    """初始化数据库表"""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            publish_time TEXT,
            content TEXT,
            source TEXT,
            url TEXT UNIQUE,
            unique_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_to_database(df, db_name="finance_news.db"):
    """保存数据到数据库"""
    if df.empty:
        return
    conn = sqlite3.connect(db_name)
    try:
        df.to_sql("news", conn, if_exists="append", index=False, chunksize=100)
        print(f"成功保存 {len(df)} 条资讯到数据库")
    except Exception as e:
        print(f"保存失败: {e}")
    finally:
        conn.close()
```

### 3. 定时任务（自动运行，无需手动触发）
```python
from apscheduler.schedulers.blocking import BlockingScheduler

def run_spiders():
    """执行所有爬虫并保存数据"""
    # 初始化爬虫
    cninfo_spider = CninfoSpider()
    eastmoney_spider = EastMoneySpider()
    xueqiu_spider = XueqiuSpider()
    
    # 采集数据（示例：医药生物板块）
    cninfo_df = cninfo_spider.get_industry_announcements("医药生物", "2026-05-07", "2026-05-10")
    eastmoney_df = eastmoney_spider.get_industry_news("013")
    xueqiu_df = xueqiu_spider.get_industry_discussions(102)
    
    # 合并去重
    combined_df = combine_platform_data(cninfo_df, eastmoney_df, xueqiu_df)
    
    # 保存到数据库
    save_to_database(combined_df)
    print("本次采集完成！")

def start_scheduler():
    """启动定时任务（每天9:00和15:30各运行一次）"""
    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(run_spiders, "cron", hour=9, minute=0)
    scheduler.add_job(run_spiders, "cron", hour=15, minute=30)
    print("定时任务已启动，每天9:00和15:30执行...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    init_database()
    start_scheduler()
```

---

## 四、反爬策略与合规提醒（避免IP封禁）

| 策略 | 具体做法 | 适用场景 |
|------|----------|----------|
| **请求频率控制** | 每次请求间隔3-5秒，批量任务间隔5-10秒 | 所有平台，特别是雪球 |
| **随机请求头** | 使用fake_useragent库生成随机User-Agent | 东方财富、雪球，避免被识别为爬虫 |
| **缓存机制** | 本地缓存已获取数据，避免重复请求同一接口 | 巨潮资讯公告、东方财富历史数据 |
| **指数退避重试** | 失败后重试间隔指数增长（1秒→2秒→4秒...） | 网络波动时，提高成功率 |
| **合规声明** | 仅用于个人研究，不用于商业用途，遵守robots.txt | 所有平台，规避法律风险 |

---

## 五、输出与使用（日报生成+消息提醒）

### 1. 生成每日资讯汇总报告
```python
def generate_daily_report(date="2026-05-10", db_name="finance_news.db"):
    """生成指定日期的资讯汇总报告"""
    conn = sqlite3.connect(db_name)
    query = f"""
        SELECT source, COUNT(*) as count, GROUP_CONCAT(title, '; ') as titles
        FROM news 
        WHERE DATE(publish_time) = '{date}'
        GROUP BY source
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    # 生成报告
    report = f"=== {date} 行业资讯汇总 ===\n"
    for _, row in df.iterrows():
        report += f"\n【{row['source']}】共{row['count']}条\n"
        report += f"标题：{row['titles']}\n"
    
    with open(f"daily_report_{date}.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print(f"日报已生成：daily_report_{date}.txt")

# 使用示例
generate_daily_report("2026-05-10")
```

### 2. 关键资讯微信提醒（可选，需Server酱）
```python
def send_wechat_alert(title, content):
    """通过Server酱发送微信提醒（免费注册：https://sct.ftqq.com/）"""
    import requests
    SCKEY = "你的Server酱SCKEY"
    url = f"https://sctapi.ftqq.com/{SCKEY}.send"
    params = {"text": title, "desp": content}
    requests.get(url, params=params)

# 关键资讯触发提醒（如：出现"集采"关键词）
def check_keywords(df, keywords=["集采", "降准", "政策"]):
    for _, row in df.iterrows():
        if any(keyword in row["title"] for keyword in keywords):
            send_wechat_alert(f"【关键资讯】{row['title']}", f"来源：{row['source']}\n链接：{row['url']}")
```

---

## 六、完整部署步骤

1. **环境准备**：安装Python 3.8+和所需依赖库
2. **初始化数据库**：运行`init_database()`创建本地数据库
3. **配置参数**：设置行业代码、日期范围、定时任务时间
4. **测试运行**：先手动执行一次`run_spiders()`，确保无报错
5. **后台部署**：在服务器或本地后台运行`scheduler.start()`，实现7×24小时自动采集

---

## 七、常见问题与解决方案

| 问题 | 解决方案 |
|------|----------|
| 巨潮资讯返回空数据 | 检查行业板块名称是否正确，调整日期范围，增加请求间隔 |
| 雪球返回403错误 | 新增Referer和Cookie字段，降低请求频率，使用随机User-Agent |
| 数据重复严重 | 优化去重逻辑，增加unique_id字段，确保URL唯一 |
| 定时任务中断 | 使用nohup后台运行（Linux/macOS），或创建Windows任务计划 |

---

这套方案完全免费，可与你现有的指数估值系统无缝对接，通过基本面资讯+历史估值数据的结合，解决"历史分位守旧"的问题，形成更全面的指数/行业分析体系。
