import requests
import os
import json
import binascii
import base64
import struct
import hashlib
import datetime

import colorama
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

TITLE_ID = os.getenv("TITLE_ID")  # Fetch from GitHub secrets
TITLE_SHARED_SECRET = os.getenv("TITLE_SHARED_SECRET")  # Fetch from GitHub secrets
PLAYER_SECRET = os.getenv("PLAYER_SECRET")  # Fetch from GitHub secrets

PLAYFAB_HEADERS = {
    "User-Agent": "libhttpclient/1.0.0.0", 
    "Content-Type": "application/json", 
    "Accept-Language": "en-US"
}

PLAYFAB_SESSION = requests.Session()
PLAYFAB_SESSION.headers.update(PLAYFAB_HEADERS)

PLAYFAB_DOMAIN = f"https://{TITLE_ID.lower()}.playfabapi.com"

def sendPlayFabRequest(endpoint, data, hdrs={}):
    rsp = PLAYFAB_SESSION.post(PLAYFAB_DOMAIN + endpoint, json=data, headers=hdrs).json()
    if rsp['code'] != 200:
        print(rsp)
    else:
        return rsp['data']
 
def getMojangCsp():
    return base64.b64decode(sendPlayFabRequest("/Client/GetTitlePublicKey", {
        "TitleId": TITLE_ID,
        "TitleSharedSecret": TITLE_SHARED_SECRET
    })['RSAPublicKey'])
    
def importCspKey(csp):
    e = struct.unpack("I", csp[0x10:0x14])[0]
    n = bytearray(csp[0x14:])
    n.reverse()
    n = int(binascii.hexlify(n), 16)
    return RSA.construct((n, e))

def genPlayFabTimestamp():
    return datetime.datetime.now().isoformat()+"Z"

def genPlayFabSignature(requestBody, timestamp):
    sha256 = hashlib.sha256()
    sha256.update(requestBody.encode("UTF-8") + b"." + timestamp.encode("UTF-8") + b"." + PLAYER_SECRET.encode("UTF-8"))
    return base64.b64encode(sha256.digest())

def LoginWithCustomId():
    customId = os.getenv("CUSTOM_ID")  # Directly use GitHub secret
    playerSecret = os.getenv("PLAYER_SECRET")  # Directly use GitHub secret
    createNewAccount = False

    if customId == None or playerSecret == None:
        createNewAccount = True

    if playerSecret == None:
        createNewAccount = True
    
    payload = {
        "CreateAccount" : None,
        "CustomId": None,
        "EncryptedRequest" : None,
        "InfoRequestParameters" : {
          "GetCharacterInventories" : False,
          "GetCharacterList" : False,
          "GetPlayerProfile" : True,
          "GetPlayerStatistics" : False,
          "GetTitleData" : False,
          "GetUserAccountInfo" : True,
          "GetUserData" : False,
          "GetUserInventory" : False,
          "GetUserReadOnlyData" : False,
          "GetUserVirtualCurrency" : False,
          "PlayerStatisticNames" : None,
          "ProfileConstraints" : None,
          "TitleDataKeys" : None,
          "UserDataKeys" : None,
          "UserReadOnlyDataKeys" : None
        },
        "PlayerSecret" : None,
        "TitleId" : TITLE_ID
    }

    if createNewAccount:
        toEnc = json.dumps({"CustomId":customId, "PlayerSecret": playerSecret}).encode("UTF-8")        
        pubkey = importCspKey(getMojangCsp())
        
        cipher_rsa = PKCS1_OAEP.new(pubkey)
        ciphertext = cipher_rsa.encrypt(toEnc)
        
        payload["CreateAccount"] = True
        payload["EncryptedRequest"] = base64.b64encode(ciphertext).decode("UTF-8")

        req = sendPlayFabRequest("/Client/LoginWithCustomID", payload)
    else:
        payload["CustomId"] = customId
        ts = genPlayFabTimestamp()
        sig = genPlayFabSignature(json.dumps(payload), ts)
        req = sendPlayFabRequest("/Client/LoginWithCustomID", payload, {"X-PlayFab-Signature": sig, "X-PlayFab-Timestamp": ts})
    entitytoken = req["EntityToken"]["EntityToken"]
    PLAYFAB_SESSION.headers.update({"X-EntityToken": entitytoken})
    return req
    
def GetEntityToken(playfabId, accType):
    req = sendPlayFabRequest("/Authentication/GetEntityToken", {
       "Entity" : {
          "Id" : playfabId,
          "Type" : accType
       }
    })
    entitytoken = req["EntityToken"]
    PLAYFAB_SESSION.headers.update({"X-EntityToken": entitytoken})
    return req
                                                
def Search(query, orderBy, select, top, skip, customIds):
    if isinstance(customIds, str):
        filter_query = f"Id eq '{customIds}'"
    elif isinstance(customIds, list):
        filter_query = " or ".join([f"Id eq '{id}'" for id in customIds])
    else:
        raise ValueError("Invalid type for customIds. It should be a string or a list.")
    return sendPlayFabRequest("/Catalog/Search", {
                                                "count": True,
                                                "query": query,
                                                "filter": f"{filter_query}",
                                                "orderBy": orderBy,
                                                "scid": "4fc10100-5f7a-4470-899b-280835760c07",
                                                "select": select,
                                                "top": top,
                                                "skip": skip
                                                })

def SearchFriendlyUuid(query, orderBy, select, top, skip, customIds):
    if isinstance(customIds, list):
        filter_query = " or ".join([f"contentType eq 'MarketplaceDurableCatalog_V1.2' and tags/any(t: t eq '{id}')" for id in customIds])
    else:
        raise ValueError("Invalid type for customIds. It should be a string or a list.")
    
    return sendPlayFabRequest("/Catalog/Search", {
                                                "count": True,
                                                "query": query,
                                                "filter": f"{filter_query}",
                                                "orderBy": orderBy,
                                                "scid": "4fc10100-5f7a-4470-899b-280835760c07",
                                                "select": select,
                                                "top": top,
                                                "skip": skip
                                                })

def process_friendlyuuid(friendlyuuid):
    MAX_SEARCH = 150

    results_dict = {}

    total_friendlyuuid = len(friendlyuuid)
    processed_friendlyuuid = 0

    use_progress_bar = total_friendlyuuid > 300

    for i in range(0, len(friendlyuuid), MAX_SEARCH):
        chunk = list(friendlyuuid.keys())[i:i + MAX_SEARCH]
        search_result = SearchFriendlyUuid("", "creationDate ASC", "title", MAX_SEARCH, 0, chunk)
        search_results = search_result["Items"]

        if search_results:
            for item in search_results:
                result_uuid = item["Id"]
                if result_uuid not in results_dict:
                    results_dict[result_uuid] = []
                results_dict[result_uuid].append(item)
        else:
            print(f"No results found for {i+1}-{min(i+MAX_SEARCH, len(friendlyuuid))}")

        processed_friendlyuuid += len(chunk)
        if use_progress_bar:
            print_progress_bar(processed_friendlyuuid, total_friendlyuuid, prefix='Converting:', suffix='Complete', length=25)
        else:
            progress_percent = (processed_friendlyuuid / total_friendlyuuid) * 100
            print(f"Progress: {progress_percent:.2f}%\r", end="", flush=True)
            print()

    unique_lines = set()
    with open("personal_keys.tsv", "w", encoding="utf-8") as df_file:
        for result_uuid, items in results_dict.items():
            for item in items:
                display_properties = item.get("DisplayProperties", {})
                pack_identity = display_properties.get("packIdentity", [])
                for identity in pack_identity:
                    if identity["uuid"] in friendlyuuid:
                        pack_type = identity.get("type").replace("worldtemplate", "world_template")
                        custom_id = identity["uuid"]
                        key = friendlyuuid[custom_id]
                        line = f"{result_uuid}\t{custom_id}\t{pack_type}\t{key}\n"
                        unique_lines.add(line)

        for line in unique_lines:
            df_file.write(line)

    unique_info_lines = set()
    with open("personal_list.txt", "w", encoding="utf-8") as f:
        for result_uuid, items in results_dict.items():
            for item in items:
                title = item.get("Title", {}).get("en-US", "")
                creator_name = item.get("DisplayProperties", {}).get("creatorName", "")
                tags = item.get("Tags", [])
                pack_type = "DLC" if "worldtemplate" in tags else "DLC"
                pack_type = "Addon" if "addon" in tags else pack_type
                pack_type = "TexturePack" if "resourcepack" in tags else pack_type
                pack_type = "Mashup" if "mashup" in tags else pack_type
                info_line = f"{title} ( {creator_name} ) - {pack_type} {result_uuid}\n"
                unique_info_lines.add(info_line)

        for info_line in unique_info_lines:
            f.write(info_line)

    print(f"{colorama.Fore.GREEN}{len(unique_lines)} converted keys!{colorama.Fore.RESET}")

def Search_name(query, orderBy, select, top, skip, search_type, search_term=None):
    base_filter = "(contentType eq 'MarketplaceDurableCatalog_V1.2')"
    tags_filter = {
        "texture": "tags/any(t: t eq 'resourcepack')",
        "mashup": "tags/any(t: t eq 'mashup')",
        "addon": "tags/any(t: t eq 'addon')",
        "persona": "(contentType eq 'PersonaDurable')",
        "capes": "(displayProperties/pieceType eq 'persona_capes')",
        "hidden": "tags/any(t: t eq 'hidden_offer')",
        "skin": "tags/any(t: t eq 'skinpack')"
    }

    if search_type in ["name", "hidden", "newest", "skin"]:
        filter_query = base_filter
        if search_type == "hidden":
            filter_query += f" and {tags_filter['hidden']}"
            search_query = None
        elif search_type == "skin":
            filter_query += f" and {tags_filter['skin']}"
            search_query = None
        elif search_type == "newest":
            filter_query = base_filter
            search_query = None
        else:
            search_query = f"\"{search_term}\""
        
        request_payload = {
            "count": True,
            "query": query,
            "filter": filter_query,
            "orderBy": "creationDate DESC",
            "scid": "4fc10100-5f7a-4470-899b-280835760c07",
            "select": select,
            "top": top,
            "skip": skip,
            "search": search_query
        }
        
        response = sendPlayFabRequest("/Catalog/Search", request_payload)
        items = response.get("Items", [])
        return items

    else:
        if search_type == "texture":
            filter_query = f"{base_filter} and {tags_filter['texture']}"
            search_query = None
        elif search_type == "mashup":
            filter_query = f"{base_filter} and {tags_filter['mashup']}"
            search_query = None
        elif search_type == "addon":
            filter_query = f"{base_filter} and {tags_filter['addon']}"
            search_query = None
        elif search_type == "allhidden":
            filter_query = f"{base_filter} and {tags_filter['hidden']}"
            search_query = None
        elif search_type == "persona":
            filter_query = f"{tags_filter['persona']}"
            search_query = f"{search_term}"
        elif search_type == "capes":
            filter_query = f"{tags_filter['capes']}"
            search_query = None

        all_items = []
        while True:
            request_payload = {
                "count": True,
                "query": query,
                "filter": filter_query,
                "orderBy": orderBy,
                "scid": "4fc10100-5f7a-4470-899b-280835760c07",
                "select": select,
                "top": top,
                "skip": skip
            }

            if search_query:
                request_payload["search"] = search_query

            response = sendPlayFabRequest("/Catalog/Search", request_payload)
            total_count = response.get("Count", 0)

            items = response.get("Items", [])
            all_items.extend(items)

            if len(items) < top or len(all_items) >= total_count:
                break

            skip += top
            if total_count - skip < top:
                top = total_count - skip

        return all_items

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█', print_end="\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=print_end)
    if iteration == total:
        print()

def main(custom_id):

    MAX_SEARCH = 300

    results_dict = {}

    if isinstance(custom_id, list):
        custom_ids = custom_id
    else:
        custom_ids = [custom_id]

    total_chunks = (len(custom_ids) + MAX_SEARCH - 1) // MAX_SEARCH

    show_progress_bar = len(custom_ids) > 100

    # Split the custom_ids list into chunks
    for i in range(0, len(custom_ids), MAX_SEARCH):
        chunk = custom_ids[i:i + MAX_SEARCH]
        search_result = Search("", "creationDate DESC", "contents", MAX_SEARCH, 0, chunk)
        search_results = search_result["Items"]

        if search_results:
            # Merge the results into the results_dict
            results_dict.update({item["Id"]: item for item in search_results})
        else:
            print(colorama.Fore.RED + f"No results found for {i+1}-{min(i+MAX_SEARCH, len(custom_ids))}")

        if show_progress_bar:
            # Print progress bar
            print_progress_bar(i // MAX_SEARCH + 1, total_chunks, prefix='Searching:', suffix='Complete', length=50)

    return results_dict
