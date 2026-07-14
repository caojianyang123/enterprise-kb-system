from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, VARCHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import Config
import hashlib

Base = declarative_base()

class Document(Base):
    """文档元数据表"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(VARCHAR(255), nullable=False)
    file_type = Column(VARCHAR(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_hash = Column(VARCHAR(64), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.now)
    status = Column(VARCHAR(20), default="uploaded")
    chunk_count = Column(Integer, default=0)

class Conversation(Base):
    """会话记录表"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(VARCHAR(64), nullable=False)
    session_id = Column(VARCHAR(64), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

class DBManager:
    """数据库管理器，负责所有数据库操作"""
    
    def __init__(self):
        self.engine = create_engine(Config.DATABASE_URL, pool_pre_ping=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def add_document(self, filename: str, file_type: str, file_size: int, content: str) -> int:
        """
        添加文档记录
        :param filename: 文件名
        :param file_type: 文件类型
        :param file_size: 文件大小
        :param content: 文件内容（用于计算哈希）
        :return: 文档ID
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        session = self.Session()
        try:
            doc = Document(
                filename=filename,
                file_type=file_type,
                file_size=file_size,
                content_hash=content_hash
            )
            session.add(doc)
            session.commit()
            return doc.id
        finally:
            session.close()
    
    def update_document_status(self, doc_id: int, status: str, chunk_count: int = 0):
        """
        更新文档状态
        :param doc_id: 文档ID
        :param status: 状态（uploaded/processing/processed/failed）
        :param chunk_count: 切分块数
        """
        session = self.Session()
        try:
            doc = session.query(Document).filter(Document.id == doc_id).first()
            if doc:
                doc.status = status
                doc.chunk_count = chunk_count
                session.commit()
        finally:
            session.close()
    
    def get_document(self, doc_id: int):
        """
        获取文档信息
        :param doc_id: 文档ID
        :return: Document对象
        """
        session = self.Session()
        try:
            return session.query(Document).filter(Document.id == doc_id).first()
        finally:
            session.close()
    
    def get_all_documents(self):
        """
        获取所有文档列表
        :return: Document对象列表
        """
        session = self.Session()
        try:
            return session.query(Document).order_by(Document.uploaded_at.desc()).all()
        finally:
            session.close()
    
    def delete_document(self, doc_id: int) -> bool:
        """
        删除文档记录
        :param doc_id: 文档ID
        :return: 是否删除成功
        """
        session = self.Session()
        try:
            doc = session.query(Document).filter(Document.id == doc_id).first()
            if doc:
                session.delete(doc)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def add_conversation(self, user_id: str, session_id: str, question: str, answer: str, sources=None):
        """
        添加会话记录
        :param user_id: 用户ID
        :param session_id: 会话ID
        :param question: 用户问题
        :param answer: AI回答
        :param sources: 引用来源
        :return: 记录ID
        """
        session = self.Session()
        try:
            conv = Conversation(
                user_id=user_id,
                session_id=session_id,
                question=question,
                answer=answer,
                sources=str(sources) if sources else None
            )
            session.add(conv)
            session.commit()
            return conv.id
        finally:
            session.close()
    
    def get_conversations(self, user_id: str, session_id: str):
        """
        获取用户会话记录
        :param user_id: 用户ID
        :param session_id: 会话ID
        :return: Conversation对象列表
        """
        session = self.Session()
        try:
            return session.query(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.session_id == session_id
            ).order_by(Conversation.created_at.asc()).all()
        finally:
            session.close()
    
    def get_all_conversations(self, user_id: str):
        """
        获取用户所有会话记录
        :param user_id: 用户ID
        :return: Conversation对象列表
        """
        session = self.Session()
        try:
            return session.query(Conversation).filter(
                Conversation.user_id == user_id
            ).order_by(Conversation.created_at.desc()).all()
        finally:
            session.close()