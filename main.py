from fastapi import FastAPI,Request,JSONResponse
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
import re,psycopg,os,sys
from psycopg_pool import ConnectionPool
libPath = os.path.join(os.path.dirname(__file__), 'lib')
sys.path.append(libPath)
from config import Config


app = FastAPI(
    title="Vercel + FastAPI",
    description="Vercel + FastAPI",
    version="1.0.0",
)

templates = Jinja2Templates(directory="templates")
cfg = Config()
pool = ConnectionPool("postgresql://neondb_owner:npg_nuc5NPZl0DJA@ep-tiny-waterfall-adb4f3n3-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
app.mount("/javascript", StaticFiles(directory="javascript"), name="javascript")
app.mount("/css", StaticFiles(directory="css"), name="css")

class signup(BaseModel):
    confirmpassword: str
    password: str
    username: str
    email: EmailStr


def getPostgresConnection():
    return pool.connection()

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
async def signup(request: Request):
    return templates.TemplateResponse("signup.html", {
        "request": request, 
        "store_name": "MODERN",  
    })

@app.post("/signup",response_class=HTMLResponse)
async def signuppost(data: Request):
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    confirmpassword = data.get("confirmpassword")

    if confirmpassword != password:
        return JSONResponse({"success": False,"message": "Passwords dont match."})

    if len(password) < 8:
        return JSONResponse({"success": False,"message": "Passwords must be atleast 8 characters long."})

    if len(username) > 20:
        return JSONResponse({"success": False,"message": "Username cannot be over 20 characters."})
    
    if not re.fullmatch(r"^\w{3,20}$", username):
        return JSONResponse({"success": False,"message": "Username can only contain letters, numbers, and underscores (3-20 characters)."})

    print("e")