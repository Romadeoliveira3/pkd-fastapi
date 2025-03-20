from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import httpx

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str
    price: float

items_db = {}

@app.post("/items")
async def create_item(item: Item):
    if item.name in items_db:
        raise HTTPException(status_code=400, detail="Item already exists")
    items_db[item.name] = item
    return {"message": f"Item '{item.name}' created successfully", "item": item}

@app.get("/items/{item_name}")
async def get_item(item_name: str):
    item = items_db.get(item_name)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
