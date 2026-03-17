def format_docs(docs):
    """Hàm phụ trợ để nối nội dung các chunk lại với nhau thành một đoạn văn bản dài."""
    return "\n\n".join(doc.page_content for doc in docs)