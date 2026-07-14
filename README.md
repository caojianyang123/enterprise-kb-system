# 企业私有知识库问答系统

基于RAG（检索增强生成）技术构建的企业级智能问答平台，支持多格式文档上传、语义向量检索与多轮对话。

## 🎯 功能特性

- **文档管理**：支持 PDF、Word、Markdown、TXT 多格式文档上传与管理
- **语义检索**：基于向量数据库的智能检索，精准匹配相关知识
- **智能问答**：结合大语言模型生成准确回答
- **多轮对话**：支持对话上下文记忆，理解语境
- **引用追踪**：显示回答的引用来源，便于溯源

## 🛠️ 技术栈

- **后端**：FastAPI + Uvicorn
- **框架**：LangChain 1.0+
- **大模型**：阿里云百炼（Qwen3.7-plus）
- **向量数据库**：ChromaDB
- **关系数据库**：SQLite
- **文档解析**：PyPDF2、python-docx
- **环境管理**：python-dotenv

## 📁 项目结构

```
enterprise-kb-system/
├── main.py                    # FastAPI 主应用入口
├── config.py                  # 配置管理
├── .env                       # 环境变量配置
├── requirements.txt           # 依赖清单
├── example_doc.md             # 示例文档
├── src/
│   ├── rag_chain.py           # RAG 问答链
│   ├── llm_service.py         # LLM 服务
│   ├── vector_store.py        # 向量库管理
│   ├── document_processor.py  # 文档解析与切分
│   └── db_manager.py          # 数据库操作
├── uploads/                   # 上传文档目录
└── chroma_db/                 # ChromaDB 数据目录
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- 阿里云百炼 API Key（需开通服务）

### 2. 安装依赖

```bash
# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

编辑 `.env` 文件，配置阿里云百炼 API Key：

```env
# 阿里云百炼 API Key（必填）
DASHSCOPE_API_KEY=your_aliyun_api_key
```

也可以通过系统环境变量设置 `DASHSCOPE_API_KEY`。

### 4. 启动应用

```bash
# 开发模式
python -m uvicorn main:app --host 0.0.0.0 --port 8501 --reload

# 生产模式
python -m uvicorn main:app --host 0.0.0.0 --port 8501
```

### 5. 访问应用

- **主页**：http://localhost:8501
- **API文档**：http://localhost:8501/docs

## 📖 使用说明

### 上传文档

1. 在左侧"文档管理"区域点击上传区域
2. 选择本地文档（支持 PDF、Word、Markdown、TXT）
3. 等待文档处理完成

### 提问问答

1. 在右侧聊天输入框中输入问题
2. 点击发送或按 Enter 键
3. 系统会从知识库中检索相关内容并生成回答
4. 回答下方会显示引用来源

### 删除文档

在文档列表中点击"删除"按钮即可删除指定文档。

## 🔌 API 接口

### 文档上传

```
POST /api/upload
Content-Type: multipart/form-data
```

### 问答查询

```
POST /api/query
Content-Type: application/json

{
  "user_id": "string",
  "session_id": "string",
  "question": "string"
}
```

### 获取文档列表

```
GET /api/documents
```

### 删除文档

```
POST /api/delete-document
Content-Type: application/json

{
  "doc_id": 1
}
```

### 系统统计

```
GET /api/stats
```

## 📝 示例文档

项目包含 `example_doc.md` 示例文档，可用于测试问答功能。

## 📄 许可证

MIT License
