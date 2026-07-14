import os
import hashlib
from typing import List
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
import markdown
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import Config

class DocumentProcessor:
    """文档处理器，负责多格式文档的解析、切分和向量化准备"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " "]
        )
    
    def extract_text(self, file_path: str) -> str:
        """
        根据文件类型提取文本内容
        :param file_path: 文件路径
        :return: 提取的文本内容
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == ".pdf":
            return self._extract_pdf(file_path)
        elif file_ext == ".docx":
            return self._extract_docx(file_path)
        elif file_ext == ".md":
            return self._extract_md(file_path)
        elif file_ext == ".txt":
            return self._extract_txt(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")
    
    def _extract_pdf(self, file_path: str) -> str:
        """提取PDF文件内容"""
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    
    def _extract_docx(self, file_path: str) -> str:
        """提取Word文件内容"""
        doc = DocxDocument(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def _extract_md(self, file_path: str) -> str:
        """提取Markdown文件内容"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return markdown.markdown(content, extensions=["extra"])
    
    def _extract_txt(self, file_path: str) -> str:
        """提取纯文本文件内容"""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    
    def split_text(self, text: str) -> List[str]:
        """
        将文本切分为多个块
        :param text: 完整文本
        :return: 文本块列表
        """
        chunks = self.text_splitter.split_text(text)
        return [chunk.strip() for chunk in chunks if chunk.strip()]
    
    def process_document(self, file_path: str) -> dict:
        """
        完整处理文档流程：提取文本 → 清洗 → 切分
        :param file_path: 文件路径
        :return: 处理结果字典
        """
        filename = os.path.basename(file_path)
        file_type = os.path.splitext(filename)[1].lower()[1:]
        file_size = os.path.getsize(file_path)
        
        text = self.extract_text(file_path)
        text = self._clean_text(text)
        chunks = self.split_text(text)
        
        return {
            "filename": filename,
            "file_type": file_type,
            "file_size": file_size,
            "content": text,
            "chunks": chunks,
            "chunk_count": len(chunks),
            "content_hash": hashlib.sha256(text.encode()).hexdigest()
        }
    
    def _clean_text(self, text: str) -> str:
        """
        清洗文本，去除多余空白和特殊字符
        :param text: 原始文本
        :return: 清洗后的文本
        """
        import re
        
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\u4e00-\u9fff\u0030-\u0039\u0041-\u005a\u0061-\u007a。！？，；：、\s]', '', text)
        text = text.strip()
        
        return text