from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware

from app.core import config, tasks

from app.api.errors.http_eror import http_error_handler
from app.api.errors.validation_error import http422_error_handler
from app.api.routes import router as api_router


def get_application():
    app = FastAPI(title=config.PROJECT_NAME, version=config.VERSION)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_event_handler("startup", tasks.create_start_app_handler(app))
    app.add_event_handler("startup", tasks.create_daily_cleanup_handler(app))
    app.add_event_handler("shutdown", tasks.create_stop_app_handler(app))

    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, http422_error_handler)

    app.include_router(api_router, prefix=config.API_PREFIX)

    return app


app = get_application()
