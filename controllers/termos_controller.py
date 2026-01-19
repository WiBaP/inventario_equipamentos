import os
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

PASTA_TERMOS = r"C:\Users\willian.pinho\Desktop\termos"

@router.get("/termo-existe/{usuario}")
async def termo_existe(usuario: str):
    caminho = os.path.join(PASTA_TERMOS, f"{usuario}.pdf")
    return {"existe": os.path.isfile(caminho)}


@router.get("/termo-download/{usuario}")
async def termo_download(usuario: str):
    caminho = os.path.join(PASTA_TERMOS, f"{usuario}.pdf")

    if not os.path.isfile(caminho):
        return {"erro": "Arquivo não encontrado"}

    return FileResponse(
        caminho,
        media_type="application/pdf",
        filename=f"{usuario}.pdf"
    )
