### Configure GCP service accounts and Vault server



This README will provide you with the building blocks (aka Terraform stanzas) required to configure our Vault server with data to be retrieved by a serverless cloud functoin. You will write your configuration by adding the stanzas in this README to `main.tf` configuration file.

To begin we will query the `google_client_config` data source. This will give us access to vaules specific to the Google Cloud provider. We have provided our credentials for Google Cloud as environment variables, so adding this data source allows us to access those vaules within our configuration without explictly defining them as `variable` blocks.
```hcl
# Access the configuration of the Google Cloud provider
data "google_client_config" "current" {}
```


Next, we will create a service account within GCP. This service account will be used to facilitate communicatioin between vault and the Google Cloud API.
Note: A service account is a special type of Google account that belongs to your application or a virtual machine (VM), instead of to an individual end user. Your application assumes the identity of the service account to call Google APIs so that the users aren't directly involved.
```hcl
# Service account for Vault to comminicate with Google Cloud API
resource "google_service_account" "vault-verifier" {
  account_id   = "vault-verifier"
  display_name = "Service account for Vault to comminicate with Google Cloud API"
}
```

Create a credentials key file for the service account. This file contains the credentials (json format) required to configure the GCP auth backend within Vault.
```hcl
# Create credentials key file for service account
resource "google_service_account_key" "vault-verifier-key" {
  service_account_id = google_service_account.vault-verifier.name
}
```

Then grant the service account the ability to verify other service accounts.
```hcl
# Grant the service account the ability to verify other service accounts
resource "google_project_iam_binding" "vault-verifier-iam" {
  project = data.google_client_config.current.project
  role    = "roles/iam.serviceAccountUser"

  members = [
    "serviceAccount:${google_service_account.vault-verifier.email}"
  ]
}
```

We need to store a secret within Vault. This secret will be retrieved later on using our serverless cloud function. 

For this, we will mount a K/V secrets engine in Vault. Then we can write a secret to a specified path. 
```hcl
# Mount kv secrets engine at path "secret"
resource "vault_mount" "kv" {
  path = "secret"
  type = "kv"
  description = "Mount KV secrets engine at path secret"
}
```
```hcl
# Add API key secret to vault 
resource "vault_generic_secret" "apikey1" {
  path = "secret/apikeys/apikey1"

  data_json = <<EOT
{
  "value":   "my-super-secret-apikey"
}
EOT
}
```


Enable Google Cloud authentication to Vault. This enables Google Cloud entities, including Cloud Functions, to authenticate to Vault using their instance metadata.
```hcl
# Enable GCP auth bakend in vault
resource "vault_gcp_auth_backend" "gcp" {
    credentials  = base64decode(google_service_account_key.vault-verifier-key.private_key)
}
```

Create a policy in Vault that permits read only access the API key value created above. Vault will assign this policy to the Cloud Function's authentication, allowing it to retrieve the value.
```hcl
# Create policy that grants read access to API key
resource "vault_policy" "apikey1" {
  name = "apikey1"

  policy = <<EOT
path "secret/apikeys/apikey1" {
  capabilities = ["read"]
}
EOT
}
```

Create a new service account which will be attached to the Cloud Function at boot.
```hcl
# Service account which will be attached to the Cloud Function at boot
resource "google_service_account" "vault-auther" {
  account_id   = "vault-auther"
  display_name = "Service account which will be attached to the Cloud Function at boot"
}
```

Create a role that permits this service account to authenticate to Vault. Upon success, Vault will assign the policy just created to the resulting token.
```hcl
# Create a GCP role in vault that permits auther service account to authenticate to Vault
# The auther service account is the one that is attached to the deployed cloud function
resource "vault_gcp_auth_backend_role" "apikey1" {
    role                   = "apikey1"
    type                   = "iam"
    backend                = vault_gcp_auth_backend.gcp.path
    bound_projects         = [data.google_client_config.current.project]
    token_policies         = [vault_policy.apikey1.name]
    bound_service_accounts = [google_service_account.vault-auther.email]
    max_jwt_exp            = "60m"
}
```

Then we can apply our configuration. From the command line run:
    
    terraform init
    terraform apply -auto-approve