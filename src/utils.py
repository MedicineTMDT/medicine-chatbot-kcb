from api.schemas import ChatResponse

def format_docs(docs):
    formatted_docs = []
    for i, doc in enumerate(docs):
        formatted_docs.append(f'<doc id="{i+1}">\n{doc.page_content}\n</doc>')
    
    return "\n\n".join(formatted_docs)

def format_history_to_string(history_tuples, max_chars_per_msg=500):
    if not history_tuples:
        return "Không có lịch sử trò chuyện trước đó."
    
    formatted_lines = []
    for role, msg in history_tuples:
        if len(msg) > max_chars_per_msg:
            msg = msg[:max_chars_per_msg] + "... [đã cắt bớt]"
            
        if role == "human":
            formatted_lines.append(f"<user>{msg}</user>")
        else:
            formatted_lines.append(f"<assistant>{msg}</assistant>")
    
    return "\n".join(formatted_lines)

def format_sse(response_type: str, **kwargs) -> str:
    chunk = ChatResponse(type=response_type, **kwargs)
    return f"data: {chunk.model_dump_json()}\n\n"
