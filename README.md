# Next.js + FastAPI

This is a [Next.js](https://nextjs.org/) project bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app), combined with a FastAPI backend.

## Getting Started

First, run the development server:

```bash
# Install dependencies
cd frontend
npm install
cd ../backend
pip install -r requirements.txt

# Run the development servers
cd frontend
npm run dev
# in another terminal
cd backend
uvicorn main:app --reload
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `frontend/app/page.tsx`. The page auto-updates as you edit the file.

The FastAPI server will be running on [http://localhost:8000](http://localhost:8000).

## Deployment to Cloud Run

The application is configured for deployment to Google Cloud Run using Cloud Build. Here are the key components:

### Prerequisites

1. Google Cloud Project setup with required APIs enabled:
   - Cloud Run
   - Cloud Build
   - Secret Manager
   - Artifact Registry

2. Required environment variables stored in Secret Manager:
   - `openai_api_key`
   - `langchain_tracing_v2`
   - `langchain_endpoint`
   - `langchain_api_key`
   - `langchain_project`
   - `cors_origins`

### Service Accounts

The deployment process involves several service accounts:

1. Cloud Build Service Account (`[PROJECT_NUMBER]@cloudbuild.gserviceaccount.com`)
   - Handles the build and deployment process

2. Cloud Run Runtime Service Account
   - Used by the running application to access GCP resources
   - Requires the `Secret Manager Secret Accessor` role
   - **Note**: After granting IAM roles, it may take a few minutes for the changes to propagate
   - If deployment fails due to permissions, try waiting for 5-10 minutes and deploy again

3. Cloud Run Service Agent
   - Manages Cloud Run infrastructure

### Deployment Process

1. Push changes to the repository
2. Cloud Build automatically triggers the build process
3. Containers are built and pushed to Artifact Registry
4. Cloud Run service is updated with the new containers

The deployment configuration is defined in `cloudbuild.yaml`.