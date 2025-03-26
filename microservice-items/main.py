from fastapi import FastAPI, Depends
from pydantic import BaseModel
from auth import validate_token, TokenData

app = FastAPI(
    root_path="/items",
    title="Item Microservice",
    version="1.0.0",
    description="API para gerenciamento de itens do sistema."
)

class Item(BaseModel):
    name: str
    description: str
    price: float

@app.get("/", summary="List Items", tags=["Items"])
async def list_items(current_user: TokenData = Depends(validate_token)):
    return [
        {"name": "Item A", "description": "Primeiro item", "price": 10.5},
        {"name": "Item B", "description": "Segundo item", "price": 20.0}
    ]

@app.post("/", summary="Create Item", tags=["Items"])
async def create_item(item: Item, current_user: TokenData = Depends(validate_token)):
    return {"message": f"Item '{item.name}' criado com sucesso por {current_user.username}."}

@app.get("/public", summary="Public Endpoint", tags=["Public"])
async def public_item_access():
    return {"message": "Este é um endpoint público do microserviço de itens."}
