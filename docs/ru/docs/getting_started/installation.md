# Установка

FastOpenAPI доступен на PyPI и поддерживает **Python 3.10+**. Вы можете установить только основную библиотеку или включить дополнительные зависимости для определённых веб-фреймворков.

## Предварительные требования

- **Python 3.10 или новее** – FastOpenAPI требует Python 3.10+ из-за использования современных аннотаций типов и Pydantic v2.
- (Необязательно) Установленный веб-фреймворк (например, Flask, Starlette и др.), если вы планируете интеграцию. Если фреймворк ещё не установлен, использование нужной опции pip (см. ниже) установит его автоматически.

## Установка через pip

#### Установка только FastOpenAPI  
*Обычная установка*
```bash
pip install fastopenapi
```

#### Установка FastOpenAPI с определённым фреймворком  
*Полезно, если вы начинаете новый сервис и ещё не установили фреймворк*
```bash
pip install fastopenapi[aiohttp]
```
```bash
pip install fastopenapi[falcon]
```
```bash
pip install fastopenapi[flask]
```
```bash
pip install fastopenapi[quart]
```
```bash
pip install fastopenapi[sanic]
```
```bash
pip install fastopenapi[starlette]
```
```bash
pip install fastopenapi[tornado]
```
```bash
pip install fastopenapi[django]
```

---
