"""NSRL Minimal Lookup Server.

The lookup server.
"""

import pkg_resources
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import __version__, crud, models, schema, settings
from .database import setup_engine

# app setup
app = FastAPI(
    title="NSRL Lookup",
    version=str(__version__),
    root_path=settings.server.root_path.rstrip("/"),
    redoc_url=None,
)
app.mount("/static", StaticFiles(directory=pkg_resources.resource_filename(__name__, "static/")), name="static")
templates = Jinja2Templates(directory=pkg_resources.resource_filename(__name__, "templates/"))

# don't try to load on import so we can effectively relfectively load
global SessionLocal


@app.on_event("startup")
def db_setup():
    """Initialise the database.

    This should be lazy loaded on startup to enable the correct reflective loading of the existing database.
    """
    global SessionLocal
    engine, SessionLocal = setup_engine()
    models.Reflected.prepare(engine=engine)


# Dependency
def get_db():
    """Get a connection to the database."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# standard error repsonses
responses = {
    404: {"description": "Item not found"},
    400: {"description": "Bad request"},
}


def _lookup(
    digest: str,
    db: Session,
    details: bool = False,
):
    """Look up a digest in the database."""
    try:
        if not details:
            entity = crud.get_distinct(db, digest=digest)
        else:
            entity = crud.get_details(db, digest=digest)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not entity:
        raise HTTPException(status_code=404, detail="File not in dataset.")
    return entity


@app.get("/exists/{digest}", response_model=schema.DistinctHash, responses={**responses})
def exists(digest: str, db: Session = Depends(get_db)):
    """Return hashes of requested file if it exists in the database."""
    return _lookup(digest=digest, db=db, details=False)


@app.get("/details/{digest}", response_model=list[schema.FileDetails], responses={**responses})
def details(digest: str, db: Session = Depends(get_db)):
    """Return all detailed information about the requested file."""
    return _lookup(digest=digest, db=db, details=True)


@app.post("/", response_class=HTMLResponse, include_in_schema=False)
def results(request: Request, digest: str = Form(), detailed: bool = Form(False), db: Session = Depends(get_db)):
    """Return results from ui query."""
    try:
        result = _lookup(digest=digest, db=db, details=detailed)
    except HTTPException as err:
        return templates.TemplateResponse(
            "index.html", {"request": request, "results": [], "detailed": False, "pkg_stats": None, "err": err}
        )

    # exists query
    if not detailed:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "results": [result], "detailed": False, "pkg_stats": None, "err": None},
        )

    # get details
    results: list[schema.FlatDetails] = []
    packages: dict[str, schema.SummaryPackageVersions] = dict()
    for r in result:
        package = r.package
        # If the package name or application type isn't set we can't get more info
        if not package or not package.name or not package.application_type:
            continue

        if package.name in packages:
            # accumulate unique versions
            packages[package.name].versions.add(package.version)
        else:
            packages[package.name] = schema.SummaryPackageVersions(
                name=package.name.strip(),
                versions=set([package.version.strip()]),
                app_type=package.application_type.strip(),
            )
            # only record details for unique package names, up to max_results limit
            if len(results) < settings.ui.max_results:
                d = schema.FlatDetails(
                    **r.model_dump(exclude="package"),
                    package_name=package.name.strip(),
                    package_app_type=package.application_type.strip(),
                    package_version=package.version.strip(),
                    package_language=package.language.strip(),
                )
                if package.manufacturer:
                    d.package_manufacturer = package.manufacturer.name.strip()
                if package.operating_system:
                    d.operating_system_name = package.operating_system.name.strip()
                    d.operating_system_version = package.operating_system.version.strip()
                    if package.operating_system.manufacturer:
                        d.operating_system_manufacturer = package.operating_system.manufacturer.name.strip()
                results.append(d)

    # summary of packages
    pkg_stats = {
        "uniq_packages": len(packages),
        "num_packages": len(result),
    }

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "results": results, "detailed": detailed, "pkg_stats": pkg_stats, "err": None},
    )


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root(request: Request) -> dict:
    """Main landing page."""
    return templates.TemplateResponse(
        "index.html", {"request": request, "results": [], "detailed": None, "pkg_stats": None, "err": None}
    )


# enable offline access to docs
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(request: Request) -> HTMLResponse:
    """Show the API documentation via Swagger."""
    return get_swagger_ui_html(
        openapi_url=r"{app.root_path}{app.openapi_url}",
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url=f"{app.root_path}/static/js/swagger-ui-bundle.js",
        swagger_css_url=f"{app.root_path}/static/css/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    """Enable offline swagger redirect."""
    return get_swagger_ui_oauth2_redirect_html()
