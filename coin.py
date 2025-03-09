import json as j
import requests as r
import os as o
from playfab import LoginWithCustomId as L, GetEntityToken as G

tc, s, c, i, m = 1, 0, 300, [], 3000

def ep():
    pm = {'requests': 'requests', 'colorama': 'colorama'}
    for mn, pn in pm.items():
        try:
            __import__(mn)
        except ModuleNotFoundError:
            try:
                pass
            except Exception:
                pass

ep()

def l():
    r = L()
    if 'PlayFabId' in r:
        return G(r['PlayFabId'], 'master_player_account')
    return None

def f(t, s, c):
    u, h = "https://20ca2.playfabapi.com/Catalog/Search", {"x-entitytoken": t["EntityToken"], "Accept": "application/json"}
    b = {"filter": "(contentType eq 'PersonaDurable')", "orderBy": "creationDate DESC", "search": "Minecraft", "skip": s, "top": c}
    re = r.post(u, json=b, headers=h)
    return re.json() if re.status_code == 200 else {}

def m():
    global tc, s, c, i
    at = l()
    if not at:
        return
    fd = f(at, s, c)
    if fd:
        tc = fd.get('data', {}).get('Count', 0)
    if tc > m:
        tc = m
    while s < tc:
        fd = f(at, s, c)
        if fd:
            i.extend(fd.get('data', {}).get('Items', []))
        s += c
    fd = {"data": {"Count": tc, "Items": i}}
    o.makedirs('marketplace', exist_ok=True)
    with open('marketplace/data.json', 'w', encoding='utf-8') as f:
        j.dump(fd, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    m()
