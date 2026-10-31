from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from services.api.routes.core import router as core_router
from services.api.routes.jobs import router as jobs_router
from services.api.routes.search import router as search_router
from services.api.routes.pursuits import router as pursuits_router
from src.platform.database import Database
from src.platform.workflow.draft_jobs import PersistedJobStore
from src.platform.workflow.errors import WorkflowError


def create_app(database_url: str | None = None) -> FastAPI:
    application = FastAPI(title='TigerExchange v2', version='0.2.0')
    application.state.db = Database(database_url)
    application.state.jobs = PersistedJobStore(application.state.db)

    @application.exception_handler(HTTPException)
    async def http_error(_request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content={
            'error': {'code': 'http_error', 'message': 'Requested route or operation is unavailable', 'retryable': False}})

    @application.exception_handler(WorkflowError)
    async def workflow_error(_request: Request, exc: WorkflowError):
        return JSONResponse(status_code=exc.status, content={
            'error': {'code': exc.code, 'message': exc.message, 'retryable': exc.retryable}})

    @application.exception_handler(RequestValidationError)
    async def invalid_request(_request: Request, _exc: RequestValidationError):
        return JSONResponse(status_code=422, content={
            'error': {'code': 'validation_error', 'message': 'Check the required fields and their values', 'retryable': False}})

    @application.exception_handler(SQLAlchemyError)
    async def database_error(_request: Request, _exc: SQLAlchemyError):
        # Driver exceptions may contain connection credentials or private query parameters.
        return JSONResponse(status_code=503, content={
            'error': {'code': 'database_unavailable', 'message': 'Database operation failed; retry after checking service status', 'retryable': True}})

    @application.middleware('http')
    async def same_origin_writes(request: Request, call_next):
        origin = request.headers.get('origin')
        if origin and request.method not in ('GET', 'HEAD', 'OPTIONS'):
            from urllib.parse import urlsplit
            parsed = urlsplit(origin)
            if parsed.netloc != request.headers.get('host') or parsed.scheme != request.url.scheme:
                return JSONResponse(status_code=403, content={
                    'error': {'code': 'origin_rejected', 'message': 'Use the same origin as this application', 'retryable': False}})
        return await call_next(request)

    @application.get('/healthz')
    async def healthz():
        return {'status': 'ok', 'service': 'tigerexchange-api'}

    application.include_router(core_router)
    application.include_router(jobs_router)
    application.include_router(search_router)
    application.include_router(pursuits_router)
    return application


app = create_app()
