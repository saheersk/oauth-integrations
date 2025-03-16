from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from api.v1 import airtable_routes, hubspot_routes, notion_routes

app = FastAPI(
    title="Integration API",
    description="API to integrate with Airtable, Notion, and HubSpot.",
    version="1.0.0",
    contact={
        "name": "Your Name",
        "email": "your.email@example.com",
    },
    license_info={
        "name": "MIT License",
    },
)

origins = [
    "http://localhost:3000",  # React app address
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
def read_root():
    return {"Ping": "Pong"}


PREFIX = '/integrations'

# Include the integration routers
app.include_router(airtable_routes.router, prefix=f"{PREFIX}/airtable",
                   tags=["Airtable"])
app.include_router(notion_routes.router, prefix=f"{PREFIX}/notion",
                   tags=["Notion"])
app.include_router(hubspot_routes.router, prefix=f"{PREFIX}/hubspot",
                   tags=["HubSpot"])


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Integration API",
        version="1.0.0",
        description="This is the API for integrating Airtable, Notion, and HubSpot.",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
