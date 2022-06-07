terraform {
  required_providers {
    github = {
      source = "integrations/github"
      version = "4.26.0"
    }
  }
}

provider "github" {
  # Configuration options
}


resource "github_repository" "devops-labs" {
  name        = "devops-labs"
  description = "Solutions to DevOps labs"
  visibility = "public"
  auto_init = true
}


resource "github_branch_default" "default"{
    repository = github_repository.devops-labs.name
    branch     = master
}

resource "github_branch" "lab4" {
    repository = github_repository.devops-labs.name
    branch     = "lab4"
}

resource "github_branch_protection_v3" "protection" {
  repository     = github_repository.devops-labs.name
  branch         = "lab4"

  restrictions {
    users = ["zlldnv"]
  }
}
