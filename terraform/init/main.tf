terraform {
  required_version = "~> 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
}

# Artifact Registry
resource "google_artifact_registry_repository" "repo" {
  location      = var.location
  repository_id = var.artifact_registry_repository_id
  format        = "DOCKER"
}

# Service Account for Operation
resource "google_service_account" "operation_account" {
  account_id   = var.operation_sa_id
  display_name = var.operation_sa_display_name
}

# Service Account for Build
resource "google_service_account" "build_account" {
  account_id   = var.build_sa_id
  display_name = var.build_sa_display_name
}

# IAM
resource "google_project_iam_member" "operation_account_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/artifactregistry.reader"
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.operation_account.email}"
}

resource "google_project_iam_member" "build_account_roles" {
  for_each = toset([
    "roles/run.developer",
    "roles/artifactregistry.writer"
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.build_account.email}"
}

# Workload Identity Pool
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = var.workload_identity_pool_id
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = var.workload_identity_provider_id
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "pool_impersonation" {
  service_account_id = google_service_account.build_account.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repo_owner}/${var.github_repo_name}"
}

# Output
output "build_service_account_email" {
  value = google_service_account.build_account.email
}

output "operation_service_account_email" {
  value = google_service_account.operation_account.email
}

output "workload_identity_provider_name" {
  value = "${google_iam_workload_identity_pool.github_pool.name}/providers/${google_iam_workload_identity_pool_provider.github_provider.workload_identity_pool_provider_id}"
} 