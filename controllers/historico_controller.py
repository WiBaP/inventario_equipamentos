from fastapi import APIRouter, HTTPException
from service.historico_service import HistoricoService

router = APIRouter(prefix="/historico", tags=["Historico"])
service = HistoricoService()


@router.get("/dispositivo/{dispositivo_id}")
def listar_por_dispositivo(dispositivo_id: int):
    """Lista o histórico de um dispositivo específico"""
    historico = service.listar_por_dispositivo(dispositivo_id)
    return historico


@router.get("/todos")
def listar_todos():
    """Lista todo o histórico de alterações"""
    historico = service.listar_todos()
    return historico