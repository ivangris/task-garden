from fastapi import APIRouter

router = APIRouter()


@router.get("")
def get_garden_state() -> dict[str, str]:
    return {"status": "not_implemented"}

