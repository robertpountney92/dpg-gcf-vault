### Deploy Cloud Function

We must set additional enviornment variable to be provided the Cloud Function. We do not have access to the vaule of $VAULT_ADDR in our terraform configuration, so we must create an additiona variable prefixed with TF_VAR that we can access.
    
    export TF_VAR_VAULT_ADDR=$VAULT_ADDR

Following this we can form our `main.tf` configuration file that will be used to deploy our Google Cloud Function.

Create variiable within the configuration to take on the vaule assigned to our environment variable `TF_VAR_VAULT_ADDR`.
```hcl
# Vaule of this variable is set through TF_VAR_VAULT_ADDR env var
variable "VAULT_ADDR" {}
```

Use remote state data source to retrived service account email address outputtted from our previous Terraform configuration located in seperate directory.
```hcl
# Retrive service account email outputtted from other terraform config
data "terraform_remote_state" "gcp-vault-config" {
  backend = "local"

  config = {
    path = "../gcp-vault-config/terraform.tfstate"
  }
}
```

In Terraform we must package our source code into a zip file in order to be deployed.
```hcl
# Deploy Google Cloud Function
# Zip up our source code
data "archive_file" "apikey-zip" {
 type        = "zip"
 source_dir  = "${path.root}/functions/"
 output_path = "${path.root}/apikey.zip"
}
```

We can then store this zipped package in a Google Storage bucket.
```hcl
# Create the storage bucket
resource "google_storage_bucket" "apikey-bucket" {
 name   = "apikey-bucket"
}
```
```hcl
# Place the zipped code in the bucket
resource "google_storage_bucket_object" "apikey-zip" {
 name   = "apikey.zip"
 bucket = google_storage_bucket.apikey-bucket.name
 source = "${path.root}/apikey.zip"
}
```

Finally we are able to create our Google Cloud Funtion. Here we supply the location of our zipped source code and the address of our Vault server as an environment variable. We also attach the vault-auther service account that we created previously within our other confiiguration file.
```hcl 
# Creating the Cloud Function
resource "google_cloudfunctions_function" "apikey-function" {
  name                  = "apikey"
  description           = "Function to retrieve API key from HashiCorp Vault"
  source_archive_bucket = google_storage_bucket.apikey-bucket.name
  source_archive_object = google_storage_bucket_object.apikey-zip.name
  timeout               = 60
  entry_point           = "F"
  trigger_http          = true
  runtime               = "python37"
  service_account_email = google_service_account.vault-auther.email
  environment_variables = {
    VAULT_ADDR = "${var.VAULT_ADDR}" # Set via TF_VAR_VAULT_ADDR environment variable
  }
}
```

Define an output for the HTTP endpoint we can use to trigger our function.
```hcl
# Output endpoint to trigger Cloud Funcion
output "http-endpoint" {
  value = google_cloudfunctions_function.apikey-function.https_trigger_url
}
```

Deploy Google Cloud Function 

    terraform init
    terraform apply -auto-approve

Invoke Cloud Funtion
curl -X POST "https://us-central1-rob-second-project.cloudfunctions.net/apikey" -H "Content-Type:application/json" --data '{"name":"Keyboard Cat"}'