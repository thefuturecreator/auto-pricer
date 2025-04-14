from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import pandas as pd
import json

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Load ZIP cache and seasonal model
zip_cache = pd.read_csv("zip_cache.csv", dtype={"pickup_zip": str, "dropoff_zip": str})
zip_cache["pickup_zip"] = zip_cache["pickup_zip"].str.zfill(5)
zip_cache["dropoff_zip"] = zip_cache["dropoff_zip"].str.zfill(5)

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
    pickup_zip = pickup_zip.zfill(5)
    dropoff_zip = dropoff_zip.zfill(5)

    # Match ZIP distance
    match = zip_cache[
        (zip_cache["pickup_zip"] == pickup_zip) &
        (zip_cache["dropoff_zip"] == dropoff_zip)
    ]
    if match.empty:
        return JSONResponse({"error": "No ZIP match found"}, status_code=404)

    distance = match.iloc[0]["distance_miles"]

    # Use real directional seasonal data
    route_key = f"{pickup_zip[:2]}_{dropoff_zip[:2]}_{month}"
    reverse_key = f"{dropoff_zip[:2]}_{pickup_zip[:2]}_{month}"

    if route_key in seasonal_data:
        base_rate = seasonal_data[route_key]
    elif reverse_key in seasonal_data:
        base_rate = round(seasonal_data[reverse_key] + 0.1, 3)  # upcharge for reverse route
    else:
        base_rate = 0.55  # fallback rate

    price = distance * base_rate

    # Apply modifiers
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
        "base_rate": base_rate,
        "final_price": round(price, 2)
    }
