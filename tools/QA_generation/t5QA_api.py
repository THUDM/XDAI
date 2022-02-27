from t5QA.pipelines import pipeline
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import os,sys
from pathlib import Path
os.environ["TOKENIZERS_PARALLELISM"] = "false"
nlp = pipeline("question-generation")
BASE_DIR = str(Path(__file__).parent.parent.parent)
sys.path.append(os.path.join(BASE_DIR))
#from config import CONFIG

app = FastAPI()

class ItemCpm(BaseModel):
    query:str = ""
    # query = "The Winter Olympics are mainly held by regions all over the world. They are the largest comprehensive winter sports in the world."


@app.get("/t5QG")
async def root(request_data: ItemCpm):
    input = request_data.query
    is_wrong = False
    try:
        res= nlp(input)
    except Exception as e:
        if str(e)=="substring not found":
            try:
                res= nlp(input)
            except Exception as e:
                print(e)
                is_wrong = True
    if is_wrong:
        return_msg = {"code":1}
    else:
        return_msg = {"code":0,"data":res}
    return return_msg


if __name__ == '__main__':
    uvicorn.run(app="t5QA_api:app", host="0.0.0.0", port=19596, reload=True, debug=True)







