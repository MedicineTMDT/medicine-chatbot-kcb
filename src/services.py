import json
import uuid
import os
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from api.schemas import DocumentMetadata
from src.chains import get_rag_chain, get_condense_chain 
from src.tools import get_medicine_tools_definition, AVAILABLE_TOOLS
from src.prompts import build_tool_agent_prompt
from src.llms import get_llm
from src.utils import format_history_to_string, format_sse
from db import crud

BASE_URL_FILE = os.getenv("BASE_URL_FILE")

class ChatStreamHandler:
    def __init__(self, db: AsyncSession, conversation_id: uuid.UUID, question: str):
        self.db = db
        self.conversation_id = conversation_id
        self.question = question
        self.tool_was_called = False
        
        self.full_answer = ""
        self.retrieved_docs = []
        self.tool_calls_executed = []
        
        self.llm = get_llm(temperature=0.0)
        self.rag_chain = get_rag_chain()
        self.condense_chain = get_condense_chain()
        self.tools = get_medicine_tools_definition()

    async def _condense_question(self, chat_history: list) -> str:
        """Rút gọn câu hỏi dựa trên ngữ cảnh."""
        return await self.condense_chain.ainvoke({
            "question": self.question,
            "chat_history": chat_history 
        })

    async def _handle_tools_execution(self, messages: list, llm_with_tools):
        """Xử lý vòng lặp Tool Calls. Yield trực tiếp các SSE event."""
        ai_msg = await llm_with_tools.ainvoke(messages)

        while ai_msg.tool_calls:
            messages.append(ai_msg)
            
            for tool_call in ai_msg.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                yield format_sse("tool_start", answer=f"Đang tra cứu chuyên sâu về {tool_name}...")
                
                tool_func = AVAILABLE_TOOLS.get(tool_name)
                result = await tool_func(**tool_args) if tool_func else {"error": f"Tool {tool_name} not found"}
                
                self.tool_calls_executed.append({
                    "name": tool_name,
                    "args": tool_args,
                    "result": result
                })
                
                messages.append(ToolMessage(
                    tool_call_id=tool_call["id"],
                    content=json.dumps(result, ensure_ascii=False)
                ))
            
            ai_msg = await llm_with_tools.ainvoke(messages)

        if self.tool_was_called:
            async for chunk in self.llm.astream(messages):
                token = chunk.content
                self.full_answer += token
                yield format_sse("stream", answer=token)
                
    async def _handle_rag_fallback(self, standalone_question: str):
        """Xử lý RAG nếu không có Tool nào được gọi."""
        async for chunk in self.rag_chain.astream({
            "question": standalone_question,
            "chat_history": [] 
        }):
            if "context" in chunk:
                self.retrieved_docs = chunk["context"]
            elif "answer" in chunk:
                token = chunk["answer"]
                self.full_answer += token
                yield format_sse("stream", answer=token)

    async def _save_conversation(self, sources_list: list):
        """Lưu lại toàn bộ lịch sử vào database."""
        await crud.save_message(
            db=self.db, 
            conversation_id=self.conversation_id, 
            role="assistant", 
            content=self.full_answer,
            sources=[s.model_dump() for s in sources_list],
            tool_calls=self.tool_calls_executed if self.tool_calls_executed else None
        )

    async def stream_generator(self):
        """Hàm chính điều phối toàn bộ luồng."""
        try:
            yield format_sse("start", conversation_id=self.conversation_id)

            raw_history = await crud.get_chat_history(db=self.db, conversation_id=self.conversation_id, limit=6)
            chat_history = [("human" if msg.role == "user" else "ai", msg.content) for msg in raw_history]
            await crud.save_message(db=self.db, conversation_id=self.conversation_id, role="user", content=self.question)

            standalone_question = await self._condense_question(chat_history)

            system_prompt = build_tool_agent_prompt().format(
                chat_history=format_history_to_string(chat_history),
                standalone_question=standalone_question
            )
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=standalone_question)]
            llm_with_tools = self.llm.bind_tools(self.tools)

            async for event in self._handle_tools_execution(messages, llm_with_tools):
                yield event

            if not self.tool_was_called:
                async for event in self._handle_rag_fallback(standalone_question):
                    yield event

            sources_list = [
                DocumentMetadata(
                    page_content=doc.page_content,
                    source_link=BASE_URL_FILE + doc.metadata["filename"] + "#page=" + str(int(doc.metadata["page_number"])),
                    **doc.metadata
                ) for doc in self.retrieved_docs
            ]
            
            await self._save_conversation(sources_list)
            yield format_sse("end", sources=sources_list if sources_list else None)

        except Exception as e:
            yield format_sse("error", answer=f"Lỗi xử lý luồng: {str(e)}")
