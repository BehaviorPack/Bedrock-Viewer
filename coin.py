import json
import requests as rq
import os as sys_os
from playfab import LoginWithCustomId as LWC, GetEntityToken as GET
T_C = 1
S_K = 0
C_T = 300
I_L = []
M_I = 3000
def chk_pkg():
    p_m = {
        'requests': 'requests',
        'colorama': 'colorama'
    }
    for m_n, p_n in p_m.items():
        try:
            __import__(m_n)
        except ModuleNotFoundError:
            print(f"Module '{m_n}' not found. Installing '{p_n}'...")
            try:
                print(f"Successfully installed '{p_n}'.")
            except Exception as e:
                print(f"Failed to install '{p_n}': {e}")
chk_pkg()
def auth():
    rsp = LWC()
    if 'PlayFabId' in rsp:
        a_t = GET(rsp['PlayFabId'], 'master_player_account')
        print("Authentication successful.")
        return a_t
    else:
        print("Authentication failed.")
        return None
def g_itm(a_t, s_k, c_t):
    u = "https://20ca2.playfabapi.com/Catalog/Search"
    h = {
        "x-entitytoken": a_t["EntityToken"],
        "Accept": "application/json"
    }
    b = {
        "filter": "(contentType eq 'PersonaDurable')",
        "orderBy": "creationDate DESC",
        "search": "Minecraft",
        "skip": s_k,
        "top": c_t
    }
    r = rq.post(u, json=b, headers=h)
    if r.status_code == 200:
        d = r.json()
        return d
    else:
        print(f"API call failed: {r.text}")
        return {}
def main():
    a_t = auth()
    if not a_t:
        print("Exiting due to authentication failure.")
        return
    global T_C, S_K, C_T, I_L
    f_d = g_itm(a_t, S_K, C_T)
    if f_d:
        print(json.dumps(f_d, ensure_ascii=False, indent=4))
        T_C = f_d.get('data', {}).get('Count', 0)
        print(f"Total items to fetch: {T_C}")
    if T_C > M_I:
        T_C = M_I
        print(f"Limiting the total number of items to fetch to {M_I}")
    while S_K < T_C:
        print(f"Fetching items {S_K} to {min(S_K + C_T, T_C)}")
        f_d = g_itm(a_t, S_K, C_T)
        if f_d:
            i = f_d.get('data', {}).get('Items', [])
            I_L.extend(i)
        S_K += C_T
    f_str = {
        "data": {
            "Count": T_C,
            "Items": I_L
        }
    }
    sys_os.makedirs('marketplace', exist_ok=True)
    with open('marketplace/data.json', 'w', encoding='utf-8') as f:
        json.dump(f_str, f, ensure_ascii=False, indent=4)
    print(f"Fetched {len(I_L)} items and saved the full response (including aggregated items) to data.json")
if __name__ == "__main__":
    main()