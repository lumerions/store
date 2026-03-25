from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Vercel + FastAPI",
    description="Vercel + FastAPI",
    version="1.0.0",
)

templates = Jinja2Templates(directory="templates")
app.mount("/javascript", StaticFiles(directory="javascript"), name="javascript")
app.mount("/css", StaticFiles(directory="css"), name="css")

@app.get("/api/data")
def get_sample_data():
    return {
        "data": [
            {"id": 1, "name": "Sample Item 1", "value": 100},
            {"id": 2, "name": "Sample Item 2", "value": 200},
            {"id": 3, "name": "Sample Item 3", "value": 300}
        ],
        "total": 3,
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.get("/api/items/{item_id}")
def get_item(item_id: int):
    return {
        "item": {
            "id": item_id,
            "name": "Sample Item " + str(item_id),
            "value": item_id * 100
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    products = [
        {"name": "Premium Product", "price": "$120.00", "desc": "Limited Edition"},
        {"name": "Everyday Essential", "price": "$45.00", "desc": "Best Seller"},
        {"name": "The Collector's Item", "price": "$250.00", "desc": "New Arrival"},
        {"name": "Starter Pack", "price": "$80.00", "desc": "Great Value"},
    ]
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "store_name": "MODERN",  
        "products": products
    })

@app.get("/login",response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request, 
        "store_name": "MODERN",  
    })

@app.get("/signup",response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("signup.html", {
        "request": request, 
        "store_name": "MODERN",  
    })