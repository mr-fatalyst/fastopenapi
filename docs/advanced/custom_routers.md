# Custom Routers

This guide explains how to create a custom router for integrating FastOpenAPI with a new web framework.

## When to Create a Custom Router

Create a custom router when:

- You want to integrate FastOpenAPI with an unsupported framework
- You need custom behavior that differs from existing routers
- You're building a framework and want FastOpenAPI support

## Architecture Overview

FastOpenAPI uses a three-tier composition-based adapter pattern:

```
BaseRouter (route registration, OpenAPI generation)
    ↓ inherits
BaseAdapter (request pipeline via composition)
    ↓ inherits
FrameworkRouter (framework-specific glue)
```

Your custom router needs to:

1. Inherit from `BaseAdapter`
2. Implement a request data extractor
3. Implement framework response building
4. Register routes with your framework

## Step 1: Create Request Data Extractor

The extractor converts framework requests into FastOpenAPI's `RequestData`:

```python
from typing import Any
from fastopenapi.core.types import FileUpload, RequestData
from fastopenapi.routers.extractors import BaseRequestDataExtractor

class MyFrameworkExtractor(BaseRequestDataExtractor):
    """Extract request data from MyFramework requests"""

    @classmethod
    def _get_path_params(cls, request: Any) -> dict:
        """Extract path parameters from URL"""
        # Example: request.match_info for aiohttp, request.path_params for starlette
        return getattr(request, "path_params", {})

    @classmethod
    def _get_query_params(cls, request: Any) -> dict:
        """Extract query string parameters"""
        query_params = {}
        for key in request.query:
            values = request.query.getall(key)
            query_params[key] = values[0] if len(values) == 1 else values
        return query_params

    @classmethod
    def _get_headers(cls, request: Any) -> dict:
        """Extract HTTP headers"""
        return dict(request.headers)

    @classmethod
    def _get_cookies(cls, request: Any) -> dict:
        """Extract cookies"""
        return dict(request.cookies)

    @classmethod
    def _get_body(cls, request: Any) -> dict | list | None:
        """Extract JSON body"""
        content_type = request.content_type or ""
        if "application/json" in content_type:
            return request.json()
        return {}

    @classmethod
    def _get_form_data(cls, request: Any) -> dict:
        """Extract form data"""
        return dict(request.form) if hasattr(request, "form") else {}

    @classmethod
    def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        """Extract uploaded files"""
        files = {}
        for key, file_obj in request.files.items():
            files[key] = FileUpload(
                filename=file_obj.filename,
                content_type=file_obj.content_type,
                size=file_obj.size,
                file=file_obj.file,
            )
        return files
```

For async frameworks, inherit from `BaseAsyncRequestDataExtractor` instead.

## Step 2: Create the Router

```python
import inspect
from collections.abc import Callable
from fastopenapi.core.types import Response
from fastopenapi.routers.base import BaseAdapter
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.openapi.ui import render_swagger_ui, render_redoc_ui

# Import your framework
from myframework import App, Response as FrameworkResponse


class MyFrameworkRouter(BaseAdapter):
    """Router for MyFramework"""

    # Path conversion pattern: {param} -> framework format
    # Examples:
    #   Flask: (r"{(\w+)}", r"<\1>")      -> /users/<user_id>
    #   Starlette: (r"{(\w+)}", r"{\1}")  -> /users/{user_id}
    PATH_CONVERSIONS = (r"{(\w+)}", r"<\1>")

    # Set the extractor class
    extractor_cls = MyFrameworkExtractor

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Register route with the framework"""
        # First, call parent to store route info
        super().add_route(path, method, endpoint)

        if self.app is not None:
            # Convert path format for framework
            framework_path = self._convert_path_for_framework(path)

            # Create view function wrapper
            def view_func(**path_params):
                # Create request envelope
                env = RequestEnvelope(
                    request=get_current_request(),  # Framework-specific
                    path_params=path_params
                )

                # Check for async endpoint in sync router
                if inspect.iscoroutinefunction(endpoint):
                    raise Exception(
                        f"Async endpoint '{endpoint.__name__}' "
                        f"cannot be used with sync router."
                    )

                # Delegate to BaseAdapter's request handler
                return self.handle_request(endpoint, env)

            # Register with framework
            self.app.add_route(framework_path, view_func, methods=[method])

    def build_framework_response(self, response: Response) -> FrameworkResponse:
        """Convert FastOpenAPI Response to framework response"""
        return FrameworkResponse(
            body=response.content,
            status=response.status_code,
            headers=response.headers,
            content_type="application/json"
        )

    def is_framework_response(self, response) -> bool:
        """Check if response is already a framework response"""
        return isinstance(response, FrameworkResponse)

    def _register_docs_endpoints(self):
        """Register OpenAPI documentation endpoints"""
        app = self.app

        @app.route(self.openapi_url, methods=["GET"])
        def openapi_json():
            return FrameworkResponse(
                body=self.openapi,
                content_type="application/json"
            )

        @app.route(self.docs_url, methods=["GET"])
        def swagger_ui():
            html = render_swagger_ui(self.openapi_url)
            return FrameworkResponse(body=html, content_type="text/html")

        @app.route(self.redoc_url, methods=["GET"])
        def redoc():
            html = render_redoc_ui(self.openapi_url)
            return FrameworkResponse(body=html, content_type="text/html")
```

## Step 3: Async Router (Optional)

For async frameworks:

```python
from fastopenapi.routers.extractors import BaseAsyncRequestDataExtractor


class MyAsyncExtractor(BaseAsyncRequestDataExtractor):
    """Async extractor for MyFramework"""

    @classmethod
    async def _get_body(cls, request) -> dict | list | None:
        """Async body extraction"""
        if request.content_type == "application/json":
            return await request.json()
        return {}

    @classmethod
    async def _get_files(cls, request) -> dict[str, FileUpload | list[FileUpload]]:
        """Async file extraction"""
        files = {}
        async for field in request.multipart():
            if field.filename:
                content = await field.read()
                files[field.name] = FileUpload(
                    filename=field.filename,
                    content_type=field.content_type,
                    size=len(content),
                    file=content,
                )
        return files


class MyAsyncRouter(BaseAdapter):
    """Async router for MyFramework"""

    extractor_async_cls = MyAsyncExtractor

    def add_route(self, path: str, method: str, endpoint: Callable):
        """Register async route"""
        super().add_route(path, method, endpoint)

        if self.app is not None:
            framework_path = self._convert_path_for_framework(path)

            async def view_func(request):
                env = RequestEnvelope(
                    request=request,
                    path_params=request.match_info
                )
                # Use async handler
                return await self.handle_request_async(endpoint, env)

            self.app.router.add_route(method, framework_path, view_func)

    # ... implement other methods
```

## Complete Example: Sync Router

Here's a complete example based on Flask's pattern:

```python
import inspect
from collections.abc import Callable
from typing import Any

from fastopenapi.core.types import FileUpload, Response
from fastopenapi.routers.base import BaseAdapter
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.extractors import BaseRequestDataExtractor
from fastopenapi.openapi.ui import render_swagger_ui, render_redoc_ui

# Framework imports
from myframework import App, Request, Response as MFResponse


class MyFrameworkExtractor(BaseRequestDataExtractor):
    @classmethod
    def _get_path_params(cls, request: Any) -> dict:
        return getattr(request, "path_params", {})

    @classmethod
    def _get_query_params(cls, request: Any) -> dict:
        return dict(request.args)

    @classmethod
    def _get_headers(cls, request: Any) -> dict:
        return dict(request.headers)

    @classmethod
    def _get_cookies(cls, request: Any) -> dict:
        return dict(request.cookies)

    @classmethod
    def _get_body(cls, request: Any) -> dict | list | None:
        if request.is_json:
            return request.json
        return {}

    @classmethod
    def _get_form_data(cls, request: Any) -> dict:
        return dict(request.form)

    @classmethod
    def _get_files(cls, request: Any) -> dict[str, FileUpload | list[FileUpload]]:
        files = {}
        for key, file_obj in request.files.items():
            files[key] = FileUpload(
                filename=file_obj.filename,
                content_type=file_obj.content_type,
                size=None,
                file=file_obj,
            )
        return files


class MyFrameworkRouter(BaseAdapter):
    """Custom router for MyFramework"""

    PATH_CONVERSIONS = (r"{(\w+)}", r"<\1>")
    extractor_cls = MyFrameworkExtractor

    def add_route(self, path: str, method: str, endpoint: Callable):
        super().add_route(path, method, endpoint)

        if self.app is not None:
            framework_path = self._convert_path_for_framework(path)

            def view_func(**path_params):
                from myframework import current_request
                env = RequestEnvelope(
                    request=current_request,
                    path_params=path_params
                )

                if inspect.iscoroutinefunction(endpoint):
                    raise Exception(
                        f"Async endpoint '{endpoint.__name__}' "
                        f"cannot be used with MyFrameworkRouter."
                    )

                return self.handle_request(endpoint, env)

            endpoint_name = f"{endpoint.__name__}:{method}:{framework_path}"
            self.app.add_url_rule(
                framework_path,
                endpoint_name,
                view_func,
                methods=[method]
            )

    def build_framework_response(self, response: Response) -> MFResponse:
        mf_response = MFResponse(response.content)
        mf_response.status_code = response.status_code
        for key, value in response.headers.items():
            mf_response.headers[key] = value
        return mf_response

    def is_framework_response(self, response) -> bool:
        return isinstance(response, MFResponse)

    def _register_docs_endpoints(self):
        @self.app.route(self.openapi_url)
        def openapi_json():
            return MFResponse(self.openapi, mimetype="application/json")

        @self.app.route(self.docs_url)
        def swagger_docs():
            html = render_swagger_ui(self.openapi_url)
            return MFResponse(html, mimetype="text/html")

        @self.app.route(self.redoc_url)
        def redoc_docs():
            html = render_redoc_ui(self.openapi_url)
            return MFResponse(html, mimetype="text/html")
```

## Usage

```python
from myframework import App
from pydantic import BaseModel

app = App()
router = MyFrameworkRouter(
    app=app,
    title="My API",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    price: float

@router.get("/items/{item_id}")
def get_item(item_id: int):
    return {"id": item_id, "name": "Test"}

@router.post("/items", response_model=Item, status_code=201)
def create_item(item: Item):
    return item
```

## Testing Your Router

```python
def test_custom_router():
    app = App()
    router = MyFrameworkRouter(app=app)

    @router.get("/test")
    def test_endpoint():
        return {"status": "ok"}

    client = app.test_client()
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}
```

## Key Classes Reference

### RouteInfo

Container for route information (from `fastopenapi.core.router`):

```python
class RouteInfo:
    path: str         # Route path, e.g., "/users/{user_id}"
    method: str       # HTTP method (GET, POST, etc.)
    endpoint: Callable  # The endpoint function
    meta: dict        # Route metadata (response_model, status_code, tags, etc.)
```

### RequestEnvelope

Wrapper for framework request (from `fastopenapi.routers.common`):

```python
@dataclass(slots=True, frozen=True)
class RequestEnvelope:
    path_params: dict[str, str]  # Path parameters extracted by framework
    request: Any | None          # Framework's request object
```

### Response

FastOpenAPI's response container (from `fastopenapi.core.types`):

```python
class Response:
    content: Any           # Response body
    status_code: int       # HTTP status code
    headers: dict[str, str] # Response headers
```

## Best Practices

1. **Inherit from BaseAdapter** - Don't reinvent the request handling pipeline
2. **Use composition** - Let BaseAdapter handle parameter resolution and validation
3. **Handle async properly** - Use `handle_request_async()` for async endpoints
4. **Convert paths correctly** - Set `PATH_CONVERSIONS` for your framework's format
5. **Test thoroughly** - Test all parameter types, validation, and error handling

## Submitting to FastOpenAPI

If you create a router for a popular framework:

1. Follow the existing router patterns (see `fastopenapi/routers/flask/`)
2. Add comprehensive tests (see `tests/routers/flask/`)
3. Add framework documentation (see `docs/frameworks/`)
4. Submit a pull request

## Next Steps

- [Architecture](architecture.md) - Understand FastOpenAPI internals
- [Testing](testing.md) - Test your custom router
- [OpenAPI Customization](openapi_customization.md) - Customize schema generation
