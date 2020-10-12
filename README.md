# dpg-gcf-vault
Serverless Secrets with Google Cloud Functions and HashiCorp Vault (DevOps Playground)

## Connect local workstation to GCP 

Intialise GCloud on your local machine, you will be prompted for account and project you wish to work with.

Also add your account to the Application Default Credentials (ADC). This will allow Terraform to access these credentials to provision resources on GCloud.

    gcloud init
    gcloud auth application-default login

Define environment variables

    export GOOGLE_PROJECT=<your_project_id>
    export GOOGLE_REGION=<your_region>

Optionally if you do not wish to use application-default credential (for example you are using a service account)

    export GOOGLE_CREDENTIALS=<path_to_credentials_file> 

Enable APIs for required Google Cloud services
    
    gcloud services enable \
        iam.googleapis.com \
        cloudfunctions.googleapis.com \
        cloudbuild.googleapis.com \
        cloudresourcemanager.googleapis.com