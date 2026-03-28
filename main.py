from fastapi import FastAPI,Request,Response,Cookie
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
import re,os,sys,bcrypt,secrets
libPath = os.path.join(os.path.dirname(__file__), 'lib')
sys.path.append(libPath)
from lib.config import Config
from lib.postgres import getPostgresConnection
from lib.redis import getRedisInstance

app = FastAPI(
    title="Vercel + FastAPI",
    description="Vercel + FastAPI",
    version="1.0.0",
)


templates = Jinja2Templates(directory="templates")
cfg = Config()
app.mount("/javascript", StaticFiles(directory="javascript"), name="javascript")
app.mount("/css", StaticFiles(directory="css"), name="css")

def setSessionCookie(response : Response,SessionId):
    response.set_cookie(
        key="SessionId", 
        value=SessionId, 
        max_age=34560000,  
        httponly=True,  
        secure=True,  
        samesite="Lax", 
    )

class SignupSchema(BaseModel):
    confirmpassword: str
    password: str
    username: str
    email: EmailStr

class LoginSchema(BaseModel):
    username: str
    password: str

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
        "store_name": cfg.StoreName,  
        "products": products
    })

@app.get("/ratelimited",response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("ratelimited.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
    })

@app.get("/notfound",response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("notfound.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
    })

@app.get("/signup",response_class=HTMLResponse)
async def signup(request: Request):
    return templates.TemplateResponse("signup.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
    })

@app.get("/login",response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
    })

@app.get("/userloggedin",response_class=JSONResponse)
async def userloggedin(request: Request,SessionId: str = Cookie(None)):
    return JSONResponse({"loggedin":getRedisInstance().get(SessionId)})

@app.post("/signup",response_class=JSONResponse)
async def signuppost(data: SignupSchema, response: Response):
    username = data.username
    email = data.email
    password = data.password
    confirmpassword = data.confirmpassword

    if confirmpassword != password:
        return JSONResponse({"success": False,"message": "Passwords dont match."})

    if len(password) < 8:
        return JSONResponse({"success": False,"message": "Passwords must be atleast 8 characters long."})

    if len(username) > 20:
        return JSONResponse({"success": False,"message": "Username cannot be over 20 characters."})
    
    if not re.fullmatch(r"^\w{3,20}$", username):
        return JSONResponse({"success": False,"message": "Username can only contain letters, numbers, and underscores (3-20 characters)."})
    
    hashedpassword = bcrypt.hashpw(password.encode("utf-8"),bcrypt.gensalt(12)).decode("utf-8")
    sessionId = secrets.token_urlsafe(32)

    try:
        with getPostgresConnection() as conn:
            with conn.cursor() as cursor:

                cursor.execute("""
                    INSERT INTO accounts (username, email, password, sessionid,locked)
                    VALUES (%s, %s, %s, %s,%s)
                    ON CONFLICT (username) DO NOTHING
                    RETURNING userid;
                """, (username, email, hashedpassword, sessionId,False))

                rowFetch = cursor.fetchone()

                if not rowFetch:
                    raise ValueError("This username is already in use.")
                else:
                    conn.commit()
                    setSessionCookie(response,sessionId)
                    getRedisInstance.set(sessionId,"1")

                return JSONResponse({"success": True})

    except ValueError as customError:
        return JSONResponse({"success": False, "message": str(customError)})

    except Exception as e:
      print(e)
      return JSONResponse({"success": False,"message": "Internal Server Error."})


@app.post("/login",response_class=JSONResponse)
async def loginpost(data : LoginSchema, response: Response):
    print(data)

    username = data.username
    password = data.password

    try:
        with getPostgresConnection() as conn:
            with conn.cursor() as cursor:

                cursor.execute("""
                    SELECT locked, password,sessionid FROM accounts WHERE username = %s;
                """, (username,))

                result = cursor.fetchone()


                if result:
                    locked = result[0]
                    passwordHashed = result[1]
                    sessionId = result[2]

                    if locked:
                        raise ValueError("This account has been locked.")
                    
                    if not bcrypt.checkpw(password.encode("utf-8"),passwordHashed.encode("utf-8")):
                        raise ValueError("Incorrect username or password.")
                    
                    setSessionCookie(response,sessionId)
                    getRedisInstance.set(sessionId,"1")
                else:
                    raise ValueError("Incorrect username or password.")
                
                return JSONResponse({"success": True})

    except ValueError as customError:
        return JSONResponse({"success": False, "message": str(customError)})

    except Exception as e:
      print(e)
      return JSONResponse({"success": False,"message": "Internal Server Error."})