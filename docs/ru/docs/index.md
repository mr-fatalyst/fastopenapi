# FastOpenAPI

<p align="center">
  <img src="https://raw.githubusercontent.com/mr-fatalyst/fastopenapi/master/logo.png" alt="Логотип">
</p>

<p align="center">
  <b>FastOpenAPI</b> — это библиотека для генерации и интеграции OpenAPI-схем с использованием Pydantic и различных фреймворков.
</p>

<p align="center">
  Этот проект вдохновлён <a href="https://fastapi.tiangolo.com/">FastAPI</a> и стремится обеспечить такой же удобный опыт для разработчиков.
</p>

<p align="center">
  <img src="https://img.shields.io/github/license/mr-fatalyst/fastopenapi">
  <img src="https://github.com/mr-fatalyst/fastopenapi/actions/workflows/master.yml/badge.svg">
  <img src="https://codecov.io/gh/mr-fatalyst/fastopenapi/branch/master/graph/badge.svg?token=USHR1I0CJB">
  <img src="https://img.shields.io/pypi/v/fastopenapi">
  <img src="https://img.shields.io/pypi/pyversions/fastopenapi">
  <img src="https://static.pepy.tech/badge/fastopenapi" alt="Загрузки с PyPI">
</p>

---

## О проекте

**FastOpenAPI** — это библиотека для Python, предназначенная для генерации и интеграции OpenAPI-схем с использованием моделей Pydantic в различных веб-фреймворках. Вдохновлённая FastAPI, она предлагает аналогичный удобный опыт для таких фреймворков, как AIOHTTP, Falcon, Flask, Quart, Sanic, Starlette и Tornado. С помощью FastOpenAPI вы можете добавить интерактивную документацию API и валидацию запросов/ответов к существующему приложению без необходимости менять фреймворк.

FastOpenAPI находится в активной разработке (до версии 1.0). Несмотря на то, что библиотека уже пригодна к использованию, возможны изменения. Обратная связь и участие в разработке приветствуются.

## Возможности

- **Автоматическая генерация схем OpenAPI** — определите маршруты и модели, и FastOpenAPI сгенерирует полноценную OpenAPI-схему.
- **Поддержка Pydantic v2** — используйте Pydantic для валидации и сериализации данных. Проверяются как запросы, так и ответы.
- **Интеграция с несколькими фреймворками** — из коробки поддерживаются AIOHTTP, Falcon, Flask, Quart, Sanic, Starlette и Tornado.
- **Маршрутизация в стиле FastAPI** — используйте декораторы `@router.get`, `@router.post` и т.п., как в FastAPI.
- **Интерактивная документация** — Swagger UI доступен по `/docs`, ReDoc — по `/redoc`.
- **Валидация запросов и обработка ошибок** — некорректные данные возвращают ошибку в формате JSON. В комплекте идут классы исключений для 400, 404 и других стандартных ошибок.

Используйте навигацию слева, чтобы изучить документацию. Начните с разделов **Установка** и **Быстрый старт**, затем перейдите к **Использование**. Отдельные страницы описывают интеграцию с каждым фреймворком. Продвинутые темы и структура библиотеки описаны в разделах **Дополнительно** и **Справочник API**. Если хотите помочь — смотрите **Участие в разработке**. Список изменений — в соответствующем разделе, а часто задаваемые вопросы — в **ЧаВо**.
