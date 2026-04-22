from fastapi import APIRouter

router = APIRouter(prefix="/cielo-test", tags=["cielo-test"])


@router.get("/status")
async def obter_status_teste_cielo():
    return {"success": True, "status": "available"}
