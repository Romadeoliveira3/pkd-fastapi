import json
from typing import Dict, List, Annotated, Any

import httpx
import asyncio
from fastapi import Depends, FastAPI, HTTPException, Security, Request, APIRouter
from fastapi.security import OAuth2AuthorizationCodeBearer, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer


from jose import jwt, jwk, JWTError
from jose.exceptions import JWTError
from pydantic import BaseModel

from fastcrud.paginated import PaginatedListResponse, compute_offset, paginated_response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

# Configuração do Keycloak
KEYCLOAK_URL = "http://localhost:8080"
REALM_NAME = "PKD-realm"
TOKEN_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/token"
INTROSPECT_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/token/introspect"
RESOURCE_REGISTRATION_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/authz/protection/resource_set"
PERMISSION_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/authz/protection/permission"
POLICY_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/authz/protection/uma-policy"

KEYCLOAK_CLIENT_ID = "confidential-client"
CLIENT_SECRET = "PKD-client-secret"

# FastAPI app
app = FastAPI()

# JWKs URL
JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/certs"

# OAuth2 scheme
# Cache das chaves públicas do Keycloak
jwks_cache = None
jwks_cache_lock = asyncio.Lock()

# OAuth2 scheme
oauth2_scheme = HTTPBearer()

# Modelo de requisição para obter o token
class TokenRequest(BaseModel):
    username: str
    password: str

# Models
class TokenData(BaseModel):
    username: str
    roles: List[str]
    
# Item model
class Item(BaseModel):
    name: str
    description: str
    price: float

# Token validation function
async def validate_token_jws(token: str) -> TokenData:
    try:
        # Fetch JWKS
        async with httpx.AsyncClient() as client:
            response = await client.get(JWKS_URL)
            response.raise_for_status()
            jwks = response.json()

        # Decode the token headers to get the key ID (kid)
        headers = jwt.get_unverified_headers(token)
        kid = headers.get("kid")
        if not kid:
            raise HTTPException(status_code=401, detail="Token missing 'kid' header")

        # Find the correct key in the JWKS
        key_data = next((key for key in jwks["keys"] if key["kid"] == kid), None)
        if not key_data:
            raise HTTPException(status_code=401, detail="Matching key not found in JWKS")

        # Convert JWK to RSA public key
        public_key = jwk.construct(key_data).public_key()

        # Verify the token
        payload = jwt.decode(
            token,
            key=public_key,
            algorithms=["RS256"],
            audience=KEYCLOAK_CLIENT_ID
        )

        # Extract username and roles
        username = payload.get("preferred_username")
        roles = payload.get("realm_access", {}).get("roles", [])
        if not username or not roles:
            raise HTTPException(status_code=401, detail="Token missing required claims")

        return TokenData(username=username, roles=roles)

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

# Dependency to get the current user
async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await validate_token(token)

# Role-Based Access Control (RBAC)
def has_role(required_role: str):
    def role_checker(token_data: TokenData = Depends(get_current_user)) -> TokenData:
        if required_role not in token_data.roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        return token_data
    return role_checker


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

    return TokenData(username=result.get("preferred_username", "unknown"), roles=result.get("realm_access", {}).get("roles", []))


async def validate_token(token: str = Depends(oauth2_scheme)) -> TokenData:
    if not token or not token.credentials:
        raise HTTPException(status_code=401, detail="Missing access token")

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "token": token.credentials,  # Obtém automaticamente o token do cabeçalho Authorization
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

    return TokenData(username=result.get("preferred_username", "unknown"), roles=result.get("realm_access", {}).get("roles", []))


# Routes
@app.get("/public")
async def public_endpoint():
    return {"message": "This is a public endpoint accessible to everyone."}

@app.post("/get-token-Bearer")
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
        
        token_data = response.json()
        
        # Retorna apenas o `Bearer`
        return { "token_type": token_data["token_type"], "id_token": token_data["id_token"],}
    
@app.get("/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    return {"message": "Você acessou um endpoint protegido!"}


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
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")
    
    return await validate_token_introspect(token.credentials)


@app.get("/protected-w-validate")
async def protected_route(current_user: TokenData = Depends(validate_token)):
    return {
        "message": f"Você acessou um endpoint protegido, {current_user.username}!",
        "roles": current_user.roles
    }
