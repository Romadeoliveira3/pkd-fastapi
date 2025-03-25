from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List
import httpx

# === Configuração ===
KEYCLOAK_CLIENT_ID = "confidential-client"
CLIENT_SECRET = "PKD-client-secret"
KEYCLOAK_URL = "http://keycloak:8080"
REALM_NAME = "PKD-realm"
INTROSPECT_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/token/introspect"

oauth2_scheme = HTTPBearer()
app = FastAPI(root_path="/items")

# === Modelos ===
class TokenData(BaseModel):
    username: str
    roles: List[str]

class Item(BaseModel):
    name: str
    description: str
    price: float

# === Validação de Token ===
async def validate_token(token: str = Depends(oauth2_scheme)) -> TokenData:
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "token": token.credentials,
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

# === Rotas ===
@app.get("/items")
async def list_items(current_user: TokenData = Depends(validate_token)):
    return [
        {"name": "Item A", "description": "Primeiro item", "price": 10.5},
        {"name": "Item B", "description": "Segundo item", "price": 20.0}
    ]

@app.post("/items")
async def create_item(item: Item, current_user: TokenData = Depends(validate_token)):
    return {"message": f"Item '{item.name}' criado com sucesso por {current_user.username}."}

@app.get("/public")
async def public_item_access():
    return {"message": "Este é um endpoint público do microserviço de itens."}
