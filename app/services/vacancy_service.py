import httpx, json
from typing import List, Dict, Any
from loguru import logger

API_BASE_URL = "https://opendata.trudvsem.ru/api/v1/vacancies"

async def fetch_vacancies(query: str, per_page: int = 20) -> List[Dict[str, Any]]:
    """
    Асинхронно запрашивает вакансии с API Работа России по заданному запросу.
    Возвращает список словарей с данными о вакансиях.
    """
    logger.info(f"Fetching vacancies from Trudvsem for query='{query}'")
    
    # Формирование параметров запроса для поиска по тексту и пагинации
    params = {
        "text": query,       # Ключевое слово для поиска
        "limit": per_page,   # Количество результатов на странице
        "offset": 0          # Начинает с первой страницы
    }

    try:
        async with httpx.AsyncClient() as client:
            # Отправляем GET-запрос к API
            response = await client.get(API_BASE_URL, params=params, timeout=15.0)
            response.raise_for_status() # Проверяем, не было ли ошибок HTTP
            data = response.json()
            with open("debug_response.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Извлекаем список вакансий из ответа
            # Путь к вакансиям в ответе: data -> results -> vacancies
            vacancies_data = data.get("results", {}).get("vacancies", [])
            
            # В ответе каждая вакансия обёрнута в объект {"vacancy": { ... }},
            # поэтому будет извлекаться внутренний словарь
            vacancies = [item.get("vacancy", {}) for item in vacancies_data if item.get("vacancy")]
            
            logger.info(f"Successfully fetched {len(vacancies)} vacancies")
            return vacancies
            
    except httpx.TimeoutException:
        logger.error(f"Timeout while fetching from Trudvsem for query '{query}'")
        raise # Пробрасываем исключение дальше для обработки в роутере
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code} while fetching from Trudvsem")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise


def map_vacancy_to_db(vacancy_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Преобразует словарь с данными о вакансии от API Работа России в словарь,
    который подходит для создания объекта модели Vacancy в нашей БД.
    """
    title = vacancy_data.get("job-name", "")
    if not title:
        title = vacancy_data.get("job_name", "") # Запасной вариант

    # Название компании
    company = vacancy_data.get("company-name", "")
    if not company:
        company = vacancy_data.get("company_name", "")

    # Ссылка на вакансию — в API Работа России это поле "vac_url"
    url = vacancy_data.get("vac_url", "")
    if not url:
        # На всякий случай, если vac_url нет, можно оставить пустым, такая вакансия не будет сохраненяться
        url = ""

    # Извлекаем зарплату
    salary_data = vacancy_data.get("salary")
    salary_str = ""
    if isinstance(salary_data, dict):
        min_salary = salary_data.get("min", "")
        max_salary = salary_data.get("max", "")
        if min_salary and max_salary:
            salary_str = f"{min_salary} - {max_salary}"
        elif min_salary:
            salary_str = f"от {min_salary}"
        elif max_salary:
            salary_str = f"до {max_salary}"
    elif isinstance(salary_data, str):
        salary_str = salary_data
    
    # Возврат словаря, ключи которого соответствуют полям модели Vacancy
    return {
        "title": title,
        "company": company,
        "url": url,
        "status": "new",         # Статус по умолчанию для новых вакансий
        # "salary": salary_str, # Пока закомментируем, если в модели Vacancy нет этого поля
    }
