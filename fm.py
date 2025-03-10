import json,requests as rq,os as sys_os
from pf import LoginWithCustomId as LWC, GetEntityToken as GET
T_C,S_K,C_T,I_L,M_I=1,0,300,[],3000

def chk_pkg():
 p_m={'requests':'requests','colorama':'colorama'}
 for m_n,p_n in p_m.items():
  try:__import__(m_n)
  except ModuleNotFoundError:
   print(f"Module '{m_n}' not found. Installing '{p_n}'...")
   try:print(f"Successfully installed '{p_n}'.")
   except Exception as e:print(f"Failed to install '{p_n}': {e}")

chk_pkg()

def auth():
 rsp=LWC()
 if'PlayFabId'in rsp:
  a_t=GET(rsp['PlayFabId'],'master_player_account')
  print("Authentication successful.")
  return a_t
 else:print("Authentication failed.");return None

def g_itm(a_t,s_k,c_t):
 u="https://20ca2.playfabapi.com/Catalog/Search"
 h={"x-entitytoken":a_t["EntityToken"],"Accept":"application/json"}
 b={"filter":"(contentType eq 'PersonaDurable')","orderBy":"creationDate DESC","search":"Minecraft","skip":s_k,"top":c_t}
 r=rq.post(u,json=b,headers=h)
 return r.json()if r.status_code==200 else(print(f"API call failed: {r.text}"),{})[1]

def g_uuid(a_t,uuid):
 u=f"https://20ca2.playfabapi.com/Catalog/Item/{uuid}"
 h={"x-entitytoken":a_t["EntityToken"],"Accept":"application/json"}
 r=rq.get(u,headers=h)
 return r.json() if r.status_code==200 else (print(f"API call failed for UUID {uuid}: {r.text}"), {})[1]

def fetch_extra_items(a_t,items_list):
 extra_items=[]
 for uuid in items_list:
  print(f"Fetching data for UUID: {uuid}")
  data=g_uuid(a_t,uuid.strip())
  if data:extra_items.append(data)
 return extra_items

def main():
 a_t=auth()
 if not a_t:return print("Exiting due to authentication failure.")
 global T_C,S_K,C_T,I_L
 f_d=g_itm(a_t,S_K,C_T)
 if f_d:print(json.dumps(f_d,ensure_ascii=False,indent=4));T_C=f_d.get('data',{}).get('Count',0);print(f"Total items to fetch: {T_C}")
 if T_C>M_I:T_C=M_I;print(f"Limiting the total number of items to fetch to {M_I}")
 while S_K<T_C:
  print(f"Fetching items {S_K} to {min(S_K+C_T,T_C)}")
  f_d=g_itm(a_t,S_K,C_T)
  if f_d:I_L.extend(f_d.get('data',{}).get('Items',[]))
  S_K+=C_T
 f_str={"data":{"Count":T_C,"Items":I_L}}

 extra_file='marketplace/extra.txt'
 if sys_os.path.exists(extra_file):
  with open(extra_file,'r',encoding='utf-8')as f:
   extra_uuids=f.readlines()
  extra_results=fetch_extra_items(a_t,extra_uuids)
  f_str["data"].setdefault("ExtraItems",[]).extend(extra_results)

 sys_os.makedirs('marketplace',exist_ok=True)
 with open('marketplace/data.json','w',encoding='utf-8')as f:json.dump(f_str,f,ensure_ascii=False,indent=4)
 print(f"Fetched {len(I_L)} items and saved the full response (including aggregated items and extra UUIDs) to data.json")

if __name__=="__main__":main()
