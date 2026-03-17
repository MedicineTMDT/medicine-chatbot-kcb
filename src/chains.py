from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

from src.llms.openai_llm import get_llm
from src.prompts import build_rag_prompt
from src.utils import format_docs
from vector_db import get_vector_store
from api.schemas.response import ChatResponse

def get_rag_chain():

    llm = get_llm(temperature=0.1)
    
    structured_llm = llm.with_structured_output(ChatResponse)
    
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    RAG_PROMPT_TEMPLATE = build_rag_prompt()
    
    prompt = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
    
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | structured_llm
    )
    
    return rag_chain