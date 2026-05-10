from dataclasses import dataclass
from typing import Optional


@dataclass
class NewsItem:
    title: str
    publish_time: str
    source: str
    url: str
    keyword: str
    content_snippet: Optional[str] = None
