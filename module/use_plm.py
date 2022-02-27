import asyncio
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import requests, json
import time
import aiohttp
from config import CONFIG


async def api_async(url="", payload={},  headers={}):
    """
    import aiohttp
    """
    if headers == {}:
        headers = {"Content-Type": "application/json;charset=utf8"}

    async with aiohttp.ClientSession(headers=headers, raise_for_status=True) as session:
        async with session.post(url, json=payload) as response:
            data = await response.json()
            return data



def req_api(url="", payload={}, method="POST", headers={}):
    if headers == {}:
        headers = {"Content-Type": "application/json;charset=utf8"}
    payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    response = requests.request(method, url, data=payload, headers=headers)
    result = response.json()
    return result

async def generate_plm(prompt="", limit=30, url=None,model="glm"):
    if url is None:
        url = CONFIG.default_plm_api
    if model == "glm":
        url = CONFIG.glm_query_api
    payload = {"content": prompt, "max_length": limit}
    #payload = {"query": prompt, "limit": limit}
    res = await api_async(url=url, payload=payload)
    if res.get("status") != 0:
        return False
    result = res.get("result")
    return result


async def getGeneratedText(prompt=[], limit=30, batchsize=1, model="ctxl"):
    limits = limit
    if isinstance(prompt, str) and batchsize:
        prompt = [prompt for _ in range(batchsize)]
    if isinstance(limits, int):
        limits = [limits for _ in range(len(prompt))]
    elif isinstance(limits, list):
        assert len(limits) == len(prompt)

    tasks = [
        asyncio.create_task(generate_plm(prompt=p, limit=l,model=model))
        for p, l in zip(prompt, limits)
    ]
    done, pending = await asyncio.wait(tasks, timeout=6)

    results = []
    for p in pending:
        p.cancel()

    for d in done:
        results.append(d.result())
    return results


if __name__ == "__main__":
    st = time.time()
    results = asyncio.run(generate_plm(prompt="你好"))
    print(time.time() - st)
    print(results)
