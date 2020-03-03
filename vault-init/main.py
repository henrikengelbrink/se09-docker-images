import http.client
import json
import os
import time

vault_host = os.environ['VAULT_HOST']
vault_port = os.environ['VAULT_PORT']
root_domain = os.environ['CERT_ROOT_DOMAIN']
root_domain_name = root_domain.replace(".", "-")

time.sleep(30)
print("Timer ended")
vault_port_int = int(vault_port)
conn = http.client.HTTPConnection(vault_host, vault_port_int)

vault_root_token = None

def sendRequest(method, payload, path):
    headers = {
      'Content-Type': 'application/json'
    }
    if vault_root_token != None:
      headers["X-Vault-Token"] = vault_root_token

    body = ''
    if payload != None:
      body = json.dumps(payload)

    conn.request(method, path, body, headers)
    res = conn.getresponse()
    #print("****************************")
    #print(path)
    #print(res.read)
    data = res.read()
    #print(data.decode("utf-8"))
    return data.decode("utf-8")

################################################################
# Init Vault
body  = {
    'recovery_shares': 1,
    'recovery_threshold': 1
}
data = sendRequest("PUT", body, "/v1/sys/init")
json_data = json.loads(data)
vault_root_token = json_data["root_token"]
print(vault_root_token)

################################################################
# Create PKI Policy
# policy_data = ""
# with open('pki_policy.hcl', 'r') as file:
#     policy_data = file.read().replace('\n','\\n')
#     print(policy_data)
# body  = {
#   "policy": policy_data
# }
# sendRequest("PUT", body, "/v1/sys/policies/acl/pki-policy")

################################################################
# Create PKI
body  = {
    'type': 'pki'
}
sendRequest("POST", body, "/v1/sys/mounts/pki")

body  = {
    'default_lease_ttl': '172800h',
    'max_lease_ttl': '172800h'
}
sendRequest("POST", body, "/v1/sys/mounts/pki/tune")

################################################################
# Generate Root CA
body = {
    'common_name': root_domain,
    'ttl': '172800h'
}
data = sendRequest("POST", body, "/v1/pki/root/generate/internal")
dataMap = json.loads(data)
caRootCertString = dataMap['data']['certificate']
caRootCertString = caRootCertString + "\n"
CaRootCertFile = open("./root-ca.crt", "w")
CaRootCertFile.write(caRootCertString.replace('\\n', '\n'))
CaRootCertFile.close()

body = {
    'issuing_certificates': 'http://localhost:8200/v1/pki/ca',
    'crl_distribution_points': 'http://localhost:8200/v1/pki/crl'
}
sendRequest("POST", body, "/v1/pki/config/urls")

################################################################
# Create Intermediate PKI
body  = {
    'type': 'pki'
}
sendRequest("POST", body, "/v1/sys/mounts/pki_int")

body  = {
    'default_lease_ttl': '172800h',
    'max_lease_ttl': '172800h'
}
sendRequest("POST", body, "/v1/sys/mounts/pki_int/tune")

################################################################
# Generate Intermediate CA
body = {
    'common_name': root_domain + ' Intermediate Authority'
}
data = sendRequest("POST", body, "/v1/pki_int/intermediate/generate/internal")
dataMap = json.loads(data)
csrString = dataMap['data']['csr']

################################################################
# Sign Intermediate CA
body = {
    'csr': csrString,
    'format': 'pem_bundle',
    'ttl': '172800h'
}
data = sendRequest("POST", body, "/v1/pki/root/sign-intermediate")
dataMap = json.loads(data)
certString = dataMap['data']['certificate']

body = {
    'certificate': certString
}
sendRequest("POST", body, "/v1/pki_int/intermediate/set-signed")

################################################################
# Create Intermediate PKI Role
body = {
    'allowed_domains': root_domain,
    'allow_subdomains': 'true',
    'max_ttl': '172800h'
}
sendRequest("POST", body, "/v1/pki_int/roles/" + root_domain_name)

################################################################
# Enable Key-Value secret engine
body  = {
    'type': 'kv',
    'options': {
      'version': '2'
    }
}
sendRequest("POST", body, "/v1/sys/mounts/kv")


def issueCert(common_name, file_name):
    body = {
        'common_name': common_name,
        'ttl': '172799h'
    }
    data = sendRequest("POST", body, "/v1/pki_int/issue/" + root_domain_name)
    dataMap = json.loads(data)
    certificateString = dataMap['data']['certificate']
    certificateString = certificateString + "\n"
    #certFile = open("./self/" + file_name + ".crt", "w")
    #certFile.write(certificateString.replace('\\n', '\n'))
    #certFile.close()

    keyString = dataMap['data']['private_key']
    keyString = keyString + "\n"
    #keyFile = open("./self/" + file_name + ".key", "w")
    #keyFile.write(keyString.replace('\\n', '\n'))
    #keyFile.close()

    caString = dataMap['data']['issuing_ca']
    caString = caString + "\n"
    #caFile = open("./self/ca.crt", "w")
    #caFile.write(caString.replace('\\n', '\n'))
    #caFile.close()
    return {
      'ca': caString,
      'cert': certificateString,
      'key': keyString
    }

server_cert_data = issueCert('mqtt.engelbrink.dev', 'server')
caFile = open("./ca.crt", "w")
caFile.write(server_cert_data["ca"].replace('\\n', '\n'))
caFile.close()
os.system('cat ./root-ca.crt ./ca.crt > ./chain.crt')
chain_cert_file = open('./chain.crt','r')
chain_cert_string = chain_cert_file.read()
chain_cert_string = chain_cert_string.replace('\n', '\\n')


body  = {
    'data': {
      'chain_crt': chain_cert_string,
      'server_crt': server_cert_data['cert'],
      'server_key': server_cert_data['key']
    }
}
sendRequest("POST", body, "/v1/kv/data/mqtt-server-cert")
