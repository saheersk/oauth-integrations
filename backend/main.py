from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1 import airtable_routes, notion_routes, hubspot_routes


app = FastAPI()

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
@app.get('/')
def read_root():
    return {'Ping': 'Pong'}


# Include the integration routers
app.include_router(airtable_routes.router, prefix="/integrations/airtable", tags=["Airtable"])
app.include_router(notion_routes.router, prefix="/integrations/notion", tags=["Notion"])
app.include_router(hubspot_routes.router, prefix="/integrations/hubspot", tags=["HubSpot"])