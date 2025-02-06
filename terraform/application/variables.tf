variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "docker_image_web" {
  type = string
}

variable "docker_image_api" {
  type = string
}

variable "service_account" {
  type = string
}

variable "openai_api_key" {
  type = string
  sensitive = true
} 