from django.apps import AppConfig
import threading
import time
import sys



class ArticleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "article"

    def ready(self):
        # 仅在 runserver 场景下启动后台导入轮询
        if any(cmd in sys.argv for cmd in ['runserver', 'runserver_plus']):
            from .services_import import import_from_oa_articles

            def _worker():
                while True:
                    try:
                        import_from_oa_articles()
                    except Exception:
                        pass
                    time.sleep(10)  # 每10秒检查一次是否有新TXT

            t = threading.Thread(target=_worker, daemon=True)
            t.start()
