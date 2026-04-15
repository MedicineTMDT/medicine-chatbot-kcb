import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from api.schemas import TitleRequest
from src.llms import get_llm
from db import get_db, crud
from src.prompts import build_title_prompt

router = APIRouter(
    prefix="/conversations",
    tags=["Title Generation"]
)

@router.post("/{conversation_id}/title")
async def generate_title_endpoint(
    conversation_id: uuid.UUID, 
    request: TitleRequest, 
    db: Session = Depends(get_db)
):
    llm = get_llm(temperature=0.1, model_name="gpt-4o-mini")

    try:
        prompt_template = build_title_prompt()
        prompt_text = prompt_template.format(question=request.question)
        
        response = llm.invoke(prompt_text)
        new_title = response.content.strip()

        updated_conv = crud.update_conversation_title(
            db=db, 
            conversation_id=conversation_id, 
            title=new_title
        )

        return new_title

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
