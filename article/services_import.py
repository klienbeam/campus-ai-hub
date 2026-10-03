from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple
import re

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User

from .models import Article
from rag.service_loader import get_rag_service


def _locate_oa_dir() -> Tuple[Path | None, List[str]]:
    tried = []
    candidates = [
        Path(settings.BASE_DIR).parent / 'oa_articles',
        Path(settings.BASE_DIR) / 'oa_articles',
        Path(settings.BASE_DIR).parent.parent / 'oa_articles',
    ]
    for p in candidates:
        tried.append(str(p))
        if p.exists() and p.is_dir():
            return p, tried
    return None, tried


def _extract_timestamp(file_path: Path) -> datetime:
    """优先根据文件名中的时间戳排序，若失败则使用文件修改时间"""
    stem = file_path.stem
    parts = stem.rsplit('_', 2)
    if len(parts) >= 3:
        date_part = parts[-2]
        time_part = parts[-1]
        try:
            return datetime.strptime(f'{date_part}{time_part}', '%Y%m%d%H%M%S')
        except Exception:
            pass
    return datetime.fromtimestamp(file_path.stat().st_mtime)


def import_from_oa_articles(
    preferred_author: User | None = None,
    limit: int | None = None,
    skip_rag: bool = False,
    only_recent: bool = False,
    recent_minutes: int = 10,
) -> Dict[str, Any]:
    """
    从 oa_articles 目录导入 .txt 文件为 Article 记录，默认按时间从新到旧。

    返回统计 dict：
    {
        imported, skipped, errors, skipped_titles,
        dir, tried, total_files, processed_files
    }
    """
    imported = 0
    skipped = 0
    errors: List[str] = []
    skipped_titles: List[str] = []

    oa_dir, tried = _locate_oa_dir()
    if oa_dir is None:
        return {'error': '未找到 oa_articles 目录', 'tried': tried}

    author = preferred_author or User.objects.filter(is_superuser=True).first() or User.objects.first()
    if not author:
        return {'error': '系统中尚无可用作者用户', 'dir': str(oa_dir)}

    txt_files = sorted(oa_dir.glob('*.txt'), key=_extract_timestamp, reverse=True)
    total_files = len(list(oa_dir.glob('*.txt')))
    
    # 如果只导入最近的文件（自动抓取模式），过滤出最近几分钟内创建的文件
    if only_recent:
        from django.utils import timezone as tz_util
        cutoff_time = tz_util.now() - tz_util.timedelta(minutes=recent_minutes)
        import time as time_module
        txt_files = [
            f for f in txt_files
            if tz_util.make_aware(datetime.fromtimestamp(f.stat().st_mtime)) > cutoff_time
        ]
    
    if not txt_files:
        return {
            'imported': 0,
            'skipped': 0,
            'errors': [],
            'skipped_titles': [],
            'dir': str(oa_dir),
            'message': '未发现 .txt 文件' + ('（或最近没有新文件）' if only_recent else ''),
            'total_files': total_files,
            'processed_files': 0,
            'tried': tried,
        }

    if limit and limit > 0:
        txt_files = txt_files[:limit]

    for file_path in txt_files:
        try:
            stem = file_path.stem
            parts = stem.rsplit('_', 2)
            title_raw = parts[0]
            created_dt = None
            
            # 尝试从文件名提取日期（格式：YYYYMMDD_HHMMSS）
            if len(parts) >= 3:
                date_part = parts[-2]
                time_part = parts[-1]
                try:
                    # 如果时间部分是000000，说明是发布日期（只有日期，没有具体时间）
                    if time_part == "000000":
                        created_dt = datetime.strptime(date_part, '%Y%m%d')
                    else:
                        created_dt = datetime.strptime(f'{date_part}{time_part}', '%Y%m%d%H%M%S')
                except Exception:
                    pass
            
            # 如果文件名没有日期，尝试从文件内容中提取发布日期
            if created_dt is None:
                try:
                    content_preview = file_path.read_text(encoding='utf-8', errors='ignore')[:500]
                    date_match = re.search(r'发布日期[：:]\s*(\d{4})[-/](\d{1,2})[-/](\d{1,2})', content_preview)
                    if date_match:
                        year, month, day = date_match.groups()
                        created_dt = datetime(int(year), int(month), int(day))
                except Exception:
                    pass
            
            title = title_raw.strip()[:64]

            existing = Article.objects.filter(title=title).first()
            if existing:
                skipped += 1
                skipped_titles.append(title[:50])
                continue

            content = None
            for enc in ['utf-8', 'utf-8-sig', 'gb18030', 'gbk']:
                try:
                    content = file_path.read_text(encoding=enc)
                    break
                except Exception:
                    continue
            if content is None:
                raise Exception('不支持的文件编码')

            article = Article.objects.create(
                author=author,
                title=title,
                content=content,
                created=created_dt or timezone.now()
            )

            if not skip_rag:
                try:
                    service = get_rag_service()
                    if service is not None:
                        service.add_article(
                            article_title=article.title,
                            article_content=article.content
                        )
                except Exception as e:
                    errors.append(f'RAG失败: {file_path.name}: {e}')

            imported += 1
        except Exception as e:
            errors.append(f'导入失败: {file_path.name}: {e}')

    result = {
        'imported': imported,
        'skipped': skipped,
        'errors': errors[:10],
        'skipped_titles': skipped_titles[:10],
        'dir': str(oa_dir),
        'total_files': total_files,
        'processed_files': len(txt_files),
        'tried': tried,
        'skip_rag': skip_rag,
    }
    if imported == 0 and skipped > 0:
        result['message'] = f'所有 {skipped} 个文件都已导入过，没有新内容'
    elif imported > 0:
        result['message'] = f'成功导入 {imported} 个新内容'
    return result

