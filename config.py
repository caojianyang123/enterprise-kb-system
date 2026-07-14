import os
from dotenv import load_dotenv

class Config:
    load_dotenv()
    
    DATABASE_URL = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'enterprise_kb.db')}"
    
    LLM_API_KEY = os.environ.get("DASHSCOPE_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    LLM_MODEL = os.environ.get("LLM_MODEL") or os.getenv("LLM_MODEL", "qwen3.7-plus")
    LLM_BASE_URL = os.environ.get("LLM_BASE_URL") or os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    
    CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), os.getenv("CHROMA_DB_PATH", "./chroma_db"))
    UPLOAD_DIR = os.path.join(os.path.dirname(__file__), os.getenv("UPLOAD_DIR", "./uploads"))
    
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    TOP_K = 3
    
    MAX_CONCURRENT_USERS = 50
    MAX_DOCUMENT_SIZE = 50 * 1024 * 1024
    
    @staticmethod
    def init_directories():
        os.makedirs(Config.CHROMA_DB_PATH, exist_ok=True)
        os.makedirs(Config.UPLOAD_DIR, exist_ok=True)