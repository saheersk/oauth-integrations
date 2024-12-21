# hubspot.py
import asyncio
import base64
import hashlib
import json
import os
import secrets

import httpx
from db.redis_client import add_key_value_redis, delete_key_redis, get_value_redis
from dotenv import load_dotenv
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

load_dotenv()

CLIENT_ID = os.environ.get("HUBSPOT_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("HUBSPOT_CLIENT_SECRET", "")

REDIRECT_URI = "http://localhost:8000/integrations/hubspot/oauth2callback"
authorization_url = f"https://app.hubspot.com/oauth/authorize?"


async def authorize_hubspot(user_id, org_id):
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

    # Updated with all required HubSpot scopes
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
    print(f"Stored state and verifier for org_id: {org_id}, user_id: {user_id}")

    return auth_url


async def oauth2callback_hubspot(request: Request):
    if request.query_params.get("error"):
        raise HTTPException(
            status_code=400,
            detail=request.query_params.get("error_description"),
        )

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
        raise HTTPException(status_code=400, detail="State does not match.")

    async with httpx.AsyncClient() as client:
        response, _, _ = await asyncio.gather(
            client.post(
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
            ),
            delete_key_redis(f"hubspot_state:{org_id}:{user_id}"),
            delete_key_redis(f"hubspot_verifier:{org_id}:{user_id}"),
        )

    await add_key_value_redis(
        f"hubspot_credentials:{org_id}:{user_id}",
        json.dumps(response.json()),
        expire=600,
    )

    return HTMLResponse(content="<html><script>window.close();</script></html>")


async def get_hubspot_credentials(user_id, org_id):
    print(org_id, user_id, "================cred==============")
    credentials = await get_value_redis(f"hubspot_credentials:{org_id}:{user_id}")
    if not credentials:
        raise HTTPException(status_code=400, detail="No credentials found.")
    credentials = json.loads(credentials)
    await delete_key_redis(f"hubspot_credentials:{org_id}:{user_id}")
    return credentials


async def create_integration_item_metadata_object(response_json):
    return {
        "id": response_json.get("id"),
        "name": response_json.get("name"),
        "type": response_json.get("type"),
        "properties": response_json.get("properties", {}),
    }


async def get_items_hubspot(credentials):
    if isinstance(credentials, str):
        credentials = json.loads(credentials)

    access_token = credentials.get("access_token")
    if not access_token:
        raise ValueError("No access token found in credentials")

    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://api.hubapi.com/crm/v3/objects/contacts"

    list_of_items = []

    while url:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()  # Raises HTTPError for bad responses (4xx, 5xx)
            except httpx.HTTPStatusError as e:
                # Handle different status codes
                print(f"HTTP error occurred: {e}")
                break
            except httpx.RequestError as e:
                # Handle request-level errors (e.g., network issues)
                print(f"Request error occurred: {e}")
                break
            except Exception as e:
                # Handle any other exceptions
                print(f"An error occurred: {e}")
                break

            # Parse the JSON response
            try:
                data = response.json()
            except ValueError as e:
                print(f"Error parsing JSON: {e}")
                break

            # Process the results
            for item in data.get("results", []):
                list_of_items.append(await create_integration_item_metadata_object(item))

            # Check for pagination and continue if more pages are available
            url = data.get("paging", {}).get("next", {}).get("link", None)

    return list_of_items
