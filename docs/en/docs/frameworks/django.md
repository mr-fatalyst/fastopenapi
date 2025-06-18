# Django Integration

This guide covers using FastOpenAPI with **Django**, a high-performance web framework.

FastOpenAPI's `DjangoRouter` supports Django, via Django's urls interface.

## Setup

Install FastOpenAPI:
```bash
pip install fastopenapi
```
or
```bash
pip install fastopenapi[django]
```

## Hello World

```python
from django.conf import settings
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from django.urls import path
from pydantic import BaseModel

from fastopenapi.routers import DjangoRouter

settings.configure(DEBUG=True, SECRET_KEY="__CHANGEME__", ROOT_URLCONF=__name__)
application = get_wsgi_application()

router = DjangoRouter(app=True)


class HelloResponse(BaseModel):
    message: str


@router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
def hello(name: str):
    """Say hello from django"""
    return HelloResponse(message=f"Hello, {name}! It's Django!")


urlpatterns = [path("", router.urls)]

if __name__ == "__main__":
    call_command("runserver")

```

## Project Example

See example for this framework in the [`examples/django/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/django) directory of the repository.
