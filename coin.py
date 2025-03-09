import json
import requests
import os
from playfab import LoginWithCustomId, GetEntityToken

TOTALCOUNT = 1
SKIP = 0
COUNT = 300
ITEMS = []  # List to aggregate all items
MAX_ITEMS = 3000  # Max number of items to fetch

def ensure_packages_installed():
    package_map = {
        'requests': 'requests',
        'colorama': 'colorama'
    }
    for module_name, package_name in package_map.items():
        try:
            __import__(module_name)
        except ModuleNotFoundError:
            print(f"Module '{module_name}' not found. Installing '{package_name}'...")
            try:
                print(f"Successfully installed '{package_name}'.")
            except Exception as e:
                print(f"Failed to install '{package_name}': {e}")

ensure_packages_installed()

def login():
    response = LoginWithCustomId()
    
    if 'PlayFabId' in response:
        auth_token = GetEntityToken(response['PlayFabId'], 'master_player_account')
        print("Authentication successful.")
        return auth_token
    else:
        print("Authentication failed.")
        return None

def fetch_items(auth_token, skip, count):
    url = "https://20ca2.playfabapi.com/Catalog/Search"
    headers = {
        "x-entitytoken": auth_token["EntityToken"],  # Extract only the token
        "Accept": "application/json"
    }
    body = {
        "filter": "(contentType eq 'PersonaDurable')",
        "orderBy": "creationDate DESC",
        "search": "Minecraft",
        "skip": skip,
        "top": count
    }

    response = requests.post(url, json=body, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data  # Return the entire JSON response
    else:
        print(f"API call failed: {response.text}")
        return {}

def main():
    auth_token = login()
    if not auth_token:
        print("Exiting due to authentication failure.")
        return
    
    global TOTALCOUNT, SKIP, COUNT, ITEMS
    
    # Fetch the full JSON response first
    full_data = fetch_items(auth_token, SKIP, COUNT)
    
    if full_data:
        # Print the full JSON response for verification
        print(json.dumps(full_data, ensure_ascii=False, indent=4))
        
        # Extract the total count for pagination from the response
        TOTALCOUNT = full_data.get('data', {}).get('Count', 0)
        print(f"Total items to fetch: {TOTALCOUNT}")
    
    # Limit the maximum number of items to fetch to 3000
    if TOTALCOUNT > MAX_ITEMS:
        TOTALCOUNT = MAX_ITEMS
        print(f"Limiting the total number of items to fetch to {MAX_ITEMS}")
    
    # Loop through the items and fetch in batches of 300
    while SKIP < TOTALCOUNT:
        print(f"Fetching items {SKIP} to {min(SKIP + COUNT, TOTALCOUNT)}")
        full_data = fetch_items(auth_token, SKIP, COUNT)
        
        if full_data:
            # Aggregate the items into the ITEMS list (this is where the items are collected)
            items = full_data.get('data', {}).get('Items', [])
            ITEMS.extend(items)
        
        # Update the SKIP value for pagination
        SKIP += COUNT
    
    # Create the final structure for saving (include the entire response structure with aggregated items)
    final_data = {
        "data": {
            "Count": TOTALCOUNT,
            "Items": ITEMS  # Aggregate all the fetched items
        }
    }

    # Create the marketplace directory if it doesn't exist
    os.makedirs('marketplace', exist_ok=True)

    # Save the full structure (including the aggregated items) to data.json inside the marketplace folder
    with open('marketplace/data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
    
    print(f"Fetched {len(ITEMS)} items and saved the full response (including aggregated items) to data.json")

if __name__ == "__main__":
    main()
