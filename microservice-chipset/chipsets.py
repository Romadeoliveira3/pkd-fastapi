from fastapi import APIRouter, Depends
from auth import validate_token, TokenData

chipsets_router = APIRouter(tags=["Chipsets"])

@chipsets_router.get("/", summary="Listar todos os chipsets")
async def list_chipsets(current_user: TokenData = Depends(validate_token)):
    return [
        {"model": "ESP32", "manufacturer": "Espressif"},
        {"model": "STM32", "manufacturer": "STMicroelectronics"},
        {"model": "ATmega328", "manufacturer": "Microchip"}
    ]

@chipsets_router.get("/public", summary="Endpoint público")
async def public_chipsets():
    return {"message": "Este é um endpoint público do microserviço de chipsets."}

@chipsets_router.get("/private", summary="Endpoint privado")
async def private_chipsets(current_user: TokenData = Depends(validate_token)):
    return {"message": f"Chipsets acessados por: {current_user.sub}"}
