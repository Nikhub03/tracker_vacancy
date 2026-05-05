# app/services/hh_service.py (исправленная версия)
import httpx
from typing import List, Dict, Any
from loguru import logger

HH_API_URL = "https://api.hh.ru/vacancies"

async def fetch_vacancies_paginated(query: str, area: int = 1, pages: int = 2, per_page: int = 20) -> List[Dict[str, Any]]:
    """
    Загружает несколько страниц вакансий с hh.ru (pages = количество страниц).
    Возвращает объединённый список вакансий (items) со всех страниц.
    """
    logger.info(f"Fetching {pages} page(s) for query='{query}', area={area}")
    for page in range(pages):
        logger.debug(f"Requesting page {page}...")
        ...
        logger.info(f"Received {len(items)} vacancies from page {page}")

    all_items = []
    async with httpx.AsyncClient() as client:
        for page in range(pages):
            params = {
                "text": query,
                "area": area,
                "per_page": per_page,
                "page": page,
                "only_with_salary": False
            }
            response = await client.get(HH_API_URL, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])
            if not items:   # если на этой странице нет вакансий, прекращаем
                break
            all_items.extend(items)
    return all_items

def map_hh_vacancy_to_db(hh_item: Dict[str, Any]) -> Dict[str, Any]:
    title = hh_item.get("name", "")
    employer = hh_item.get("employer")
    company = employer.get("name") if employer else ""
    url = hh_item.get("alternate_url", "")
    return {
        "title": title,
        "company": company,
        "url": url,
        "status": "new"
    }