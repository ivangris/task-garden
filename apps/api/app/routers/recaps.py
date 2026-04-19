from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_recaps() -> dict[str, str]:
    return {"status": "not_implemented"}

