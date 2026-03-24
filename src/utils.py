def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def format_history_to_string(history_tuples):
    if not history_tuples:
        return "Không có lịch sử trò chuyện."
    
    formatted_lines = []
    for role, msg in history_tuples:
        prefix = "User" if role == "human" else "AI"
        formatted_lines.append(f"{prefix}: {msg}")
    
    return "\n".join(formatted_lines)