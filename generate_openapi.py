from fastapi.openapi.utils import get_openapi
from project.app import app
import json


with open('openapi.json', 'w') as f:
    json.dump(get_openapi(
        title=app.title,
        version=app.version,
        openapi_version="2.0",
        description=app.description,
        routes=app.routes
    ), f)
