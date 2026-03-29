from fastapi import FastAPI,Request,Response,Cookie
from fastapi.responses import HTMLResponse,JSONResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import re,os,sys,bcrypt,secrets,resend
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
redis = getRedisInstance()
resend.api_key = cfg.ResendAPIKey

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

def checkUserEmailLimit(Username):
    rediskey = Username
    emailCount = redis.get(rediskey)

    if emailCount is None:
        redis.set(rediskey,1,ex=cfg.EMAILWindow)
        return True
    
    emailCount = int(emailCount)

    if emailCount >= cfg.EMAILLimit:
        return False

    redis.incr(rediskey)
    return True

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

def sendEmail(sender,reciever,subject,html):
    try:
        resend.Emails.send({
            "from": sender,
            "to": reciever,
            "subject": subject,
            "html": html
        })
        return {"success": True}
    except resend.exceptions.ResendError as e:
        return JSONResponse({"success": False, "message": str(e)})
    except Exception as error:
        return JSONResponse({"success": False, "message": str(error)})

@app.get("/", response_class=HTMLResponse)
@limiter.limit("50/minute")
async def root(request: Request):

    with getPostgresConnection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""SELECT * from storeitems""")
            rows = cursor.fetchall()

    items = []

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


@app.get("/settings",response_class=HTMLResponse)
@limiter.limit("50/minute")
async def login(request: Request):
    return templates.TemplateResponse("settings.html", {
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

    if not SessionId:
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "store_name": cfg.StoreName,  
        })
    
    SessionIdList = SessionId.split(":")
    SessionId = SessionIdList[0]
    SessionUsername = SessionIdList[1]

    if SessionUsername == cfg.AdminUsername:
        return templates.TemplateResponse("admin.html", {
            "request": request, 
            "store_name": cfg.StoreName,  
        })
    else:
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "store_name": cfg.StoreName,  
        })

@app.get("/userloggedin",response_class=JSONResponse)
@limiter.limit("50/minute")
async def userloggedin(request: Request, SessionId: str = Cookie(None)):
    sessionData = None 
    if SessionId:
        sessionData = redis.get(SessionId)
        SessionIdList = SessionId.split(":")
        SessionId = SessionIdList[0]
        SessionUsername = SessionIdList[1]

        if SessionUsername == cfg.AdminUsername:
            return JSONResponse({"loggedin": sessionData,"isadmin":True})

    return JSONResponse({"loggedin": sessionData})

@app.get("/adminapi/getPendingOrders")
@limiter.limit("50/minute")
async def pendingorders(request: Request, SessionId: str = Cookie(None)):
    if SessionId:
        SessionIdList = SessionId.split(":")
        SessionId = SessionIdList[0]
        SessionUsername = SessionIdList[1]
        if SessionUsername != cfg.AdminUsername:
            return JSONResponse({"success": False,"message": "Not authorized to do this action."})
    else:
        return JSONResponse({"success": False,"message": "Not authorized to do this action."})
    
    with getPostgresConnection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                SELECT id, username, items, total 
                FROM orders 
                WHERE delivered = False
            """)

            rows = cursor.fetchall()

            rows = {
                "success": True,
                "orders": [
                    {
                    "id": 101,
                    "username": "Builderman_99",
                    "items": "1x Dominus Empyreus, 2x Dr. Elephant",
                    "total": "$2000.00"
                    },
                    {
                    "id": 102,
                    "username": "Player1",
                    "items": "1x Classic Hoodie",
                    "total": "$50.00"
                    }
                ]
            }

            if rows:
                return rows

            return {
                "success": True, 
                "orders": rows
            }

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
    csrfToken = secrets.token_urlsafe(16)

    try:
        with getPostgresConnection() as conn:
            with conn.cursor() as cursor:

                cursor.execute("""
                    INSERT INTO accounts (username, email, password, sessionid,locked,orderemails)
                    VALUES (%s, %s, %s, %s,%s,%s)
                    ON CONFLICT (username) DO NOTHING
                    RETURNING userid;
                """, (username, email, hashedpassword, sessionId,False,True))

                rowFetch = cursor.fetchone()

                if not rowFetch:
                    raise ValueError("This username is already in use.")
                else:
                    conn.commit()
                    setSessionCookie(response,sessionId + ":" + username)
                    redis.set(sessionId + ":" + username,csrfToken)

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
    offsale = data.offsale
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
                """, (itemname, imageurl, description, price,offsale))

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
    offsale = data.offsale

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
                SET price = %s, description = %s, imageurl= %s,itemname = %s,offsale = %s
                WHERE itemid = %s
            """, (price, description,imageurl, itemname,offsale,itemid))

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


@app.post("/api/changePassword")
@limiter.limit("50/minute")
async def changepw(request: Request,data: ChangePasswordSchema, response: Response, SessionId: str = Cookie(None)):
    currentpassword = data.currentpassword
    newpassword = data.newpassword

    if len(newpassword) < 8:
        return JSONResponse({"success": False,"message": "Passwords must be atleast 8 characters long."})
    
    if not SessionId:
        return JSONResponse({"success": False,"message": "This session is invalid."})

    with getPostgresConnection() as conn:
        with conn.cursor() as cursor:
            try:
                SessionIdList = SessionId.split(":")
                SessionId = SessionIdList[0]
                SessionUsername = SessionIdList[1]
                
                cursor.execute("""
                    SELECT locked, password 
                    FROM accounts 
                    WHERE username = %s
                    FOR UPDATE
                """, (SessionUsername,))
                
                result = cursor.fetchone()

                if not result:
                    return JSONResponse({"success": False, "message": "This session is invalid."})

                locked = result[0]
                passwordHash = result[1]

                if locked:
                    return JSONResponse({"success": False, "message": "This account is locked."})
                
                if not bcrypt.checkpw(currentpassword.encode("utf-8"),passwordHash.encode("utf-8")):
                    return JSONResponse({"success": False, "message": "Incorrect password."})
                
                if bcrypt.checkpw(newpassword.encode("utf-8"),passwordHash.encode("utf-8")):
                    return JSONResponse({"success": False, "message": "The new password, can't be the same as the old one."})

                newPasswordHash = bcrypt.hashpw(newpassword.encode("utf-8"),bcrypt.gensalt(12)).decode("utf-8")
                sessionId = secrets.token_urlsafe(32)
                csrfToken = secrets.token_urlsafe(16)
                sessionIdToken = sessionId + ":" + SessionUsername

                cursor.execute("""
                    UPDATE accounts 
                    SET password = %s, sessionid = %s
                    WHERE username = %s
                """, (newPasswordHash, sessionIdToken, SessionUsername))

                setSessionCookie(response,sessionId + ":" + SessionUsername)
                redis.set(sessionIdToken,csrfToken)
                conn.commit()
            except Exception as error:
                conn.rollback()
                return JSONResponse({"success": False, "message": "Internal Server Error."})

    return {"success": True}


@app.post("/api/ChangeOrderEmail")
@limiter.limit("50/minute")
async def changeorderemail(request: Request,data: EnableOrderEmailsSchema, response: Response, SessionId: str = Cookie(None)):
    enable = data.enable

    if not isinstance(enable, bool):
        return JSONResponse({"success": False, "message": "This change email order query is not valid."})

    with getPostgresConnection() as conn:
        with conn.cursor() as cursor:
            SessionIdList = SessionId.split(":")
            SessionId = SessionIdList[0]
            SessionUsername = SessionIdList[1]
                                    
            cursor.execute("""
                UPDATE accounts
                SET orderemails = %s
                WHERE username = %s AND sessionid = %s
                RETURNING orderemails;
            """, (enable, SessionUsername, SessionId))

            result = cursor.fetchone()

            if not result:
                return JSONResponse({"success": False, "message": "Invalid session or account not found."})

            conn.commit()

    return {"success": True}

@app.post("/api/ChangeAccountEmail")
@limiter.limit("50/minute")
async def changeaccountemail(request: Request,data: ChangeAccountEmailSchema, response: Response, SessionId: str = Cookie(None)):
    newEmail = data.email

    if not SessionId:
        return JSONResponse({"success": False,"message": "This session is invalid."})

    SessionIdList = SessionId.split(":")
    SessionId = SessionIdList[0]
    SessionUsername = SessionIdList[1]

    if not checkUserEmailLimit(SessionUsername):
        return JSONResponse({"success": False,"message": "Email sending limit reached. Try again later."})

    with getPostgresConnection() as conn:
        with conn.cursor() as cursor:
            EmailVerificationCode = secrets.token_urlsafe(10)
            cursor.execute("""
                UPDATE accounts
                SET pendingnewemail = %s, emailcode = %s, emailcodetime = NOW()
                WHERE username = %s AND sessionid = %s
            """, (newEmail, EmailVerificationCode, SessionUsername, SessionId))

            if cursor.rowcount == 0:
                return JSONResponse({"success": False, "message": "Invalid session or account not found."})
            
            HtmlContent = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #f7f7f7; padding: 20px;">
                <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; padding: 30px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #333;">Email Verification</h2>
                <p style="font-size: 16px; color: #555;">Use the code below to verify your email address:</p>
                <div style="margin: 20px 0;">
                    <span style="font-size: 24px; font-weight: bold; color: #1a73e8; background-color: #e8f0fe; padding: 10px 20px; border-radius: 6px;">{EmailVerificationCode}</span>
                </div>
                <p style="font-size: 14px; color: #555;">This verification code will expire in 15 minutes.</p>
                <p style="font-size: 14px; color: #888;">If you did not request this verification, you can ignore this email.</p>
                <p style="font-size: 14px; color: #888;">&copy; {datetime.now().year} {cfg.StoreName}</p>
                </div>
            </body>
            </html>
            """

            sendEmail("Email Verification <verification@syntaxrevival.store>",newEmail,"Email Verification",HtmlContent)
            conn.commit()   

    return {"success": True}


@app.post("/api/VerifyEmail")
@limiter.limit("50/minute")
async def verifyemail(request: Request,data: EnableOrderEmailsSchema, response: Response, SessionId: str = Cookie(None)):
    VerificationCode = data.code

    if not SessionId:
        return JSONResponse({"success": False,"message": "This session is invalid."})

    SessionIdList = SessionId.split(":")
    SessionId = SessionIdList[0]
    SessionUsername = SessionIdList[1]

    with getPostgresConnection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE accounts
                SET email = pendingnewemail,
                    pendingnewemail = NULL,
                    emailcode = NULL,
                    emailcodetime = NULL
                WHERE username = %s
                AND sessionid = %s
                AND emailcode = %s
                AND pendingnewemail IS NOT NULL
                AND emailcodetime > NOW() - INTERVAL '15 minutes'
            """, (SessionUsername, SessionId, VerificationCode))


            if cursor.rowcount == 0:
                return JSONResponse({"success": False, "message": "Invalid or expired verification code."})

            conn.commit()

    return {"success": True}

@app.get("/{path:path}", response_class=HTMLResponse)
@limiter.limit("50/minute")
async def catchall(request: Request, path: str):
    return templates.TemplateResponse("notfound.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
    })