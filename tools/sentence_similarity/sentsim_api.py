import uvicorn
from .sentence_sim import get_similarity_scores
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Optional, List, Any, Union
app = FastAPI()

class SentSim(BaseModel):
    target: str = ""
    candidates: List[str] = []


class ResBody(BaseModel):
    code: int = 0
    msg: str = "ok"
    debug: Optional[Any] = {}
    data: Optional[Any] = {}

@app.get("/tools/sentence_sim", summary="sentence")
async def cal_sim(item: SentSim) -> ResBody:
    target = item.target
    candidates = item.candidates
    res = get_similarity_scores(target=target, candidates=candidates)
    data = {"res": res}
    res = ResBody(data=data)
    return res


if __name__ == "__main__":
    uvicorn.run(
        app="sentsim_api:app", host="0.0.0.0", port=19502, debug=True, reload=True
    )
