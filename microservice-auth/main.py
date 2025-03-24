from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from jose import jwt, jwk
import httpx, asyncio
from typing import List

# === Configuração Keycloak ===
KEYCLOAK_URL = "http://keycloak:8080"
REALM_NAME = "PKD-realm"
TOKEN_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/token"
INTROSPECT_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/token/introspect"
JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/certs"
KEYCLOAK_CLIENT_ID = "confidential-client"
CLIENT_SECRET = "PKD-client-secret"

# === App & Segurança ===
app = FastAPI()
oauth2_scheme = HTTPBearer()
jwks_cache = None
jwks_cache_lock = asyncio.Lock()

# === Models ===
class TokenRequest(BaseModel):
    username: str
    password: str

class TokenData(BaseModel):
    username: str
    roles: List[str]

# === Funções de Validação ===
async def validate_token_introspect(token: str) -> TokenData:
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "token": token,
        "client_id": KEYCLOAK_CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(INTROSPECT_URL, headers=headers, data=data)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Keycloak introspection failed")
        result = response.json()
        if not result.get("active", False):
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    return TokenData(
        username=result.get("preferred_username", "unknown"),
        roles=result.get("realm_access", {}).get("roles", [])
    )

async def validate_token(token: str = Depends(oauth2_scheme)) -> TokenData:
    if not token or not token.credentials:
        raise HTTPException(status_code=401, detail="Missing access token")
    return await validate_token_introspect(token.credentials)

# === Rotas ===
@app.post("/get-token")
async def get_token(request: TokenRequest):
    data = {
        "grant_type": "password",
        "client_id": KEYCLOAK_CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "openid",
        "username": request.username,
        "password": request.password
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(TOKEN_URL, data=data)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

@app.get("/token-validation")
async def test_token(token: str = Depends(oauth2_scheme)):
    return await validate_token_introspect(token.credentials)

@app.get("/protected")
async def protected_route(current_user: TokenData = Depends(validate_token)):
    return {
        "message": f"Acesso concedido ao usuário {current_user.username}",
        "roles": current_user.roles
    }

@app.get("/validate")
async def validate_for_nginx(request: Request):
    auth = request.headers.get("authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = auth.replace("Bearer ", "")
    try:
        await validate_token_introspect(token)
        return {}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail="Invalid token")

@app.get("/public")
async def public_endpoint():
    return {"message": "Este é um endpoint público acessível a todos."}
