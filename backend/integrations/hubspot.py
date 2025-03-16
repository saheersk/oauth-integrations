# hubspot.py
import asyncio
import base64
import hashlib
import json
import logging
import os
import secrets
from typing import List, Union

import httpx
from backend.db.redis_client import add_key_value_redis, delete_key_redis, get_value_redis
from dotenv import load_dotenv
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse
from integrations.integration_item import IntegrationItem
# from services.rate_limit import is_rate_limited

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("HubSpotIntegration")

load_dotenv()

CLIENT_ID = os.environ.get("HUBSPOT_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("HUBSPOT_CLIENT_SECRET", "")

REDIRECT_URI = "http://localhost:8000/integrations/hubspot/oauth2callback"
authorization_url = "https://app.hubspot.com/oauth/authorize?"


async def authorize_hubspot(user_id, org_id):
    logger.info("Starting authorization process for user_id=%s, org_id=%s", user_id, org_id)
    state_data = {
        "state": secrets.token_urlsafe(32),
        "user_id": user_id,
        "org_id": org_id,
    }
    encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode("utf-8")).decode("utf-8")

    code_verifier = secrets.token_urlsafe(32)
    m = hashlib.sha256()
    m.update(code_verifier.encode("utf-8"))
    code_challenge = base64.urlsafe_b64encode(m.digest()).decode("utf-8").replace("=", "")

    auth_url = (
        f"{authorization_url}"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope=oauth%20automation%20crm.objects.custom.read%20crm.schemas.contacts.read&"
        f"state={encoded_state}&"
        f"code_challenge={code_challenge}&"
        f"code_challenge_method=S256"
    )

    await asyncio.gather(
        add_key_value_redis(
            f"hubspot_state:{org_id}:{user_id}",
            json.dumps(state_data),
            expire=600,
        ),
        add_key_value_redis(f"hubspot_verifier:{org_id}:{user_id}", code_verifier, expire=600),
    )
    logger.info("Stored state and verifier for org_id=%s, user_id=%s", org_id, user_id)
    return auth_url


async def oauth2callback_hubspot(request: Request):
    logger.info("Processing OAuth2 callback.")

    if request.query_params.get("error"):
        error_description = request.query_params.get("error_description")
        logger.error("OAuth2 error: %s", error_description)
        raise HTTPException(status_code=400, detail=error_description)

    code = request.query_params.get("code")
    encoded_state = request.query_params.get("state")
    state_data = json.loads(base64.urlsafe_b64decode(encoded_state).decode("utf-8"))

    original_state = state_data.get("state")
    user_id = state_data.get("user_id")
    org_id = state_data.get("org_id")

    saved_state, code_verifier = await asyncio.gather(
        get_value_redis(f"hubspot_state:{org_id}:{user_id}"),
        get_value_redis(f"hubspot_verifier:{org_id}:{user_id}"),
    )

    if not saved_state or original_state != json.loads(saved_state).get("state"):
        logger.error("State mismatch for org_id=%s, user_id=%s", org_id, user_id)
        raise HTTPException(status_code=400, detail="State does not match.")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.hubapi.com/oauth/v1/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI,
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "code_verifier": code_verifier,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("Failed to exchange code for token: %s", e)
            raise HTTPException(status_code=500, detail="Token exchange failed.")

    response_json = response.json()
    logger.info("Received tokens for user_id=%s, org_id=%s", user_id, org_id)

    await add_key_value_redis(
        f"hubspot_credentials:{org_id}:{user_id}",
        json.dumps(response_json),
        expire=600,
    )

    await asyncio.gather(
        delete_key_redis(f"hubspot_state:{org_id}:{user_id}"),
        delete_key_redis(f"hubspot_verifier:{org_id}:{user_id}"),
    )
    logger.info("Cleared temporary state and verifier for org_id=%s, user_id=%s", org_id, user_id)

    return HTMLResponse(content="<html><script>window.close();</script></html>")


async def get_hubspot_credentials(user_id, org_id):
    logger.info("Fetching credentials for user_id=%s, org_id=%s", user_id, org_id)
    credentials = await get_value_redis(f"hubspot_credentials:{org_id}:{user_id}")
    if not credentials:
        logger.warning("No credentials found for user_id=%s, org_id=%s", user_id, org_id)
        raise HTTPException(status_code=400, detail="No credentials found.")
    return json.loads(credentials)


async def create_integration_item_metadata_object(response_json):
    logger.debug(f"Creating metadata object for response: {response_json}")
    return {
        "id": response_json.get("id"),
        "name": response_json.get("name"),
        "type": response_json.get("type"),
        "properties": response_json.get("properties", {}),
    }


async def get_items_hubspot(credentials: Union[str, dict]) -> List[IntegrationItem]:
    logger.info("Fetching items from HubSpot.")

    if isinstance(credentials, str):
        credentials = json.loads(credentials)
    
    print(credentials, "====credentials====")

    user_id = credentials.get("user_id")
    org_id = credentials.get("org_id")

    if not user_id or not org_id:
        logger.error("Missing user_id or org_id in credentials.")
        raise ValueError("Missing user_id or org_id in credentials")

    # if await is_rate_limited(user_id):
    #     raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    access_token = credentials.get("access_token")
    if not access_token:
        logger.error("Missing access token in credentials.")
        raise ValueError("Missing access token in credentials")

    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://api.hubapi.com/crm/v3/objects/contacts"

    list_of_items = []

    while url:
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                logger.info(f"Fetching data from {url}")
                response = await client.get(url, headers=headers)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    logger.info("Access token expired. Refreshing token.")
                    access_token = await refresh_access_token_hubspot(user_id, org_id)
                    headers["Authorization"] = f"Bearer {access_token}"
                    continue
                logger.error(f"HTTP error fetching HubSpot items: {e}")
                break
            except httpx.RequestError as e:
                logger.error(f"Request error occurred: {e}")
                break

            data = response.json()
            items = data.get("results", [])

            print(items, "==items====")

            for item in items:
                integration_item = IntegrationItem(
                    id=item.get("id"),
                    name=item["properties"].get("firstname", "Unknown"),
                    type="hubspot_contact",
                    properties=item["properties"]
                )
                list_of_items.append(integration_item)

            url = data.get("paging", {}).get("next", {}).get("link", None)

    logger.info(f"Fetched {len(list_of_items)} items from HubSpot.")
    return list_of_items


async def refresh_access_token_hubspot(user_id, org_id):
    logger.info(f"Refreshing access token for user_id={user_id}, org_id={org_id}")
    credentials = await get_value_redis(f"hubspot_credentials:{org_id}:{user_id}")
    logger.debug(f"Credentials from Redis: {credentials}")

    if not credentials:
        logger.error("Credentials not found in Redis.")
        raise HTTPException(status_code=400, detail="No credentials found.")

    credentials = json.loads(credentials)
    refresh_token = credentials.get("refresh_token")
    if not refresh_token:
        logger.error("No refresh token found in credentials.")
        raise HTTPException(status_code=400, detail="No refresh token found.")

    async with httpx.AsyncClient() as client:
        try:
            logger.info("Sending refresh token request to HubSpot.")
            response = await client.post(
                "https://api.hubapi.com/oauth/v1/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            response_json = response.json()
            logger.debug(f"Refresh token response: {response_json}")
        except httpx.RequestError as e:
            logger.error(f"Request error during token refresh: {e}")
            raise HTTPException(status_code=500, detail="Failed to refresh access token.")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error during token refresh: {e}")
            raise HTTPException(status_code=400, detail="Failed to refresh access token.")

    new_access_token = response_json.get("access_token")
    if not new_access_token:
        logger.error("No new access token returned in response.")
        raise HTTPException(status_code=400, detail="Failed to refresh access token.")

    logger.info("Storing new access token in Redis.")
    await add_key_value_redis(
        f"hubspot_credentials:{org_id}:{user_id}",
        json.dumps(response_json),
        expire=600,
    )

    return new_access_token
