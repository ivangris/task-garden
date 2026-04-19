from fastapi import APIRouter

router = APIRouter()


@router.get("")
def get_sync_status() -> dict[str, str]:
    return {"status": "not_implemented"}

