# Arguments for this provider are defined by Environment Varibales
provider "google" {
}

# Access the configuration of the Google Cloud provider
data "google_client_config" "current" {}

# VAULT_TOKEN and VAULT_ADDR environment variables should be set. See file ../vault-helm/README.md
provider "vault" {}