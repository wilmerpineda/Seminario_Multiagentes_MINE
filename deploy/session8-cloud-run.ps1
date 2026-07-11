param(
  [Parameter(Mandatory=$true)][string]$ProjectId,
  [Parameter(Mandatory=$true)][string]$CloudSqlInstance,
  [string]$Region = "us-central1",
  [string]$Repository = "multiagent-course"
)

$ErrorActionPreference = "Stop"
gcloud.cmd config set project $ProjectId
gcloud.cmd services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com aiplatform.googleapis.com
gcloud.cmd artifacts repositories describe $Repository --location $Region 2>$null
if ($LASTEXITCODE -ne 0) { gcloud.cmd artifacts repositories create $Repository --repository-format docker --location $Region }

$ApiImage = "$Region-docker.pkg.dev/$ProjectId/$Repository/session8-bi-api:latest"
$DashboardImage = "$Region-docker.pkg.dev/$ProjectId/$Repository/session8-bi-dashboard:latest"
gcloud.cmd builds submit --region $Region --config cloudbuild.session8.yaml --substitutions "_REGION=$Region,_REPOSITORY=$Repository,_TAG=latest" .

Write-Host "Cree Cloud SQL, el usuario bi_reader y los secretos DATABASE_URL/API_KEY antes del despliegue."
gcloud.cmd run deploy session8-bi-api --image $ApiImage --region $Region --service-account "session8-api@$ProjectId.iam.gserviceaccount.com" --allow-unauthenticated --port 8080 --add-cloudsql-instances $CloudSqlInstance --set-env-vars "ENABLE_LLM=true,LLM_PROVIDER=vertex,GOOGLE_CLOUD_PROJECT=$ProjectId,GOOGLE_CLOUD_LOCATION=$Region" --set-secrets "DATABASE_URL=SESSION8_DATABASE_URL:latest,API_KEY=SESSION8_API_KEY:latest" --memory 1Gi --cpu 1 --min-instances 0 --max-instances 2 --concurrency 20 --timeout 120
$ApiUrl = gcloud.cmd run services describe session8-bi-api --region $Region --format "value(status.url)"
gcloud.cmd run deploy session8-bi-dashboard --image $DashboardImage --region $Region --service-account "session8-dashboard@$ProjectId.iam.gserviceaccount.com" --allow-unauthenticated --port 8080 --set-env-vars "BI_API_URL=$ApiUrl" --set-secrets "API_KEY=SESSION8_API_KEY:latest" --memory 1Gi --cpu 1 --min-instances 0 --max-instances 2 --concurrency 20 --timeout 120
Write-Host "API: $ApiUrl"
gcloud.cmd run services describe session8-bi-dashboard --region $Region --format "value(status.url)"
