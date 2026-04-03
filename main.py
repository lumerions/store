from fastapi import FastAPI,Request,Response,Cookie
from fastapi.responses import HTMLResponse,JSONResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import re,os,sys,bcrypt,secrets,resend,json,requests
libPath = os.path.join(os.path.dirname(__file__), 'lib')
sys.path.append(libPath)
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from psycopg.rows import dict_row
from lib.config import Config
from lib.postgres import getPostgresConnection
from lib.redisclient import getRedisInstance
from lib.schema import *
from lib.functions import *


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


@app.get("/", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def root(request: Request, SessionId: str = Cookie(None)):

    CachedStoreData = redis.get("storedata")
    SessionData = userIsLoggedIn(SessionId)

    if CachedStoreData is None:
        with getPostgresConnection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute("""SELECT * from storeitems""")
                rows = cursor.fetchall()
    else: 
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "store_name": cfg.StoreName,  
            "products": json.loads(CachedStoreData),
            "sessiondata": SessionData
        })

    items = []
    onsaleitems = []

    for row in rows:
        itemdata = ({
            "id": row['itemid'],
            "name": row['itemname'],    
            "price": row['price'],       
            "image": row['imageurl'],    
            "description": row['description'], 
            "offsale": row['offsale'],
            "desc": ""                   # for now temporary
        })

        items.append(itemdata)

        if not row["offsale"]:
            onsaleitems.append(itemdata)

    redis.set("storedata", json.dumps(onsaleitems), ex=3600)

    return templates.TemplateResponse("index.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
        "products": onsaleitems,
        "sessiondata": SessionData
    })

@app.get("/ratelimited",response_class=HTMLResponse)
@limiter.limit("60/minute")
async def login(request: Request):
    return templates.TemplateResponse("errors.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
        "error_code": 429
    })

@app.get("/notfound",response_class=HTMLResponse)
@limiter.limit("60/minute")
async def login(request: Request):
    return templates.TemplateResponse("errors.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
        "error_code": 429  
    })

@app.get("/internalerror",response_class=HTMLResponse)
@limiter.limit("60/minute")
async def login(request: Request):
    return templates.TemplateResponse("errors.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
        "error_code": 500  
    })

@app.get("/settings",response_class=HTMLResponse)
@limiter.limit("60/minute")
async def settings(request: Request, SessionId: str = Cookie(None)):
    sessionData = None 

    if not SessionId:
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "store_name": cfg.StoreName,
            "email": "",
            "order_emails": "OrderEmailsCached"
        })

    keys = [
        SessionId,
        SessionId + "e",
        SessionId + "oe"
    ]

    sessionData, EmailCached, OrderEmailsCached = redis.mget(*keys)
    SessionIdList = SessionId.split(":")
    SessionId = SessionIdList[0]
    SessionUsername = SessionIdList[1]

    if EmailCached is None and OrderEmailsCached is None:
        with getPostgresConnection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT email,orderemails password FROM accounts WHERE username = %s AND sessionid = %s;
                """, (SessionUsername,SessionId))

                result = cursor.fetchone()

                if not result:
                    return JSONResponse({"success": False, "message": "This username has no data."})
                
                email = result[0]
                orderEmails = result[1]

                redis.mset({
                    SessionId + "e": email,
                    SessionId + "oe": orderEmails,
                })


            return templates.TemplateResponse("settings.html", {
                "request": request,
                "store_name": cfg.StoreName,
                "email": email,
                "order_emails": orderEmails
            })
    else:
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "store_name": cfg.StoreName,
            "email": EmailCached,
            "order_emails": OrderEmailsCached
        })


@app.get("/signup",response_class=HTMLResponse)
@limiter.limit("60/minute")
async def signup(request: Request):
    return templates.TemplateResponse("signup.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
    })

@app.get("/login",response_class=HTMLResponse)
@limiter.limit("60/minute")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request, 
        "store_name": cfg.StoreName,  
    })

@app.get("/admin",response_class=JSONResponse)
@limiter.limit("60/minute")
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
@limiter.limit("60/minute")
async def userloggedin(request: Request, SessionId: str = Cookie(None)):
    return userIsLoggedIn(SessionId)

@app.get("/adminapi/getPendingOrders")
@limiter.limit("60/minute")
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
        

@app.get("/store/product/{itemid}")
async def getproduct(request: Request,itemid : int):
    with getPostgresConnection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT * FROM storeitems WHERE itemid = %s;", (itemid,))
            row = cursor.fetchone()

    if not row:
        return templates.TemplateResponse("notfound.html", {
            "request": request, 
            "store_name": cfg.StoreName,  
        })
    
    ProductData = {
        "id": row["itemid"],
        "name": row["itemname"],
        "price": row["price"],
        "image": row["imageurl"],
        "description": row.get("description", "No description provided."),
        "offsale": row["offsale"],
        "created_at": row["created_at"]
    }

    return templates.TemplateResponse("productpage.html", {
        "request": request,
        "store_name": cfg.StoreName,
        "product": ProductData
    })

@app.post("/signup",response_class=JSONResponse)
@limiter.limit("60/minute")
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
@limiter.limit("60/minute")
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
@limiter.limit("60/minute")
async def logout(request : Request,response: Response):
    response.delete_cookie(
        key="SessionId",
        path="/",
        httponly=True,
        samesite="lax"
    )
    return {"success": True}

@app.post("/adminapi/newitem")
@limiter.limit("60/minute")
async def additem(request: Request,data: AddItemSchema, SessionId: str = Cookie(None)):
    itemname = data.itemname
    imageurl = data.imageurl
    description = data.description
    price = data.price
    offsale = data.offsale

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
@limiter.limit("60/minute")
async def changeitem(request: Request,data: AddItemSchema, SessionId: str = Cookie(None)):
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
@limiter.limit("60/minute")
async def lockaccount(request: Request,data: LockAccountSchema, SessionId: str = Cookie(None)):
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
@limiter.limit("60/minute")
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
@limiter.limit("60/minute")
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
@limiter.limit("60/minute")
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

            HtmlContent = generate_email_html(
                code=EmailVerificationCode,
                store_name=cfg.StoreName,
                title="Email Verification",
                message="Use the code below to verify your email address:"
            )

            sendEmail("Email Verification <verification@syntaxrevival.store>",newEmail,"Email Verification",HtmlContent)
            conn.commit()   

    return {"success": True}


@app.post("/api/VerifyEmail")
@limiter.limit("60/minute")
async def verifyemail(request: Request, data: VerifyAccountEmail, response: Response, SessionId: str = Cookie(None)):
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

@app.post("/api/OTP")
@limiter.limit("60/minute")
async def otp(request: Request, data: OTP, response: Response, SessionId: str = Cookie(None)):
    InputUsername = data.username

    if not checkUserEmailLimit(InputUsername):
        return JSONResponse({"success": False,"message": "Email sending limit reached. Try again later."})

    with getPostgresConnection() as conn:
        with conn.cursor() as cursor:
            optCode = secrets.token_urlsafe(10)

            cursor.execute("""
                UPDATE accounts
                SET otpcode = %s, 
                    otpcodetime = NOW()
                WHERE username = %s
                RETURNING email;
            """, (optCode, InputUsername))

            result = cursor.fetchone()

            if not result:
                return JSONResponse({"success": False, "message": "Invalid session or account not found."})
            
            UserEmail = result[0]       
            HtmlContent = generate_email_html(
                code=optCode,
                store_name=cfg.StoreName,
                title="One Time Login Code",
                message="Use the one time code to log into your account:"
            )

            sendEmail("One Time Code <otp@syntaxrevival.store>",UserEmail,"One Time Code",HtmlContent)
            conn.commit()   


    return {"success": True}

@app.post("/api/VerifyOTP")
@limiter.limit("60/minute")
async def verifyotp(request: Request, data: VerifyAccountEmail, response: Response, SessionIdToken: str = Cookie(None)):
    OPTCodeInput = data.code

    try:
        with getPostgresConnection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE accounts
                    SET otpcode = NULL,
                        otpcodetime = NULL
                    WHERE otpcode = %s
                    AND otpcodetime > NOW() - INTERVAL '15 minutes'
                    RETURNING username, sessionid;
                """, (OPTCodeInput,)) 

                result = cursor.fetchone()

                if result:
                    SessionUsername = result[0]
                    SessionId = result[1]
                    setSessionCookie(response,SessionId + ":" + SessionUsername)
                    conn.commit()
                    return {"success": True}
                else:
                    return JSONResponse({"success": False,"message": "This session is invalid."})

    except Exception as e:
        return JSONResponse({"success": False,"message": "Internal Server Error."})

@app.post("/api/createcryptoinvoice")
@limiter.limit("60/minute")
async def createinvoice(request: Request, data: CryptoInvoiceSchema):
    TotalPrice = 0
    PriceLookup = None
    headers = {
        "x-api-key": cfg.NowPaymentsAPISecret,
        "Content-Type": "application/json"
    }

    if not data.coin.lower() in cfg.SUPPORTEDCOINS:
        return JSONResponse({"success": False,"message": f"We currently do not support {data.coin}"})

    with getPostgresConnection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""SELECT * from storeitems""")
            rows = cursor.fetchall()
            PriceLookup = {row["itemname"].strip(): int(row["price"].replace("$",""))
                for row in rows
            }

    for itemname in data.itemnames:
        itemnameStriped = itemname.strip()

        if itemnameStriped in PriceLookup:
            TotalPrice += int(PriceLookup[itemnameStriped])
        else:
            return JSONResponse({"success": False,"message": "One of the cart items doesn't exist."})        

    payload = {
        "price_amount": TotalPrice, 
        "price_currency": "usd",
        "pay_currency": data.coin,
        "ipn_callback_url": "",
        "order_id": secrets.token_urlsafe(16),
        "order_description": f"Items: {', '.join(data.itemnames)}"
    }

    try:
        response = requests.post(cfg.NowPaymentsAPIURL, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return {"invoice_url": data.get('invoice_url')}
        else:
            return JSONResponse({"error": "Error with sending post request to nowpayments."}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Oops, something went wrong, please try again later."}, status_code=400)


@app.get("/{path:path}", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def catchall(request: Request, path: str):
    return templates.TemplateResponse("error.html", { 
        "request": request, 
        "store_name": cfg.StoreName,
        "error_code": 404  
    })
