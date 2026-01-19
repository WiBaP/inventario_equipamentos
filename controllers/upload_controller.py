from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from service.upload_service import UploadService

router = APIRouter()
upload_service = UploadService()

@router.post("/upload-termo/{usuario}")
async def upload_termo(usuario: str, file: UploadFile = File(...)):
    try:
        caminho = await upload_service.salvar_termo(usuario, file)
        return JSONResponse({
            "status": "ok",
            "mensagem": "Termo salvo com sucesso!",
            "caminho": caminho
        })
    except Exception as e:
        return JSONResponse(
            {"status": "erro", "mensagem": str(e)},
            status_code=500
        )
