from src.utils import format_docs, format_history_to_string

def test_format_docs_success():
    class MockDoc:
        def __init__(self, content):
            self.page_content = content

    docs = [MockDoc("Tác dụng của Paracetamol"), MockDoc("Liều dùng cho người lớn")]
    result = format_docs(docs)

    assert '<doc id="1">\nTác dụng của Paracetamol\n</doc>' in result
    assert '<doc id="2">\nLiều dùng cho người lớn\n</doc>' in result

def test_format_docs_empty():
    assert format_docs([]) == ""

# ==========================================
# TEST LỊCH SỬ CHAT
# ==========================================

def test_format_history_empty():
    assert format_history_to_string([]) == "Không có lịch sử trò chuyện trước đó."

def test_format_history_normal():
    history = [("human", "Đau đầu uống gì?"), ("ai", "Bạn nên uống Paracetamol.")]
    result = format_history_to_string(history)

    assert "<user>Đau đầu uống gì?</user>" in result
    assert "<assistant>Bạn nên uống Paracetamol.</assistant>" in result

def test_format_history_truncation():
    long_msg = "A" * 510 
    history = [("human", long_msg)]
    
    result = format_history_to_string(history, max_chars_per_msg=500)
    
    assert "... [đã cắt bớt]</user>" in result
    assert len(result) < 550  
