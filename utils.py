from requests import Session
from time import sleep, time
from datetime import datetime, timezone
from pathlib import Path

import requests, os, string

def urlencode(url: str):
    is_ok = string.ascii_letters + "0123456789-_.~"
    ret = list(url)
    for (i, c) in enumerate(ret):
        if c not in is_ok:
            ret[i] = f"%{c.encode().hex()}".upper()
    return "".join(ret)


def transformPath(pth: str):
    newPth = ""
    pth = pth.replace('—', '--').replace(':', '-')
    is_ok = string.ascii_letters + "0123456789_-éèêùôç&à+-?!,()[]' "
    for p in pth:
        if p in is_ok:
            newPth += p
        else:
            newPth += "?"
    return newPth

def url_decode(url):
    import urllib.parse
    return urllib.parse.unquote(url)

BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
    "Accept-Language": "fr,fr-FR;q=0.9,en-US;q=0.8,en-GB;q=0.7,en;q=0.6",
    "Cache-Control": "no-cache",
    "DNT": "1",
    "Pragma": "no-cache",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
}

def buildHeaders(contentType: str):
    h = BASE_HEADERS.copy()
    h.update({"Content-Type": contentType})
    return h

def buildLoginForms(username: str, passwd: str, ajax_id: str):
    return "user_id=" + username + "&password=" + urlencode(passwd) + "&login=Se+connecter&secondaryAuthToken=&showMFARegistration=%24showMFARegistration&showMFAVerification=%24showMFAVerification&showMFASuccessFul=%24showMFASuccessFul&action=login&new_loc=&blackboard.platform.security.NonceUtil.nonce.ajax=" + ajax_id



def clear_console():
    os.system("clear")
