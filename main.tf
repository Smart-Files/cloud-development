# main.tf
 
terraform {
  required_version = ">= 0.14"
 
  required_providers {
    google = ">= 3.3"
  }
}

provider "google" {
  project = "smartfile-422907"
}

resource "google_project_service" "run_api" {
  service = "run.googleapis.com"
 
  disable_on_destroy = true
}

resource "google_cloud_run_service" "run_service" {
  name = "smartfile-sever-terraform"
  location = "us-central1"
 
  template {
    spec {
      containers {
        image = "gcr.io/smartfile-422907/smartfile-server:latest"
      }
    }
  }
 
  traffic {
    percent         = 100
    latest_revision = true
  }
 
  # Waits for the Cloud Run API to be enabled
  depends_on = [google_project_service.run_api]
}


# Allow unauthenticated users to invoke the service
resource "google_cloud_run_service_iam_member" "run_all_users" {
  service  = google_cloud_run_service.run_service.name
  location = google_cloud_run_service.run_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "service_url" {
  value = google_cloud_run_service.run_service.status[0].url
}