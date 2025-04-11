from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import pandas as pd
import json

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Load cached ZIP-to-ZIP distances
zip_cache = pd.read_csv("zip_cache.csv")

# Load seasonal pricing model
with open("seasonal_model.json") as f:
    seasonal_data = json.load(f)

@app.get("/", response_class=HTMLResponse)
async def quote_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/quote")
async def get_quote(
    pickup_zip: str,
    dropoff_zip: str,
    month: int,
    enclosed: int = 0,
    inop: int = 0,
    classic: int = 0,
    heavy: int = 0,
    vehicle_count: int = 1
):
    # Find ZIP-to-ZIP match
    match = zip_cache[
        (zip_cache["pickup_zip"] == int(pickup_zip)) &
        (zip_cache["dropoff_zip"] == int(dropoff_zip))
    ]
    if match.empty:
        return JSONResponse({"error": "No ZIP match found"}, status_code=404)

    distance = match.iloc[0]["distance_miles"]

    # Route key format: CA_TX_5
    route_key = f"{pickup_zip[:2]}_{dropoff_zip[:2]}_{month}"
    base_rate = seasonal_data.get(route_key, 0.55)  # fallback rate

    price = distance * base_rate

    if enclosed:
        price += 300
    if inop:
        price += 150
    if classic:
        price += 200
    if heavy:
        price += 100
    if vehicle_count > 1:
        price -= 50 * (vehicle_count - 1)

    return {
        "pickup_zip": pickup_zip,
        "dropoff_zip": dropoff_zip,
        "miles": round(distance),
        "base_rate": round(base_rate, 2),
        "final_price": round(price, 2)
    }
