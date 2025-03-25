from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer
from typing import List
from pydantic import BaseModel
import httpx

# ⚠️ Importante para funcionar corretamente via Nginx
app = FastAPI(root_path="/chipsets")

oauth2_scheme = HTTPBearer()

# Configuração para introspecção com Keycloak
KEYCLOAK_URL = "http://keycloak:8080"
REALM_NAME = "PKD-realm"
INTROSPECT_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/token/introspect"
CLIENT_ID = "confidential-client"
CLIENT_SECRET = "PKD-client-secret"

class TokenData(BaseModel):
    username: str
    roles: List[str]

class Chipset(BaseModel):
    model: str
    manufacturer: str

async def validate_token(token = Depends(oauth2_scheme)) -> TokenData:
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "token": token.credentials,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(INTROSPECT_URL, headers=headers, data=data)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Keycloak introspection failed")
        result = response.json()
        if not result.get("active"):
            raise HTTPException(status_code=401, detail="Invalid token")
    return TokenData(
        username=result.get("preferred_username", "unknown"),
        roles=result.get("realm_access", {}).get("roles", [])
    )

@app.get("/chipsets")
async def list_chipsets(current_user: TokenData = Depends(validate_token)):
    return [
        {"model": "ESP32", "manufacturer": "Espressif"},
        {"model": "STM32", "manufacturer": "STMicroelectronics"},
        {"model": "ATmega328", "manufacturer": "Microchip"}
    ]

@app.get("/public")
async def public_info():
    return {"message": "Este é um endpoint público do microserviço de chipsets."}
