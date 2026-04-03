from fastapi import FastAPI,Request,Response,Cookie
from fastapi.responses import JSONResponse
import resend
from config import Config
cfg = Config()
from redisclient import getRedisInstance
redis = getRedisInstance()

def trustCheckAdminUser(cursor,SessionId):
    SessionIdList = SessionId.split(":")
    SessionId = SessionIdList[0]
    
    cursor.execute("""
        SELECT locked,username FROM accounts WHERE sessionid = %s;
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


def setSessionCookie(response : Response,SessionId):
    response.set_cookie(
        key="SessionId", 
        value=SessionId, 
        max_age=34560000,  
        httponly=True,  
        secure=True,  
        samesite="Lax", 
    )

def userIsLoggedIn(SessionId):
    sessionData = None 
    if SessionId:
        sessionData = redis.get(SessionId)
        SessionIdList = SessionId.split(":")
        SessionId = SessionIdList[0]
        SessionUsername = SessionIdList[1]

        if SessionUsername == cfg.AdminUsername:
            return {"loggedin": sessionData,"isadmin":True}

    return {"loggedin": sessionData}

def generateEmailHtml(code: str, store_name: str, title: str, message: str, expiry_minutes: int = 15) -> str:
    """
    Generates HTML for an email with a verification or one-time login code.

    Args:
        code (str): The verification or login code.
        store_name (str): Name of your store/application.
        title (str): Header/title for the email (e.g., "Email Verification").
        message (str): Main message describing the code usage.
        expiry_minutes (int): How long the code is valid for. Default is 15 minutes.

    Returns:
        str: HTML content as a string.
    """
    htmlcontent = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f7f7f7; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; padding: 30px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #333;">{title}</h2>
            <p style="font-size: 16px; color: #555;">{message}</p>
            <div style="margin: 20px 0;">
                <span style="font-size: 24px; font-weight: bold; color: #1a73e8; background-color: #e8f0fe; padding: 10px 20px; border-radius: 6px;">{code}</span>
            </div>
            <p style="font-size: 14px; color: #555;">This code will expire in {expiry_minutes} minutes. Requesting a new code will expire the previous one.</p>
            <p style="font-size: 14px; color: #888;">If you did not request this, you can ignore this email.</p>
            <p style="font-size: 14px; color: #888;">&copy; {datetime.now().year} {store_name}</p>
        </div>
    </body>
    </html>
    """
    return htmlcontent

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