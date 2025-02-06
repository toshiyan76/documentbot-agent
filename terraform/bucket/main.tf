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
  region  = "asia-northeast1"
}

resource "google_storage_bucket" "terraform_state" {
  name          = "documentbot-agent-tfstate"
  location      = "ASIA-NORTHEAST1"
  force_destroy = false

  versioning {
    enabled = true
  }
}
