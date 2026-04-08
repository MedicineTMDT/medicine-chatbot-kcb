from operator import itemgetter
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableParallel
from src.llms import get_llm
from functools import lru_cache
from src.prompts import build_rag_prompt, build_condense_prompt
from src.utils import format_docs, format_history_to_string
from db import get_vector_store
from langchain_core.output_parsers import StrOutputParser

@lru_cache(maxsize=1)
def get_condense_chain():
    """
    Exposes the condense chain separately to rephrase questions 
    before tool calling or RAG.
    """
    llm = get_llm(temperature=0.0)
    condense_prompt = PromptTemplate.from_template(build_condense_prompt())
    condense_chain = (
        condense_prompt 
        | llm 
        | StrOutputParser()
    )
    return condense_chain

@lru_cache(maxsize=1)
def get_rag_chain():
    llm = get_llm(temperature=0.1)
        
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    # Reuse the condense chain
    condense_chain = get_condense_chain()

    # 2. Main RAG Logic
    RAG_PROMPT_TEMPLATE = build_rag_prompt()
    prompt = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
    
    answer_chain = (
        prompt 
        | llm 
        | StrOutputParser()
    )

    rag_chain = (
        RunnablePassthrough.assign(
            chat_history=lambda x: format_history_to_string(x["chat_history"])
        )
        | RunnablePassthrough.assign(
            standalone_question=condense_chain
        )
        | RunnableParallel(
            {
                "context": itemgetter("standalone_question") | retriever, 
                "question": itemgetter("question"),
                "chat_history": itemgetter("chat_history")
            }
        )
        | RunnablePassthrough.assign(
            answer=(
                RunnablePassthrough.assign(
                    context=lambda x: format_docs(x["context"]) 
                )
                | answer_chain
            )
        )
    )
    
    return rag_chain