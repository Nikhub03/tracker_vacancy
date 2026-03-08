from fastapi import APIRouter

router = APIRouter(prefix="/vacancies", tags=["vacancies"])

@router.get("/")
async def get_vacancies():
    return {"vacancies": []}