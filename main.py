import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from src.rag_chain import RAGChain
from config import Config

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["TRANSFORMERS_OFFLINE"] = "0"

app = FastAPI(title="企业私有知识库问答系统", version="1.0.0")

rag_chain = None

def init_rag_chain():
    global rag_chain
    if rag_chain is None:
        rag_chain = RAGChain()

class QueryRequest(BaseModel):
    user_id: str = ""
    session_id: str = ""
    question: str

class DeleteDocumentRequest(BaseModel):
    doc_id: int

@app.on_event("startup")
async def startup_event():
    init_rag_chain()
    Config.init_directories()

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>企业私有知识库问答系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; height: 100vh; }
        .container { display: flex; height: 100%; }
        .sidebar { width: 320px; background: #fff; border-right: 1px solid #e8e8e8; padding: 20px; display: flex; flex-direction: column; }
        .sidebar h2 { font-size: 18px; margin-bottom: 20px; color: #333; }
        .upload-area { border: 2px dashed #d9d9d9; border-radius: 8px; padding: 30px; text-align: center; cursor: pointer; transition: all 0.3s; margin-bottom: 20px; }
        .upload-area:hover { border-color: #1890ff; background: #f0f5ff; }
        .upload-area input { display: none; }
        .upload-area .icon { font-size: 40px; margin-bottom: 10px; }
        .upload-area .text { color: #999; font-size: 14px; }
        .doc-list { flex: 1; overflow-y: auto; }
        .doc-item { padding: 12px; border-radius: 6px; margin-bottom: 8px; background: #fafafa; display: flex; justify-content: space-between; align-items: center; }
        .doc-item .name { font-size: 14px; color: #333; }
        .doc-item .meta { font-size: 12px; color: #999; margin-top: 4px; }
        .doc-item .delete-btn { background: #fff; border: 1px solid #ff4d4f; color: #ff4d4f; padding: 4px 12px; border-radius: 4px; font-size: 12px; cursor: pointer; }
        .doc-item .delete-btn:hover { background: #fff1f0; }
        .chat-area { flex: 1; display: flex; flex-direction: column; }
        .chat-header { padding: 20px; background: #fff; border-bottom: 1px solid #e8e8e8; display: flex; justify-content: space-between; align-items: center; }
        .chat-header h1 { font-size: 20px; color: #333; }
        .chat-header .clear-btn { background: #fff; border: 1px solid #d9d9d9; color: #666; padding: 6px 16px; border-radius: 4px; font-size: 14px; cursor: pointer; }
        .chat-header .clear-btn:hover { background: #f5f5f5; }
        .messages { flex: 1; overflow-y: auto; padding: 20px; }
        .message { margin-bottom: 20px; }
        .message.user .content { background: #1890ff; color: #fff; border-radius: 0 12px 12px 12px; }
        .message.assistant .content { background: #fff; color: #333; border-radius: 12px 0 12px 12px; border: 1px solid #e8e8e8; }
        .message .content { max-width: 70%; padding: 12px 16px; font-size: 15px; line-height: 1.6; }
        .message.user { display: flex; justify-content: flex-end; }
        .message.assistant { display: flex; justify-content: flex-start; }
        .message .sources { margin-top: 8px; font-size: 12px; color: #999; padding-left: 16px; }
        .input-area { padding: 20px; background: #fff; border-top: 1px solid #e8e8e8; }
        .input-wrapper { display: flex; gap: 12px; }
        .input-wrapper input { flex: 1; padding: 12px 16px; border: 1px solid #d9d9d9; border-radius: 8px; font-size: 15px; outline: none; }
        .input-wrapper input:focus { border-color: #1890ff; }
        .input-wrapper button { padding: 12px 24px; background: #1890ff; color: #fff; border: none; border-radius: 8px; font-size: 15px; cursor: pointer; }
        .input-wrapper button:hover { background: #40a9ff; }
        .loading { color: #999; font-size: 14px; padding-left: 16px; }
        .stats { margin-top: 20px; padding-top: 20px; border-top: 1px solid #e8e8e8; font-size: 14px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h2>📁 文档管理</h2>
            <div class="upload-area" id="uploadArea">
                <input type="file" id="fileInput" multiple accept=".pdf,.docx,.md,.txt">
                <div class="icon">📤</div>
                <div class="text">点击或拖拽上传文档</div>
                <div class="text" style="font-size: 12px; margin-top: 4px;">支持 PDF、Word、Markdown、TXT</div>
            </div>
            <div class="doc-list" id="docList">
                <div style="text-align: center; color: #999; padding: 20px;">暂无文档</div>
            </div>
            <div class="stats" id="stats"></div>
        </div>
        <div class="chat-area">
            <div class="chat-header">
                <h1>💬 企业私有知识库问答系统</h1>
                <button class="clear-btn" onclick="clearChat()">清空对话</button>
            </div>
            <div class="messages" id="messages"></div>
            <div class="input-area">
                <div class="input-wrapper">
                    <input type="text" id="questionInput" placeholder="请输入您的问题..." onkeydown="if(event.key==='Enter')sendQuestion()">
                    <button onclick="sendQuestion()">发送</button>
                </div>
                <div class="loading" id="loading" style="display: none;">正在检索知识库...</div>
            </div>
        </div>
    </div>
    <script>
        let userId = localStorage.getItem('userId') || generateUUID();
        let sessionId = localStorage.getItem('sessionId') || generateUUID();
        
        localStorage.setItem('userId', userId);
        localStorage.setItem('sessionId', sessionId);
        
        function generateUUID() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        }
        
        async function sendQuestion() {
            const input = document.getElementById('questionInput');
            const question = input.value.trim();
            if (!question) return;
            
            input.value = '';
            addMessage('user', question);
            document.getElementById('loading').style.display = 'block';
            
            try {
                const response = await fetch('/api/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId, session_id: sessionId, question: question })
                });
                const result = await response.json();
                
                if (result.success) {
                    addMessage('assistant', result.answer, result.sources);
                } else {
                    addMessage('assistant', '查询失败: ' + result.message);
                }
            } catch (error) {
                addMessage('assistant', '网络错误: ' + error.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        function addMessage(role, content, sources = []) {
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = 'message ' + role;
            
            let sourcesHtml = '';
            if (sources && sources.length > 0) {
                sourcesHtml = '<div class="sources">引用来源:<br>' + sources.map(s => '- ' + s).join('<br>') + '</div>';
            }
            
            div.innerHTML = '<div class="content">' + content + '</div>' + sourcesHtml;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function clearChat() {
            sessionId = generateUUID();
            localStorage.setItem('sessionId', sessionId);
            document.getElementById('messages').innerHTML = '';
        }
        
        document.getElementById('uploadArea').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
        
        document.getElementById('fileInput').addEventListener('change', async (e) => {
            const files = e.target.files;
            if (!files.length) return;
            
            for (const file of files) {
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/api/upload', {
                        method: 'POST',
                        body: formData
                    });
                    const result = await response.json();
                    alert(result.message);
                } catch (error) {
                    alert('上传失败: ' + error.message);
                }
            }
            loadDocuments();
            e.target.value = '';
        });
        
        async function loadDocuments() {
            try {
                const response = await fetch('/api/documents');
                const documents = await response.json();
                const docList = document.getElementById('docList');
                
                if (documents.length === 0) {
                    docList.innerHTML = '<div style="text-align: center; color: #999; padding: 20px;">暂无文档</div>';
                } else {
                    docList.innerHTML = documents.map(doc => `
                        <div class="doc-item">
                            <div>
                                <div class="name">${doc.filename}</div>
                                <div class="meta">${doc.file_type} | ${(doc.file_size/1024).toFixed(1)} KB | ${doc.chunk_count} 片段</div>
                            </div>
                            <button class="delete-btn" onclick="deleteDocument(${doc.id})">删除</button>
                        </div>
                    `).join('');
                }
            } catch (error) {
                console.error('加载文档失败:', error);
            }
        }
        
        async function deleteDocument(docId) {
            if (!confirm('确定要删除这个文档吗？')) return;
            
            try {
                const response = await fetch('/api/delete-document', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ doc_id: docId })
                });
                const result = await response.json();
                if (result.success) {
                    loadDocuments();
                    alert('删除成功');
                } else {
                    alert('删除失败: ' + result.message);
                }
            } catch (error) {
                alert('删除失败: ' + error.message);
            }
        }
        
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                document.getElementById('stats').innerHTML = `向量库文档总数: <strong>${stats.total_documents}</strong>`;
            } catch (error) {
                console.error('加载统计信息失败:', error);
            }
        }
        
        loadDocuments();
        loadStats();
        setInterval(loadDocuments, 5000);
        setInterval(loadStats, 10000);
    </script>
</body>
</html>
"""

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(Config.UPLOAD_DIR, file.filename)
        
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        result = rag_chain.upload_and_index(file_path)
        
        if result["success"]:
            return {"success": True, "message": result["message"]}
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query")
async def query(request: QueryRequest):
    try:
        user_id = request.user_id or str(uuid.uuid4())
        session_id = request.session_id or str(uuid.uuid4())
        
        result = rag_chain.query(
            user_id=user_id,
            session_id=session_id,
            question=request.question
        )
        
        if result["success"]:
            return {"success": True, "answer": result["answer"], "sources": result.get("sources", [])}
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
async def get_documents():
    try:
        documents = rag_chain.get_documents()
        return [{
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "chunk_count": doc.chunk_count,
            "status": doc.status
        } for doc in documents]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/delete-document")
async def delete_document(request: DeleteDocumentRequest):
    try:
        success = rag_chain.delete_document(request.doc_id)
        if success:
            return {"success": True, "message": "文档删除成功"}
        else:
            return {"success": False, "message": "文档删除失败"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    try:
        stats = rag_chain.get_collection_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
