"""Optional DeepSeek + Chroma retrieval service.

This module is imported lazily through ``service_loader`` so the main site can
run without downloading an embedding model or installing the AI extras.
"""

import os
import re
from pathlib import Path

from django.conf import settings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

from article.models import Article
from rag.models import QASession


class DeepSeekRAGService:
    def __init__(self):
        self.persist_directory = Path(settings.BASE_DIR) / 'rag' / 'chroma_db'
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=os.environ.get('EMBEDDING_MODEL', 'BAAI/bge-small-zh-v1.5'),
            model_kwargs={'device': 'cpu'},
        )
        self.llm = ChatOpenAI(
            model='deepseek-chat',
            api_key=os.environ['DEEPSEEK_API_KEY'],
            base_url='https://api.deepseek.com',
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=120,
        )
        self.db = Chroma(
            persist_directory=str(self.persist_directory),
            embedding_function=self.embeddings,
        )

    @staticmethod
    def _clean_html(content):
        return re.sub(r'\s+', ' ', re.sub(r'<.*?>', '', content)).strip()

    def _documents_for(self, article_title, article_content):
        document = Document(
            page_content=self._clean_html(article_content),
            metadata={'article_title': article_title},
        )
        return self.text_splitter.split_documents([document])

    def add_article(self, article_title, article_content):
        documents = self._documents_for(article_title, article_content)
        if documents:
            self.db.add_documents(documents)
        return True

    def delete_article(self, article_title):
        existing = self.db.get(where={'article_title': article_title})
        if existing.get('ids'):
            self.db.delete(ids=existing['ids'])
        return True

    def update_article(self, article_title, new_content):
        self.delete_article(article_title)
        return self.add_article(article_title, new_content)

    def refresh_knowledge_base(self):
        existing = self.db.get()
        if existing.get('ids'):
            self.db.delete(ids=existing['ids'])
        for article in Article.objects.iterator():
            self.add_article(article.title, article.content)
        return True

    def ask_question(self, question):
        docs = self.db.similarity_search(question, k=5)
        context = '\n\n'.join(doc.page_content for doc in docs)
        prompt = PromptTemplate.from_template(
            '你是校园信息助手。只根据上下文回答；若信息不足，请明确说明。\n\n'
            '上下文：\n{context}\n\n问题：{question}'
        )
        answer = (prompt | self.llm | StrOutputParser()).invoke(
            {'context': context, 'question': question}
        )

        related_articles = []
        for title in dict.fromkeys(doc.metadata.get('article_title') for doc in docs):
            if not title:
                continue
            article = Article.objects.filter(title=title).first()
            if article:
                related_articles.append({
                    'id': article.id,
                    'title': article.title,
                    'url': article.get_absolute_url(),
                    'author': article.author.username,
                    'created': article.created.strftime('%Y-%m-%d'),
                })

        session = QASession.objects.create(
            question=question,
            answer=answer,
            related_articles=[article['id'] for article in related_articles],
        )
        return {
            'answer': answer,
            'related_articles': related_articles,
            'session_id': session.id,
        }
