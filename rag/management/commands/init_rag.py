from django.core.management.base import BaseCommand
from rag.service_loader import get_rag_service


class Command(BaseCommand):
    help = '初始化RAG知识库'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新初始化知识库',
        )

    def handle(self, *args, **options):
        rag_service = get_rag_service()
        if rag_service is None:
            self.stderr.write(
                'AI 功能未配置。请安装 requirements-ai.txt 并设置 DEEPSEEK_API_KEY。'
            )
            return
        if options['force']:
            self.stdout.write('强制重新初始化知识库...')
            success = rag_service.refresh_knowledge_base()
        else:
            self.stdout.write('检查知识库状态...')
            if not rag_service.db.get().get('ids'):
                self.stdout.write('知识库不存在或为空，开始初始化...')
                success = rag_service.refresh_knowledge_base()
            else:
                self.stdout.write('知识库已存在，无需重复初始化。')
                success = True

        if success:
            self.stdout.write(
                self.style.SUCCESS('RAG知识库初始化完成！')
            )
        else:
            self.stdout.write(
                self.style.ERROR('RAG知识库初始化失败！')
            )









