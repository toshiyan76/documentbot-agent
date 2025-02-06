locals {
  service_name = "documentbot-agent-service"
}

terraform {
  required_version = "~> 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "gcs" {
    bucket = "documentbot-agent-tfstate"
    prefix = "application/terraform"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_cloud_run_v2_service" "my-service" {
  name                = local.service_name
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    containers {
      name       = "web"
      image      = var.docker_image_web
      depends_on = ["app"]
      ports {
        container_port = 3000
      }
      startup_probe {
        timeout_seconds = 120
        period_seconds  = 10
        tcp_socket {
          port = 3000
        }
      }
    }

    containers {
      name  = "app"
      image = var.docker_image_api
      startup_probe {
        timeout_seconds = 120
        period_seconds  = 10
        tcp_socket {
          port = 8080
        }
      }
      env {
        name  = "OPENAI_API_KEY"
        value = var.openai_api_key
      }
    }
    service_account = var.service_account
    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }
  }
}
          value = google_cloud_run_service.backend.status[0].url
        }
      }
    }
  }
}

# IAM
data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "backend_noauth" {
  location = google_cloud_run_service.backend.location
  project  = google_cloud_run_service.backend.project
  service  = google_cloud_run_service.backend.name

  policy_data = data.google_iam_policy.noauth.policy_data
}

resource "google_cloud_run_service_iam_policy" "frontend_noauth" {
  location = google_cloud_run_service.frontend.location
  project  = google_cloud_run_service.frontend.project
  service  = google_cloud_run_service.frontend.name

  policy_data = data.google_iam_policy.noauth.policy_data
}

# Output
output "backend_url" {
  value = google_cloud_run_service.backend.status[0].url
}

output "frontend_url" {
  value = google_cloud_run_service.frontend.status[0].url
} 