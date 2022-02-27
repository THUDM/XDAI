from pipelines import pipeline
from fastapi import FastAPI, Request, Depends
import uvicorn
from fastapi import FastAPI, Request, Depends
from pydantic import BaseModel
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
#query = "The Winter Olympics are mainly held by regions all over the world. They are the largest comprehensive winter sports in the world."
nlp = pipeline("question-generation")
#res= nlp(query)
#print(res)


app = FastAPI()

class Item_cpm(BaseModel):
    query:str
    limit:int = 60

@app.get("/t5QG")
async def root(request_data: Item_cpm):
    input = request_data.query
    limit = request_data.limit
    is_wrong = False
    try:
        res= nlp(input)
    except Exception as e:
        if str(e)=="substring not found":
            try:
                res= nlp(input)
            except Exception as e:
                is_wrong = True
    if is_wrong:
        return_msg = {"code":1}
    else:
        return_msg = {"code":0,"data":res}
    return return_msg


if __name__ == '__main__':
    uvicorn.run(app="main:app", host="0.0.0.0", port=19596, reload=True, debug=True)







