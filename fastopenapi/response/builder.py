from typing import Any

from pydantic import BaseModel

from fastopenapi.core.types import Response


class ResponseBuilder:
    """Build and serialize responses"""

    def build(self, result: Any, meta: dict) -> Response:
        """Build response from endpoint result"""
        # Handle tuple response (body, status, headers)
        if isinstance(result, tuple):
            if len(result) == 2:
                content, status = result
                headers = {}
            elif len(result) == 3:
                content, status, headers = result
            else:
                content = result
                status = meta.get("status_code", 200)
                headers = {}
        # Handle Response object
        elif isinstance(result, Response):
            return result
        # Handle regular response
        else:
            content = result
            status = meta.get("status_code", 200)
            headers = {}

        # Serialize content
        content = self._serialize(content)

        return Response(content=content, status_code=status, headers=headers)

    def _serialize(self, data: Any) -> Any:
        """Serialize response data"""
        if isinstance(data, BaseModel):
            return data.model_dump(by_alias=True)
        if isinstance(data, list) and data and isinstance(data[0], BaseModel):
            return [item.model_dump(by_alias=True) for item in data]
        if isinstance(data, list):
            return [self._serialize(item) for item in data]
        if isinstance(data, dict):
            return {k: self._serialize(v) for k, v in data.items()}
        return data
