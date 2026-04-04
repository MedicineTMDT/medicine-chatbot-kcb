import json
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from api.schemas import ChatRequest, ChatResponse, DocumentMetadata
from src.chains import get_rag_chain, get_condense_chain 
from src.tools import get_medicine_tools_definition, AVAILABLE_TOOLS
from src.prompts import build_tool_agent_prompt
from src.llms import get_llm
from src.utils import format_history_to_string
from db import get_db, crud
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

@router.post("/")
async def ask_question_stream(request: ChatRequest, db: Session = Depends(get_db)):
    rag_chain = get_rag_chain()
    condense_chain = get_condense_chain()
    llm = get_llm(temperature=0.0)

    try:
        conversation_id = request.conversation_id
        if not conversation_id:
            new_conv = crud.create_conversation(db=db, user_id=request.user_id, title="New Conversation")
            conversation_id = new_conv.id

        raw_history = crud.get_chat_history(db=db, conversation_id=conversation_id, limit=6)
        chat_history = [("human" if msg.role == "user" else "ai", msg.content) for msg in raw_history]

        crud.save_message(db=db, conversation_id=conversation_id, role="user", content=request.question)

        async def event_generator():
            full_answer = ""
            retrieved_docs = []
            tool_calls_executed = []
            
            try:
                start_chunk = ChatResponse(type="start", conversation_id=conversation_id)
                yield f"data: {start_chunk.model_dump_json()}\n\n"

                # 1. Condense phase
                standalone_question = await condense_chain.ainvoke({
                    "question": request.question,
                    "chat_history": chat_history 
                })

                # 2. Tool detection phase
                tools = get_medicine_tools_definition()
                system_prompt = build_tool_agent_prompt().format(
                    chat_history=format_history_to_string(chat_history),
                    standalone_question=standalone_question
                )
                
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=standalone_question)
                ]

                # Bind tools to LLM
                llm_with_tools = llm.bind_tools(tools)
                ai_msg = await llm_with_tools.ainvoke(messages)
                
                tool_was_called = False
                
                # Tool Loop
                while ai_msg.tool_calls:
                    tool_was_called = True
                    messages.append(ai_msg)
                    
                    for tool_call in ai_msg.tool_calls:
                        tool_name = tool_call["name"]
                        tool_args = tool_call["args"]
                        
                        # Notify frontend about tool start
                        yield f"data: {ChatResponse(type='tool_start', answer=f'Đang tra cứu chuyên sâu về {tool_name}...').model_dump_json()}\n\n"
                        
                        # Execute internal tool
                        tool_func = AVAILABLE_TOOLS.get(tool_name)
                        if tool_func:
                            result = await tool_func(**tool_args)
                        else:
                            result = {"error": f"Tool {tool_name} not found"}
                            
                        tool_calls_executed.append({
                            "name": tool_name,
                            "args": tool_args,
                            "result": result
                        })
                        
                        messages.append(ToolMessage(
                            tool_call_id=tool_call["id"],
                            content=json.dumps(result, ensure_ascii=False)
                        ))
                    
                    # Call LLM again to decide next step
                    ai_msg = await llm_with_tools.ainvoke(messages)

                # 3. Final generation or Fallback
                if tool_was_called:
                    # Final response after tools
                    async for chunk in llm.astream(messages):
                        token = chunk.content
                        full_answer += token
                        yield f"data: {ChatResponse(type='stream', answer=token).model_dump_json()}\n\n"
                else:
                    # Fallback to existing RAG chain
                    # Note: RAG chain already handles history, but we use standalone for purity
                    async for chunk in rag_chain.astream({
                        "question": standalone_question,
                        "chat_history": [] 
                    }):
                        if "context" in chunk:
                            retrieved_docs = chunk["context"]
                        elif "answer" in chunk:
                            token = chunk["answer"]
                            full_answer += token
                            yield f"data: {ChatResponse(type='stream', answer=token).model_dump_json()}\n\n"

                # 4. Cleanup & Save
                sources_list = [
                    DocumentMetadata(page_content=doc.page_content, **doc.metadata) for doc in retrieved_docs
                ]
                
                crud.save_message(
                    db=db, 
                    conversation_id=conversation_id, 
                    role="assistant", 
                    content=full_answer,
                    sources=[s.model_dump() for s in sources_list],
                    tool_calls=tool_calls_executed if tool_calls_executed else None
                )
                
                end_chunk = ChatResponse(type="end", sources=sources_list if sources_list else None)
                yield f"data: {end_chunk.model_dump_json()}\n\n"

            except Exception as e:
                error_chunk = ChatResponse(type="error", answer=f"Lỗi xử lý luồng: {str(e)}")
                yield f"data: {error_chunk.model_dump_json()}\n\n"
        
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))