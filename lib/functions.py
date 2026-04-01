from fastapi import FastAPI,Request,Response,Cookie
from fastapi.responses import JSONResponse
import resend
from config import Config
cfg = Config()

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