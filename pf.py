import requests as r, os as o, json as j, binascii as b, base64 as b64, struct as s, hashlib as h, datetime as dt
from Crypto.PublicKey import RSA as rsa
from Crypto.Cipher import PKCS1_OAEP as p

T=o.getenv("TITLE_ID")
S=o.getenv("TITLE_SHARED_SECRET")
P=o.getenv("PLAYER_SECRET")
H={"User-Agent":"libhttpclient/1.0.0.0","Content-Type":"application/json","Accept-Language":"en-US"}
C=r.Session()
C.headers.update(H)
D=f"https://{T.lower()}.playfabapi.com"

def x(e,d,h={}):return C.post(D+e,json=d,headers=h).json()['data'] if C.post(D+e,json=d,headers=h).json()['code']==200 else print(C.post(D+e,json=d,headers=h).json())
def g():return b64.b64decode(x("/Client/GetTitlePublicKey",{"TitleId":T,"TitleSharedSecret":S})['RSAPublicKey'])
def i(c):e=s.unpack("I",c[0x10:0x14])[0];n=bytearray(c[0x14:]);n.reverse();n=int(b.hexlify(n),16);return rsa.construct((n,e))
def t():return dt.datetime.now().isoformat()+"Z"
def sig(r,t):return b64.b64encode(h.sha256().update(r.encode("UTF-8")+b"." +t.encode("UTF-8")+b"." +P.encode("UTF-8")).digest())
def l():
    c=o.getenv("CUSTOM_ID")
    p=o.getenv("PLAYER_SECRET")
    n=False
    if c==None or p==None:n=True
    if p==None:n=True
    pld={"CreateAccount":None,"CustomId":None,"EncryptedRequest":None,"InfoRequestParameters":{"GetCharacterInventories":False,"GetCharacterList":False,"GetPlayerProfile":True,"GetPlayerStatistics":False,"GetTitleData":False,"GetUserAccountInfo":True,"GetUserData":False,"GetUserInventory":False,"GetUserReadOnlyData":False,"GetUserVirtualCurrency":False,"PlayerStatisticNames":None,"ProfileConstraints":None,"TitleDataKeys":None,"UserDataKeys":None,"UserReadOnlyDataKeys":None},"PlayerSecret":None,"TitleId":T}
    if n:
        toEnc=j.dumps({"CustomId":c,"PlayerSecret":p}).encode("UTF-8")
        pubkey=i(g())
        cipher_rsa=p.new(pubkey)
        ct=cipher_rsa.encrypt(toEnc)
        pld["CreateAccount"]=True
        pld["EncryptedRequest"]=b64.b64encode(ct).decode("UTF-8")
        req=x("/Client/LoginWithCustomID",pld)
    else:
        pld["CustomId"]=c
        ts=t()
        sgn=sig(j.dumps(pld),ts)
        req=x("/Client/LoginWithCustomID",pld,{"X-PlayFab-Signature":sgn,"X-PlayFab-Timestamp":ts})
    et=req["EntityToken"]["EntityToken"]
    C.headers.update({"X-EntityToken":et})
    return req
def gt(f,t):req=x("/Authentication/GetEntityToken",{"Entity":{"Id":f,"Type":t}});et=req["EntityToken"];C.headers.update({"X-EntityToken":et});return req
