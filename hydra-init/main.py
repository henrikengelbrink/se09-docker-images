import requests
import json
import os
import secrets

hydra_host = os.environ['HYDRA_HOST']
hydra_port = os.environ['HYDRA_PORT']
hydra_client_name = os.environ['HYDRA_CLIENT_NAME']

url = hydra_host + ":" + hydra_port +  "/clients"

client_id = secrets.token_hex(16)
print(hydra_client_name + " client_id: " + client_id)

body  = {
    "client_name": hydra_client_name,
    "client_id": client_id,
    "token_endpoint_auth_method": "none",
    "response_types": ["code", "id_token"],
    "grant_types": ["refresh_token","authorization_code"],
    "scope": "openid offline",
    "redirect_uris": ["com.se09-user-app:/oauth2/callback"]
}
payload = json.dumps(body)

headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data = payload)
print("Client create status: " + str(response.status_code))
