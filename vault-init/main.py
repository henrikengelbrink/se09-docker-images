import http.client
import json
import os
import time
import base64

vault_host = os.environ['VAULT_HOST']
vault_port = os.environ['VAULT_PORT']
root_domain = os.environ['CERT_ROOT_DOMAIN']
root_domain_name = root_domain.replace(".", "-")

k8s_host = os.environ['K8S_HOST']
k8s_ca_cert = os.environ['K8S_CA_CERT']
k8s_token = os.environ['K8S_TOKEN']

k8s_host_env = os.environ['KUBERNETES_PORT_443_TCP_ADDR']
cluster_token_env = os.environ['CLUSTER_TOKEN']

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
    print("****************************")
    print(path)
    data = res.read()
    print(data.decode("utf-8"))
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
    'max_lease_ttl': '87600h'
}
sendRequest("POST", body, "/v1/sys/mounts/pki/tune")

################################################################
# Generate Root CA
body = {
    'common_name': root_domain,
    'ttl': '87600h',
    'key_bits': 4096
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
    'max_lease_ttl': '87600h'
}
sendRequest("POST", body, "/v1/sys/mounts/pki_int/tune")

################################################################
# Generate Intermediate CA
body = {
    'common_name': root_domain + ' Intermediate Authority',
    'key_bits': 4096
}
data = sendRequest("POST", body, "/v1/pki_int/intermediate/generate/internal")
dataMap = json.loads(data)
csrString = dataMap['data']['csr']

################################################################
# Sign Intermediate CA
body = {
    'csr': csrString,
    'format': 'pem_bundle',
    'ttl': '87600h'
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
    'max_ttl': '8760h'
}
sendRequest("POST", body, "/v1/pki_int/roles/" + root_domain_name)

################################################################
# Enable Key-Value secret engine
body  = {
    'type': 'kv'
}
sendRequest("POST", body, "/v1/sys/mounts/secret")


def issueCert(common_name, file_name):
    body = {
        'common_name': common_name,
        'ttl': '8760h'
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

################################################################
# Issue server cert for MQTT broker
server_cert_data = issueCert('mqtt.engelbrink.dev', 'server')
caFile = open("./ca.crt", "w")
caFile.write(server_cert_data["ca"].replace('\\n', '\n'))
caFile.close()
os.system('cat ./root-ca.crt ./ca.crt > ./chain.crt')
chain_cert_file = open('./chain.crt','r')
chain_cert_string = chain_cert_file.read()
#chain_cert_string = chain_cert_string.replace('\n', '\\n')


body  = {
    'data': {
      'chain_crt': chain_cert_string
    }
}
sendRequest("POST", body, "/v1/secret/mqtt-server-chain")

body  = {
    'data': {
      'server_crt': server_cert_data['cert']
    }
}
sendRequest("POST", body, "/v1/secret/mqtt-server-cert")
body  = {
    'data': {
      'server_key': server_cert_data['key']
    }
}
sendRequest("POST", body, "/v1/secret/mqtt-server-key")

################################################################
# Enable k8s secret engine
body  = {
    'type': 'kubernetes'
}
sendRequest("POST", body, "/v1/sys/auth/kubernetes")

k8s_ca_cert_bytes = base64.b64decode(k8s_ca_cert)
k8s_ca_cert_decoded = k8s_ca_cert_bytes.decode('ascii')
#k8s_ca_cert_decoded = k8s_ca_cert_decoded.replace("\n", "\\n")

cluster_token_file = open('/var/run/secrets/kubernetes.io/serviceaccount/token','r')
cluster_token = cluster_token_file.read()
print(cluster_token)

print("***********************")
print("***********************")
print("***********************")
print(k8s_ca_cert_decoded)

print("***********************")
print("***********************")

val_kubernetes_host = "https://" + k8s_host_env + ":443"
val_kubernetes_ca_cert = k8s_ca_cert_decoded
val_token_reviewer_jwt = cluster_token_env

print("val_kubernetes_host")
print(val_kubernetes_host)
print("val_kubernetes_ca_cert")
print(val_kubernetes_ca_cert)
print("val_token_reviewer_jwt")
print(val_token_reviewer_jwt)

body  = {
    'kubernetes_host': val_kubernetes_host,
    'kubernetes_ca_cert': val_kubernetes_ca_cert,
    'token_reviewer_jwt': val_token_reviewer_jwt
}
k8s_config_response = sendRequest("POST", body, "/v1/auth/kubernetes/config")
print(k8s_config_response)

################################################################
# Create k8s Policy for mqtt
policy_data = "path \"secret/mqtt-server-*\" {\n  capabilities = [\"read\"]\n}"
body  = {
  "policy": policy_data
}
sendRequest("PUT", body, "/v1/sys/policies/acl/mqtt-server-cert-secret-policy")

################################################################
# Create k8s role for vault example
body  = {
  "bound_service_account_names": "vault-auth",
  "bound_service_account_namespaces": "vault",
  "policies": ["mqtt-server-cert-secret-policy"],
  "max_ttl": 1800000
}
sendRequest("POST", body, "/v1/auth/kubernetes/role/mqtt-server-cert-secret-role")

################################################################
# Create k8s role for vernemq
body  = {
  "bound_service_account_names": "vernemq-cluster",
  "bound_service_account_namespaces": "mqtt",
  "policies": ["mqtt-server-cert-secret-policy"],
  "max_ttl": 1800000
}
sendRequest("POST", body, "/v1/auth/kubernetes/role/vernemq-role")

################################################################
# Create k8s Policy for device-service
policy_data = "path \"pki*\" {\n  capabilities = [\"create\", \"read\", \"update\"]\n}"
body  = {
  "policy": policy_data
}
sendRequest("PUT", body, "/v1/sys/policies/acl/device-service-policy")

################################################################
# Create k8s role for device-service
body  = {
  "bound_service_account_names": "device-service",
  "bound_service_account_namespaces": "services",
  "policies": ["device-service-policy", "mqtt-server-cert-secret-policy"],
  "max_ttl": 1800000
}
sendRequest("POST", body, "/v1/auth/kubernetes/role/device-service-role")
