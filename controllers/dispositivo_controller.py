from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from service.dispositivo_service import DispositivoService
from model.dispositivo import Dispositivo
from fastapi import Cookie
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter(prefix="/dispositivos", tags=["Dispositivos"])

class DispositivoSchema(BaseModel):
    hostname: str
    serialnumber: str | None = None
    fabricante: str | None = None
    modelo: str | None = None
    cpu: str | None = None
    memoriagb: str | None = None
    ultimousuario: str | None = None
    status: str | None = None
    obs: str | None = None
    estado: str | None = None
    ignorar_conflito: bool = False


service = DispositivoService()

@router.get("/listar")
def listar():
    dispositivos = service.listar()
    return dispositivos

@router.post("/incluir")
def incluir(
    d: DispositivoSchema,
    usuario: str = Cookie(None)
):
    if not usuario:
        raise HTTPException(401, "Usuário não identificado")

    dispositivo = Dispositivo(**d.dict())

    if service.incluir(dispositivo, usuario):
        return {"message": "Dispositivo incluído com sucesso!"}

    raise HTTPException(400, "Erro ao incluir dispositivo.")


@router.put("/alterar/{id}")
def alterar(
    id: int,
    d: DispositivoSchema,
    usuario: str = Cookie(None)
):
    if not usuario:
        raise HTTPException(401, "Usuário não identificado")

    data = d.dict()
    data["id"] = id
    dispositivo = Dispositivo(**data)

    resultado = service.alterar(dispositivo, usuario)

    if isinstance(resultado, dict) and resultado.get("conflito_usuario"):
        return resultado

    if resultado:
        return {"message": "Dispositivo alterado com sucesso!"}


    raise HTTPException(400, "Erro ao alterar dispositivo.")


@router.delete("/deletar/{hostname}")
def deletar(hostname: str):
    if service.deletar(hostname):
        return {"message": "Dispositivo deletado com sucesso!"}
    raise HTTPException(400, "Erro ao deletar dispositivo.")


@router.get("/pesquisar/{termo}")
def pesquisar(termo: str):
    dispositivos = service.pesquisar(termo)
    return dispositivos

# ENDPOINT — VERIFICAR STATUS NO AD
@router.get("/verificar_ad")
def verificar_usuario_ad():
    dados = service.verificar_usuario_ad()
    return dados or []

# --------------------------
# ENDPOINT — CONFIRMAR RETIRADA DO NOTEBOOK
# --------------------------
@router.put("/confirmar_retirada/{hostname}")
def confirmar_retirada(hostname: str, usuario: str = Cookie(None)):

    if not usuario:
        raise HTTPException(401, "Usuário não identificado")

    return service.confirmar_retirada(hostname, usuario)

@router.post("/gerar-termo-usuario/{usuario}")
def gerar_termo_por_usuario(usuario: str, dados: dict):
    assinatura = dados.get("assinatura")
    
    if not assinatura:
        raise HTTPException(
            status_code=400, 
            detail="Assinatura não fornecida"
        )
    
    # Salvar PDF
    resultado = service.salvar_termo_pdf(usuario, assinatura)
    
    if not resultado:
        raise HTTPException(
            status_code=404, 
            detail=f"Nenhum dispositivo ou usuário encontrado para '{usuario}'"
        )
    
    return JSONResponse({
        "message": "PDF gerado e salvo com sucesso!",
        "arquivo": resultado['arquivo'],
        "caminho": resultado['caminho'],
        "usuario": resultado['usuario']
    })


