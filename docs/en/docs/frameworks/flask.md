# Flask Integration

This guide demonstrates FastOpenAPI integration with **Flask**, one of the most popular Python web frameworks.

The `FlaskRouter` class ties FastOpenAPI into the Flask routing system.

## Setup

Install FastOpenAPI:
```bash
pip install fastopenapi
```
or
```bash
pip install fastopenapi[flask]
```

## Hello World

```python
from flask import Flask
from pydantic import BaseModel
from fastopenapi.routers import FlaskRouter

app = Flask(__name__)
router = FlaskRouter(app=app)  # Attach FastOpenAPI to the Flask app

class HelloResponse(BaseModel):
    message: str

@router.get("/hello", tags=["Hello"], response_model=HelloResponse)
def hello(name: str):
    """Say hello from Flask"""
    return HelloResponse(message=f"Hello, {name}! It's Flask!")

if __name__ == "__main__":
    app.run(port=8000)

```

## Project Example

See example for this framework in the [`examples/flask/`](https://github.com/mr-fatalyst/fastopenapi/tree/master/examples/flask) directory of the repository.
