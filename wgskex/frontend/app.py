from fastapi import FastAPI

from wgskex.common import KexInfo

app = FastAPI()


@app.post("/api/v1/wg/key/exchange")
async def wg_key_exchange(kex_info: KexInfo):
    print(f"Received request for domain {kex_info.domain} with public key: {kex_info.public_key}.")
    return {"status": "OK"}
