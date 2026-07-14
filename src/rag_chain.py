from src.document_processor import DocumentProcessor
from src.vector_store import VectorStoreManager
from src.llm_service import LLMService
from src.db_manager import DBManager
from config import Config
from typing import List, Tuple

class RAGChain:
    """RAG问答链，整合文档处理、向量检索和LLM生成"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.vector_store = VectorStoreManager()
        self.llm_service = LLMService()
        self.db_manager = DBManager()
        Config.init_directories()
    
    def upload_and_index(self, file_path: str) -> dict:
        """
        上传文档并建立索引
        :param file_path: 文件路径
        :return: 处理结果字典
        """
        try:
            result = self.document_processor.process_document(file_path)
            
            doc_id = self.db_manager.add_document(
                filename=result["filename"],
                file_type=result["file_type"],
                file_size=result["file_size"],
                content=result["content"]
            )
            
            self.db_manager.update_document_status(doc_id, "processing")
            
            self.vector_store.add_documents(
                doc_id=doc_id,
                chunks=result["chunks"],
                filename=result["filename"]
            )
            
            self.db_manager.update_document_status(doc_id, "processed", result["chunk_count"])
            
            return {
                "success": True,
                "doc_id": doc_id,
                "message": f"文档上传成功，共切分为 {result['chunk_count']} 个片段"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"文档处理失败：{str(e)}"
            }
    
    def query(self, user_id: str, session_id: str, question: str) -> dict:
        """
        执行问答查询
        :param user_id: 用户ID
        :param session_id: 会话ID
        :param question: 用户问题
        :return: 查询结果字典
        """
        try:
            chat_history = self._get_chat_history(user_id, session_id)
            
            search_query = question
            if chat_history:
                history_text = "\n".join([f"问：{msg['question']} 答：{msg['answer']}" for msg in chat_history])
                search_query = f"{history_text}\n\n当前问题：{question}"
            
            search_results = self.vector_store.search(search_query)
            
            if not search_results:
                if chat_history:
                    history_context = "\n".join([f"用户问：{msg['question']}\n助手答：{msg['answer']}" for msg in chat_history])
                    answer = self.llm_service.generate_answer(history_context, question, chat_history)
                    sources = []
                else:
                    answer = "未找到相关知识，请尝试其他关键词或上传相关文档。"
                    sources = []
            else:
                context = self.llm_service.format_context(search_results)
                if chat_history:
                    history_context = "\n".join([f"用户问：{msg['question']}\n助手答：{msg['answer']}" for msg in chat_history])
                    context = f"{history_context}\n\n---\n{context}"
                sources = self.llm_service.get_sources(search_results)
                answer = self.llm_service.generate_answer(context, question, chat_history)
            
            self.db_manager.add_conversation(
                user_id=user_id,
                session_id=session_id,
                question=question,
                answer=answer,
                sources=sources
            )
            
            return {
                "success": True,
                "answer": answer,
                "sources": sources,
                "search_results": search_results
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"查询失败：{str(e)}"
            }
    
    def _get_chat_history(self, user_id: str, session_id: str) -> List[dict]:
        """
        获取对话历史，用于上下文理解
        :param user_id: 用户ID
        :param session_id: 会话ID
        :return: 对话历史列表
        """
        conversations = self.db_manager.get_conversations(user_id, session_id)
        return [
            {
                "question": conv.question,
                "answer": conv.answer
            }
            for conv in conversations[-5:]
        ]
    
    def delete_document(self, doc_id: int) -> bool:
        """
        删除文档及其索引
        :param doc_id: 文档ID
        :return: 是否删除成功
        """
        try:
            self.vector_store.delete_by_doc_id(doc_id)
            return self.db_manager.delete_document(doc_id)
        except Exception as e:
            print(f"删除文档失败：{e}")
            return False
    
    def get_documents(self):
        """
        获取所有文档列表
        :return: 文档列表
        """
        return self.db_manager.get_all_documents()
    
    def get_collection_stats(self) -> dict:
        """
        获取向量库统计信息
        :return: 统计信息
        """
        return self.vector_store.get_collection_stats()