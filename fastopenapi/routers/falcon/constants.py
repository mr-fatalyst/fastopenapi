from http import HTTPStatus

import falcon

# Mapping HTTP status to Falcon constants
HTTP_STATUS_TO_FALCON = {
    HTTPStatus.OK: falcon.HTTP_200,
    HTTPStatus.CREATED: falcon.HTTP_201,
    HTTPStatus.NO_CONTENT: falcon.HTTP_204,
    HTTPStatus.BAD_REQUEST: falcon.HTTP_400,
    HTTPStatus.UNAUTHORIZED: falcon.HTTP_401,
    HTTPStatus.FORBIDDEN: falcon.HTTP_403,
    HTTPStatus.NOT_FOUND: falcon.HTTP_404,
    HTTPStatus.UNPROCESSABLE_ENTITY: falcon.HTTP_422,
    HTTPStatus.INTERNAL_SERVER_ERROR: falcon.HTTP_500,
}

# Method mapping
METHODS_MAPPER = {
    "GET": "on_get",
    "POST": "on_post",
    "PUT": "on_put",
    "PATCH": "on_patch",
    "DELETE": "on_delete",
    "HEAD": "on_head",
    "OPTIONS": "on_options",
}
