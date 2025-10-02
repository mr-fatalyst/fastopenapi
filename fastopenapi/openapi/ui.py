from fastopenapi.core.constants import REDOC_URL, SWAGGER_URL


def render_swagger_ui(openapi_json_url: str) -> str:
    """Render Swagger UI HTML"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8">
        <title>Swagger UI</title>
        <link rel="stylesheet" href="{SWAGGER_URL}swagger-ui.css" />
      </head>
      <body>
        <div id="swagger-ui"></div>
        <script src="{SWAGGER_URL}swagger-ui-bundle.js"></script>
        <script>
          SwaggerUIBundle({{
            url: '{openapi_json_url}',
            dom_id: '#swagger-ui'
          }});
        </script>
      </body>
    </html>
    """


def render_redoc_ui(openapi_json_url: str) -> str:
    """Render Redoc UI HTML"""
    return f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body {{
            margin: 0;
            padding: 0;
          }}
        </style>
      </head>
      <body>
        <redoc spec-url='{openapi_json_url}'></redoc>
        <script src="{REDOC_URL}"></script>
      </body>
    </html>
    """
