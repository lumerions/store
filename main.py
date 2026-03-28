from fastapi import FastAPI,Request,Response,Cookie
from fastapi.responses import HTMLResponse,JSONResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, EmailStr
import re,os,sys,bcrypt,secrets
libPath = os.path.join(os.path.dirname(__file__), 'lib')
sys.path.append(libPath)
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from lib.config import Config
from lib.postgres import getPostgresConnection
from lib.redis import getRedisInstance

templates = Jinja2Templates(directory="templates")
cfg = Config()

app = FastAPI(
    title=cfg.StoreName,
    description=cfg.StoreName,
    version="1.0.0",
)

app.mount("/javascript", StaticFiles(directory="javascript"), name="javascript")
app.mount("/css", StaticFiles(directory="css"), name="css")

def LimiterFunction(request : Request):
    print(request.client.host)
    return request.client.host

limiter = Limiter(key_func=LimiterFunction)
app.add_middleware(SlowAPIMiddleware)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def ratelimited(request : Request,exc: RateLimitExceeded):
    return RedirectResponse(url="/ratelimited")

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
@limiter.limit("50/minute")
async def root(request: Request):
    products = [
        {"name": "Dont Tread On Me", "price": "$120.00", "desc": "Limited Edition","image":"https://patriotallianceusa.com/cdn/shop/files/DTOM_2.jpg?v=1762466745&width=700"},
        {"name": "Your Design Here", "price": "$120.00", "desc": "Limited Edition","image":"data:image/jpeg;base64,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"},
    ]
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
        "products": products
    })

@app.get("/ratelimited",response_class=HTMLResponse)
@limiter.limit("50/minute")
async def login(request: Request):
    return templates.TemplateResponse("ratelimited.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
    })

@app.get("/notfound",response_class=HTMLResponse)
@limiter.limit("50/minute")
async def login(request: Request):
    return templates.TemplateResponse("notfound.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
    })

@app.get("/internalerror",response_class=HTMLResponse)
@limiter.limit("50/minute")
async def login(request: Request):
    return templates.TemplateResponse("internalerror.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
    })

@app.get("/signup",response_class=HTMLResponse)
@limiter.limit("50/minute")
async def signup(request: Request):
    return templates.TemplateResponse("signup.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
    })

@app.get("/login",response_class=HTMLResponse)
@limiter.limit("50/minute")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
    })

@app.get("/userloggedin",response_class=JSONResponse)
@limiter.limit("50/minute")
async def userloggedin(request: Request,SessionId: str = Cookie(None)):
    sessionData =  getRedisInstance().get(SessionId)
    print(sessionData)
    return JSONResponse({"loggedin": True})

@app.post("/signup",response_class=JSONResponse)
@limiter.limit("50/minute")
async def signuppost(request: Request,data: SignupSchema, response: Response):
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
                    getRedisInstance().set(sessionId,"1")

                return JSONResponse({"success": True})

    except ValueError as customError:
        return JSONResponse({"success": False, "message": str(customError)})

    except Exception as e:
      print(e)
      return JSONResponse({"success": False,"message": "Internal Server Error."})


@app.post("/login",response_class=JSONResponse)
@limiter.limit("50/minute")
async def loginpost(request : Request,data : LoginSchema, response: Response):
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
                    getRedisInstance().set(sessionId,"1")
                else:
                    raise ValueError("Incorrect username or password.")
                
                return JSONResponse({"success": True})

    except ValueError as customError:
        return JSONResponse({"success": False, "message": str(customError)})

    except Exception as e:
      print(e)
      return JSONResponse({"success": False,"message": "Internal Server Error."})
    
@app.get("/{path:path}", response_class=HTMLResponse)
@limiter.limit("50/minute")
async def catch_all(request: Request, path: str):
    return templates.TemplateResponse("notfound.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
    })