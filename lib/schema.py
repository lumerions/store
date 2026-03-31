from pydantic import BaseModel, EmailStr

class SignupSchema(BaseModel):
    confirmpassword: str
    password: str
    username: str
    email: EmailStr

class LoginSchema(BaseModel):
    username: str
    password: str

class AddItemSchema(BaseModel):
    itemname: str
    price: str
    imageurl: str
    description: str
    offsale: bool

class LockAccountSchema(BaseModel):
    username: str
    lockaccount: str

class ChangePasswordSchema(BaseModel):
    currentpassword: str
    newpassword: str

class EnableOrderEmailsSchema(BaseModel):
    enable: bool

class ChangeAccountEmailSchema(BaseModel):
    email: EmailStr

class VerifyAccountEmail(BaseModel):
    code: str

class OTP(BaseModel):
    pass 