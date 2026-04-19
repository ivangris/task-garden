from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_extractions() -> dict[str, str]:
    return {"status": "not_implemented"}

