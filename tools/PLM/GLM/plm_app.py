### for internal use
import random
import time
import warnings
from typing import Optional, Any
import os
import pynvml
import torch
from pathlib import Path, PurePath

from fastapi import FastAPI
from pydantic import BaseModel
import sys
BASE_DIR = str(Path(__file__).parent.parent)
sys.path.append(os.path.join(BASE_DIR, ""))
from generate_text import generate_samples,get_prepared


app = FastAPI()
sentinel = {}
pynvml.nvmlInit()


class BotModel(BaseModel):
    query: str = None
    limit: int = 30


class BotsBody(BaseModel):
    code: int = 0
    data: Optional[Any]
    cost: float = 0
    msg: str = "okay"


def usegpu(num=1,min_space=24*1024**3):
    available = []
    total_devices =pynvml.nvmlDeviceGetCount()
    for index in range(total_devices):
        handle = pynvml.nvmlDeviceGetHandleByIndex(index)
        meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle)
        unused = meminfo.total - meminfo.used
        if unused >= min_space:
            available.append(index)
    cnt = min(len(available), num)
    if cnt > 0:
        os.environ["CUDA_VISIBLE_DEVICES"] = ",".join(map(str, available[:cnt]))
        return available[:cnt]
    else:
        return None

@app.on_event("startup")
async def startup_event():
    # todo is_gpu_available is better
    gpus = usegpu(num=1)
    if not gpus:
        warnings.warn("No GPU available")
    gpu = gpus[0]
    #logger.info(f"use GPU:{gpu}")
    print(f"use GPU:{gpu}")
    os.environ["MASTER_PORT"] = str(random.randint(6010, 6200))
    sentinel["model"], sentinel["tokenizer"], sentinel["param"] = get_prepared()
    #logger.info("Startup....")
    print("Startup....")


#@app.get("/health", summary="beat health")
async def health():
    gpus = usegpu(num=1)
    return {"gpu": gpus[0] }


@app.post("/glm", summary="ask bot by query string||", response_model=BotsBody)
async def bot_ask(item: BotModel):
    sentinel["param"].out_seq_length = item.limit

    st = time.time()
    res = generate_samples(
        item.query,
        sentinel["model"],
        sentinel["tokenizer"],
        sentinel["param"],
        torch.cuda.current_device(),
    )
    if res:
        et = time.time() - st
        return BotsBody(data=res, cost=et)
    else:
        return BotsBody(code=-1, msg="Failed")

if __name__ == "__main__":
    #uvicorn.run("PLM.plm_app:app", host="0.0.0.0", port=19567)
    # uvicorn PLM.plm_app:app  --port 19567 --host '0.0.0.0'  --reload --debug
    pass