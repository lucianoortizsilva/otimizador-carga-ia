import logging
import os
import sys

from fastapi import FastAPI, Response

from models import OtimizarCargaRequest
from service import otimizar_carga as otimizar_carga_service


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("otimizador-carga")

APP_NAME = os.getenv("APP_NAME", "otimizador-carga-ia")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")

app = FastAPI(title=APP_NAME, version=APP_VERSION)


@app.post("/otimizar-carga")
def otimizar_carga(payload: OtimizarCargaRequest) -> Response:
    logger.info(
        "Requisição recebida com %d SKU(s) e regra de caminhão %d->%d",
        len(payload.skus),
        payload.regra_caminhao.id_origem,
        payload.regra_caminhao.id_destino,
    )
    conteudo_json = otimizar_carga_service(payload)
    return Response(content=conteudo_json, media_type="application/json")


@app.get("/health")
def health() -> dict:
    return {"status": "up", "app": APP_NAME, "version": APP_VERSION}


if __name__ == "__main__":
    import uvicorn

    # VII. Port binding — host/porta vêm do ambiente.
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host=host, port=port, reload=False)