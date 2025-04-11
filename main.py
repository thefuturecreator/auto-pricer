from fastapi.responses import JSONResponse
import pandas as pd
import json

# Load cached data
zip_cache = pd.read_csv("zip_cache.csv")
with open("seasonal_model.json") as f:
    seasonal_data = json.load(f)

app.get("/quote")
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
    # Find the closest matching ZIP pair
    match = zip_cache[
        (zip_cache["pickup_zip"] == int(pickup_zip)) &
        (zip_cache["dropoff_zip"] == int(dropoff_zip))
    ]
    if match.empty:
        return JSONResponse({"error": "No ZIP match found"}, status_code=404)

    distance = match.iloc[0]["distance_miles"]

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

    return {"price": round(price, 2), "miles": round(distance), "rate": round(base_rate, 2)}
