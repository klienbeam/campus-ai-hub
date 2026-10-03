from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json

from .service_loader import get_rag_service
from .models import QASession
from article.models import Article


class QAView(View):
    """问答页面视图"""
    
    def get(self, request):
        """显示问答页面"""
        return render(request, 'rag/qa.html')
    
    def post(self, request):
        """处理问答请求"""
        try:
            data = json.loads(request.body)
            question = data.get('question', '').strip()
            
            if not question:
                return JsonResponse({'error': '问题不能为空'}, status=400)
            
            service = get_rag_service()
            if service is None:
                return JsonResponse(
                    {'error': 'AI 功能未配置，请安装 AI 依赖并设置 DEEPSEEK_API_KEY'},
                    status=503,
                )
            result = service.ask_question(question)
            
            if 'error' in result:
                return JsonResponse({'error': result['error']}, status=500)
            
            # 获取相关文章信息
            related_articles = result.get('related_articles', [])
            
            return JsonResponse({
                'answer': result['answer'],
                'related_articles': related_articles,
                'session_id': result.get('session_id')
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': '无效的JSON数据'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'服务器错误: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def refresh_knowledge_base(request):
    """刷新知识库API"""
    try:
        service = get_rag_service()
        if service is None:
            return JsonResponse(
                {'error': 'AI 功能未配置，请安装 AI 依赖并设置 DEEPSEEK_API_KEY'},
                status=503,
            )
        success = service.refresh_knowledge_base()
        if success:
            return JsonResponse({'message': '知识库刷新成功'})
        else:
            return JsonResponse({'error': '知识库刷新失败'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'刷新知识库时出错: {str(e)}'}, status=500)


@require_http_methods(["GET"])
def qa_history(request):
    """获取问答历史"""
    try:
        sessions = QASession.objects.all()[:10]  # 最近10条
        history = [
            {
                'id': session.id,
                'question': session.question,
                'answer': session.answer[:100] + '...' if len(session.answer) > 100 else session.answer,
                'created_at': session.created_at.strftime('%Y-%m-%d %H:%M')
            }
            for session in sessions
        ]
        return JsonResponse({'history': history})
    except Exception as e:
        return JsonResponse({'error': f'获取历史记录时出错: {str(e)}'}, status=500)
