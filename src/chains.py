from operator import itemgetter
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from src.llms import get_llm
from src.prompts import build_rag_prompt
from src.utils import format_docs, format_history_to_string
from db import get_vector_store
from api.schemas.chat import ChatResponse
from functools import lru_cache

@lru_cache(maxsize=1)
def get_rag_chain():
    llm = get_llm(temperature=0.1)
    
    structured_llm = llm.with_structured_output(ChatResponse)
    
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    RAG_PROMPT_TEMPLATE = build_rag_prompt()
    prompt = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
    
    rag_chain = (
        {
            "context": itemgetter("question") | retriever | format_docs, 
            
            "question": itemgetter("question"),
            
            "chat_history": itemgetter("chat_history") | RunnableLambda(format_history_to_string)
        }
        | prompt
        | structured_llm
    )
    
    return rag_chain