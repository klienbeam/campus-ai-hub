from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Dict, Any, List

import requests
from bs4 import BeautifulSoup
from django.conf import settings

BASE_URL = "http://oa.stu.edu.cn"
LIST_URL = BASE_URL + "/csweb/list.jsp"
ARTICLE_BASE = BASE_URL + "/page/maint/template/news/newstemplateprotal.jsp"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/141.0.0.0 Safari/537.36"
    )
})


def _get_save_dir() -> Path:
    path = Path(settings.BASE_DIR).parent / "oa_articles"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _fetch_titles(page_index: int = 1) -> List[Dict[str, str]]:
    params = {
        "pageindex": page_index,
        "pagesize": 10
    }
    resp = SESSION.get(LIST_URL, params=params, timeout=10)
    resp.encoding = resp.apparent_encoding
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    titles = []
    for tr in soup.find_all("tr", class_="datalight"):
        link = tr.find("a", attrs={"target": True})
        if not link:
            continue
        title = (link.get("title") or link.text or "").strip()
        href = link.get("href", "")
        match = re.search(r"docid=(\d+)", href)
        if not match or not title:
            continue
        docid = match.group(1)
        full_link = f"{ARTICLE_BASE}?templatetype=1&templateid=3&docid={docid}"
        
        # 尝试从列表页提取发布日期（通常在td中）
        publish_date = None
        tds = tr.find_all("td")
        for td in tds:
            text = td.get_text(strip=True)
            # 尝试匹配日期格式：YYYY-MM-DD 或 YYYY/MM/DD
            date_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', text)
            if date_match:
                try:
                    year, month, day = date_match.groups()
                    publish_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    break
                except:
                    pass
        
        titles.append({
            "title": title,
            "url": full_link,
            "publish_date": publish_date  # 可能为None
        })
    return titles


def _fetch_article_content(url: str) -> tuple[str, str]:
    """
    获取文章内容和发布日期
    返回: (content, publish_date)
    """
    try:
        resp = SESSION.get(url, timeout=10)
        resp.encoding = resp.apparent_encoding
        if resp.status_code != 200:
            return "", ""
        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.find("span", id="spanContent")
        if not content:
            content = soup.select_one(".newstext, .content, #mainContent")
        if not content:
            return "", ""
        raw_text = content.get_text("\n", strip=False)
        text = re.sub(r"(\d+)\s+(\d+)", r"\1\2", raw_text)
        text = re.sub(r"(\d+)\s+([年月日时分])", r"\1\2", text)
        text = re.sub(r"(\d+):\s*(\d+)", r"\1:\2", text)
        text = re.sub(r"([：:])\s*\n\s*", r"\1 ", text)
        text = re.sub(r'([，。；、"\'’])\s*\n\s*', r"\1", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"^\n+|\n+$", "", text)
        text = re.sub(r"^\s+", "", text, flags=re.MULTILINE)
        content_text = text.strip()
        
        # 尝试从页面提取发布日期
        publish_date = None
        # 查找常见的日期标签
        date_patterns = [
            r'发布时间[：:]\s*(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})',
            r'发布日期[：:]\s*(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})',
            r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})[日]?\s*发布',
        ]
        page_text = soup.get_text()
        for pattern in date_patterns:
            match = re.search(pattern, page_text)
            if match:
                try:
                    year, month, day = match.groups()
                    publish_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    break
                except:
                    pass
        
        return content_text, publish_date or ""
    except Exception:
        return "", ""


def _file_exists(save_dir: Path, title: str) -> bool:
    safe_title = re.sub(r'[\\/:*?"<>|]', "_", title)
    for file in save_dir.glob(f"{safe_title}_*.txt"):
        if file.is_file():
            return True
    return False


def _save_to_txt(save_dir: Path, title: str, content: str, publish_date: str = None) -> str:
    """
    保存为txt文件，文件名包含发布日期（如果提供）
    publish_date格式: YYYY-MM-DD
    """
    safe_title = re.sub(r'[\\/:*?"<>|]', "_", title)
    
    # 如果提供了发布日期，使用它作为文件名时间戳；否则使用当前时间
    if publish_date:
        try:
            # 将 YYYY-MM-DD 转换为 YYYYMMDD_HHMMSS（时间部分用000000）
            date_part = publish_date.replace("-", "")
            timestamp = f"{date_part}_000000"
        except:
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    else:
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    
    filename = save_dir / f"{safe_title}_{timestamp}.txt"
    with filename.open("w", encoding="utf-8") as f:
        title_line = f"【OA通知】{title}"
        space_num = max(0, (80 - len(title_line)) // 2)
        f.write(" " * space_num + title_line + "\n\n")
        if publish_date:
            f.write(f"发布日期：{publish_date}\n\n")
        f.write("=" * 80 + "\n\n")
        f.write(content)
    return filename.name


def fetch_latest_oa_articles(target_count: int = 50, max_pages: int = 60, delay: float = 0.3) -> Dict[str, Any]:
    """
    直接从 OA 网站抓取最新内容，保存为 txt 文件。
    :param target_count: 需要抓取的新文件数量
    :param max_pages: 最多遍历的页数
    :param delay: 每篇之间的延迟，避免请求过快
    """
    save_dir = _get_save_dir()
    fetched = 0
    skipped = 0
    errors: List[str] = []

    page = 1
    while fetched < target_count and page <= max_pages:
        titles = _fetch_titles(page)
        if not titles:
            break
        for item in titles:
            if fetched >= target_count:
                break
            title = item["title"]
            url = item["url"]
            list_date = item.get("publish_date")  # 从列表页获取的日期
            
            if _file_exists(save_dir, title):
                skipped += 1
                continue

            content, detail_date = _fetch_article_content(url)
            if not content:
                errors.append(f"抓取失败: {title}")
                continue

            # 优先使用详情页的日期，其次使用列表页的日期
            publish_date = detail_date or list_date
            _save_to_txt(save_dir, title, content, publish_date)
            fetched += 1
            time.sleep(delay)
        page += 1

    return {
        "fetched": fetched,
        "skipped_existing": skipped,
        "errors": errors[:5],
        "save_dir": str(save_dir),
        "target": target_count,
        "pages_visited": page - 1,
    }
