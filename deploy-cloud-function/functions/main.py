# Global (instance-wide) scope
# If you declare a variable in global scope, its value can be reused in subsequent invocations without having to be recomputed (caching). 
import os
import requests

# Set the address of Vault cluster
vault_addr = os.environ['VAULT_ADDR']

# Query metadata of cloud funtion for JWT token 
# The JWT token maps to the service account attached this cloud function
jwt = requests.get('http://metadata/computeMetadata/v1/instance/service-accounts/default/identity',
    headers={'Metadata-Flavor':'Google'},
    params={'audience':'http://vault/apikey1', 'format':'full'})

def F(request):
    # Per-function scope
    # This computation runs every time this function is called

    # Authenticate to Vault using JWT token
    auth = requests.post(vault_addr + '/v1/auth/gcp/login',
    json={'role':'apikey1', 'jwt':jwt.text})

    # Extract Vault token from respose    
    vault_token = auth.json()['auth']['client_token']

    # Request our secret - API Key
    r = requests.get(vault_addr + '/v1/secret/apikeys/apikey1',
        headers={'x-vault-token': vault_token})

    # Extract the value our API Key 
    apikey = r.json()['data']['value']
    return f'{apikey}'
