# Список изменений

Все значимые изменения в FastOpenAPI документируются в этом файле.

## [0.5.0] – 2025-04-13

### Добавлено
- **AioHttpRouter** для интеграции с фреймворком AIOHTTP (поддержка async).
- Кэш схем моделей на уровне класса для повышения производительности (избегает повторной генерации JSON Schema для одной и той же Pydantic-модели).
- Параметр `response_errors` в декораторах маршрутов для документирования ошибок в OpenAPI.
- Модуль `error_handler` для стандартных ошибок (предоставляет исключения, такие как `BadRequestError`, `ResourceNotFoundError` и др., как описано в документации).
- Поддержка базовых типов Python (`int`, `float`, `bool`, `str`) как `response_model` (для простых ответов).

## [0.4.0] – 2025-03-20

### Добавлено
- Поддержка **ReDoc UI**. Интерфейс ReDoc теперь доступен по умолчанию (например, по адресу `/redoc`).
- **TornadoRouter** для интеграции с фреймворком Tornado.

### Изменено
- Обновлены все тесты для повышения покрытия и надёжности.

### Исправлено
- Код ответа при внутренних ошибках: изменён с 422 на 500 для необработанных исключений, чтобы лучше соответствовать стандартам HTTP.

### Удалено
- Удалены методы `add_docs_route` и `add_openapi_route` из `BaseRouter`. Маршруты документации теперь добавляются автоматически, так что эти методы больше не нужны.

## [0.3.1] – 2025-03-15

### Исправлено
- Исправлена ошибка импорта роутеров при отсутствии установленного фреймворка (защита от `ModuleNotFoundError`).

## [0.3.0] – 2025-03-15

### Добавлено
- **QuartRouter** для интеграции с фреймворком Quart (асинхронный аналог Flask).
- Начальная документация (введение и примеры базового использования) добавлена в репозиторий.

### Изменено
- Упрощён синтаксис импорта роутеров: теперь можно писать `from fastopenapi.routers import YourRouter` вместо длинных путей.

### Исправлено
- Исправлено извлечение параметров из моделей Pydantic в GET-маршрутах. Параметры из query на основе моделей теперь работают корректно.

## [0.2.1] – 2025-03-12

### Исправлено
- Исправлена сериализация ответов: `_serialize_response` теперь корректно преобразует `BaseModel` в словарь перед JSON-сериализацией.
- Устранена ошибка в `DataLoader`, вызывавшая сбой при пустых данных (возможно, используется внутри генератора схем).
- Добавлены тесты, покрывающие описанные случаи.
- Добавлен этот файл `CHANGELOG.md` для отслеживания изменений.

## [0.2.0] – 2025-03-11

### Добавлено
- Реализован `resolve_endpoint_params` в `BaseRouter` для разрешения параметров (path, query, body) и интеграции с валидацией Pydantic.
- Параметр `prefix` в `include_router`, позволяющий группировать маршруты под одним префиксом.
- Поддержка `status_code` в декораторах маршрутов (установка кода по умолчанию).

### Изменено
- Рефакторинг всех реализаций роутеров для унификации и снижения дублирования.

### Удалено
- Удалён метод `register_routes` из реализации для Starlette (устарел после рефакторинга).

## [0.1.0] – 2025-03-01

### Добавлено
- Первый релиз FastOpenAPI.
- Реализован основной функционал:
  - Базовые классы и структура роутеров.
  - Поддержка роутеров для Falcon, Flask, Sanic, Starlette.
  - Генерация схем OpenAPI с использованием Pydantic v2.
  - Базовая валидация параметров запроса и тела.
- Добавлена документация (README) и несколько примеров.
- Добавлен начальный набор тестов, покрывающий регистрацию маршрутов и генерацию схем.
