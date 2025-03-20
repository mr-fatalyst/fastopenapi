from flask import Flask
from pydantic import BaseModel

from fastopenapi.routers import FlaskRouter

app = Flask(__name__)
router = FlaskRouter(app=app)


class HelloResponse(BaseModel):
    message: str


@router.get("/hello", tags=["Hello"], status_code=200, response_model=HelloResponse)
def hello(name: str):
    """Say hello from Flask"""
    return HelloResponse(message=f"Hello, {name}! It's Flask!")


if __name__ == "__main__":
    app.run(port=8000)
