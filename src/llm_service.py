from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from config import Config
from typing import List

class LLMService:
    """LLM服务管理器，负责与阿里云百炼模型交互"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name=Config.LLM_MODEL,
            openai_api_key=Config.LLM_API_KEY,
            openai_api_base=Config.LLM_BASE_URL,
            temperature=0.1,
            max_tokens=2000
        )
        
        self.system_prompt = """
你是一个专业的企业知识库问答助手。请根据提供的上下文回答用户问题。

回答规则：
1. 必须基于提供的上下文信息进行回答，不要编造信息
2. 如果上下文没有相关信息，请明确说明"未找到相关知识"
3. 回答要准确、简洁，逻辑清晰
4. 对于技术问题，尽量提供代码示例或具体步骤
5. 引用来源时要清晰标注文档名称和段落

格式要求：
- 答案使用自然语言，适当分段
- 如果有多个要点，使用列表形式
- 引用来源放在回答末尾
"""
    
    def generate_answer(self, context: str, question: str, chat_history: List = None) -> str:
        """
        根据上下文生成回答
        :param context: 检索到的上下文信息
        :param question: 用户问题
        :param chat_history: 对话历史（可选）
        :return: AI生成的回答
        """
        messages = [
            SystemMessage(content=self.system_prompt)
        ]
        
        if chat_history:
            for msg in chat_history[-5:]:
                messages.append(HumanMessage(content=msg["question"]))
                messages.append(AIMessage(content=msg["answer"]))
        
        messages.append(HumanMessage(content=f"上下文信息：\n{context}\n\n用户问题：{question}"))
        
        response = self.llm.invoke(messages)
        return response.content
    
    def format_context(self, search_results: List[dict]) -> str:
        """
        格式化检索结果为上下文文本
        :param search_results: 检索结果列表
        :return: 格式化后的上下文文本
        """
        context_parts = []
        for i, result in enumerate(search_results, 1):
            context_parts.append(f"""
【来源 {i}：{result['metadata']['filename']}】
{result['content']}
---
""")
        return "\n".join(context_parts)
    
    def get_sources(self, search_results: List[dict]) -> List[str]:
        """
        提取引用来源列表
        :param search_results: 检索结果列表
        :return: 来源列表
        """
        sources = []
        seen = set()
        for result in search_results:
            source = f"{result['metadata']['filename']}"
            if source not in seen:
                sources.append(source)
                seen.add(source)
        return sources