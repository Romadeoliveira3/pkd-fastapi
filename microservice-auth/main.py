from fastapi import FastAPI, HTTPException, Depends
import httpx
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()

KEYCLOAK_URL = "http://keycloak:8080"
REALM_NAME = "PKD-realm"
TOKEN_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/token"
INTROSPECT_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/token/introspect"

KEYCLOAK_CLIENT_ID = "confidential-client"
CLIENT_SECRET = "PKD-client-secret"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)

async def validate_token(token: str = Depends(oauth2_scheme)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            INTROSPECT_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"token": token, "client_id": KEYCLOAK_CLIENT_ID, "client_secret": CLIENT_SECRET},
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Keycloak introspection failed")

        result = response.json()
        if not result.get("active", False):
            raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"username": result.get("preferred_username"), "roles": result.get("realm_access", {}).get("roles", [])}

@app.get("/validate-token")
async def validate(token_data: dict = Depends(validate_token)):
    return token_data
