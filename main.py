from fastapi import FastAPI,Request,Response,Cookie
from fastapi.responses import HTMLResponse,JSONResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException
import re,os,sys,bcrypt,secrets
libPath = os.path.join(os.path.dirname(__file__), 'lib')
sys.path.append(libPath)
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from psycopg.rows import dict_row
from lib.config import Config
from lib.postgres import getPostgresConnection
from lib.redis import getRedisInstance
from lib.schema import *

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

def trustCheckAdminUser(cursor,SessionId):
    cursor.execute("""
        SELECT locked,username FROM accounts WHERE SessionId = %s;
    """, (SessionId,))

    result = cursor.fetchone()

    if not result:
        return JSONResponse({"success": False, "message": "Unknown username or sessionid."})

    locked = result[0]
    username = result[1]

    if locked:
        return JSONResponse({"success": False, "message": "This admin user is locked."})
    
    if str(username) != cfg.AdminUsername:
        return JSONResponse({"success": False, "message": "Not authorized to do this action."})
    
    return None


@app.get("/", response_class=HTMLResponse)
@limiter.limit("50/minute")
async def root(request: Request):

    with getPostgresConnection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""SELECT * from storeitems""")
            rows = cursor.fetchall()

    items = []

    print(rows)

    for row in rows:
        items.append({
            "name": row['itemname'],    
            "price": row['price'],       
            "image": row['imageurl'],    
            "description": row['description'], 
            "offsale": row['offsale'],
            "desc": ""                   # for now temporary
        })

    onsaleitems = [r for r in items if not r["offsale"]]

    print(items)

    return templates.TemplateResponse("index.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
        "products": onsaleitems
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

@app.get("/admin",response_class=JSONResponse)
@limiter.limit("50/minute")
async def adminload(request: Request,SessionId: str = Cookie(None)):
    SessionIdList = SessionId.split(":")
    SessionId = SessionIdList[0]
    SessionUsername = SessionIdList[1]

    print(SessionIdList)

    if SessionUsername == cfg.AdminUsername:
        return templates.TemplateResponse("admin.html", {
            "request": request, 
            "store_name": cfg.StoreName,  
        })

@app.get("/userloggedin",response_class=JSONResponse)
@limiter.limit("50/minute")
async def userloggedin(request: Request, SessionId: str = Cookie(None)):
    sessionData = None 
    if SessionId:
        sessionData = getRedisInstance().get(str(SessionId))
        SessionIdList = SessionId.split(":")
        SessionId = SessionIdList[0]
        SessionUsername = SessionIdList[1]

        print(SessionIdList)

        if SessionUsername == cfg.AdminUsername:
            return JSONResponse({"loggedin": sessionData,"isadmin":True})

    return JSONResponse({"loggedin": sessionData})

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
                    setSessionCookie(response,sessionId + ":" + username)
                    getRedisInstance().set(sessionId + ":" + username,"1")

                return {"success": True}

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
                    
                    setSessionCookie(response,sessionId + ":" + username)
                    getRedisInstance().set(sessionId + ":" + username,"1")
                else:
                    raise ValueError("Incorrect username or password.")
                
                return {"success": True}

    except ValueError as customError:
        return JSONResponse({"success": False, "message": str(customError)})

    except Exception as e:
      print(e)
      return JSONResponse({"success": False,"message": "Internal Server Error."})
    
@app.post("/logout")
@app.post("/logout/")
@limiter.limit("50/minute")
async def logout(request : Request,response: Response):
    response.delete_cookie(
        key="SessionId",
        path="/",
        httponly=True,
        samesite="lax"
    )
    return {"success": True}

@app.post("/adminapi/newitem")
@limiter.limit("50/minute")
async def additem(request: Request,data: AddItemSchema, SessionId: str = Cookie(None)):
    itemname = data.itemname
    imageurl = data.imageurl
    description = data.description
    price = data.price
# hopefully 2 different admins dont run this at once
    with getPostgresConnection() as conn:
        with conn.cursor() as cursor:
            print(SessionId)
            trustCheck = trustCheckAdminUser(cursor,SessionId)

            if trustCheck:
                return trustCheck
            
            try:
                cursor.execute("""SELECT itemid from storeitems WHERE itemname = %s;""",(itemname,))

                result = cursor.fetchone()

                if result:
                    return JSONResponse({"success": False, "message": "The itemname is already taken by another itemid."})

                cursor.execute("""
                    INSERT INTO storeitems (itemname, imageurl, description, price,offsale)
                    VALUES (%s, %s, %s, %s,%s)
                    ON CONFLICT (itemname) DO NOTHING
                    RETURNING itemid;
                """, (itemname, imageurl, description, price,False))

                newItem = cursor.fetchone()
                conn.commit()

                if not newItem:
                    return JSONResponse({"success": False, "message": "The itemname is already taken by another itemid."})
            except Exception as error:
                conn.rollback()
                return JSONResponse({"success": False, "message": f"Database error: {str(error)}"})

    return {"success": True}


@app.post("/adminapi/changeItem")
@limiter.limit("50/minute")
async def additem(request: Request,data: AddItemSchema, SessionId: str = Cookie(None)):
    itemname = data.itemname
    imageurl = data.imageurl
    description = data.description
    price = data.price

    with getPostgresConnection() as conn:
        with conn.cursor() as cursor:
            trustCheck = trustCheckAdminUser(cursor,SessionId)

            if trustCheck:
                return trustCheck
            
            cursor.execute("""SELECT itemid from storeitems WHERE itemname = %s;""",(itemname,))
            result = cursor.fetchone()

            if not result:
                return JSONResponse({"success": False, "message": "No data found for that itemname."})

            itemid = result[0]

            cursor.execute("""
                UPDATE storeitems 
                SET price = %s, description = %s, imageurl= %s,itemname = %s
                WHERE itemid = %s
            """, (price, description,imageurl, itemname,itemid))

            conn.commit()

    return {"success": True}

@app.post("/adminapi/lockAccount")
@limiter.limit("50/minute")
async def additem(request: Request,data: LockAccountSchema, SessionId: str = Cookie(None)):
    username = data.username
    lockAccount = data.lockaccount

    if lockAccount == "lock":
        lockAccount = True
    elif lockAccount == "unlock":
        lockAccount = False
    else:
        return JSONResponse({"success": False, "message": "This lock account query is not valid."})

    if cfg.AdminUsername == username:
        return JSONResponse({"success": False, "message": "This account cannot be locked."})

    with getPostgresConnection() as conn:
        with conn.cursor() as cursor:
            trustCheck = trustCheckAdminUser(cursor,SessionId)

            if trustCheck:
                return trustCheck
            
            cursor.execute("""
                SELECT locked FROM accounts WHERE username = %s;
            """, (username,))
            
            result = cursor.fetchone()

            if not result:
                return JSONResponse({"success": False, "message": "This username has no data."})

            locked = result[0]

            if locked == lockAccount:
                return JSONResponse({"success": False, "message": "This account's status is the same value to what you are trying to set it to."})

            cursor.execute("""
                UPDATE accounts 
                SET locked = %s
                WHERE username = %s
            """, (lockAccount, username))

            conn.commit()

    return {"success": True}

@app.get("/{path:path}", response_class=HTMLResponse)
@limiter.limit("50/minute")
async def catchall(request: Request, path: str):
    return templates.TemplateResponse("notfound.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
    })