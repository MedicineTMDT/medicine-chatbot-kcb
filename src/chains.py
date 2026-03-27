from operator import itemgetter
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableParallel
from src.llms import get_llm
from src.prompts import build_rag_prompt
from src.utils import format_docs, format_history_to_string
from db import get_vector_store
from functools import lru_cache
from langchain_core.output_parsers import StrOutputParser

@lru_cache(maxsize=1)
def get_rag_chain():
    llm = get_llm(temperature=0.1)
        
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    RAG_PROMPT_TEMPLATE = build_rag_prompt()
    prompt = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
    
    answer_chain = (
        prompt 
        | llm 
        | StrOutputParser()
    )

    rag_chain = RunnableParallel(
        {
            "context": itemgetter("question") | retriever, 
            "question": itemgetter("question"),
            "chat_history": itemgetter("chat_history") | RunnableLambda(format_history_to_string)
        }
    ).assign(
        answer=(
            RunnablePassthrough.assign(
                context=lambda x: format_docs(x["context"]) 
            )
            | answer_chain
        )
    )
    
    return rag_chain