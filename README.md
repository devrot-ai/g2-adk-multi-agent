# ADK Gemini Multi-Agent Assistant on Cloud Run

This mini-project implements one AI agent using **Google ADK** and **Gemini**, deployable to **Cloud Run**.
It satisfies the requirement: callable via HTTP endpoint and returns valid responses.

## Capability

- Multi-agent coordinator with three specialists:
	- Summarization
	- Text classification (topic + sentiment)
	- Grounded Q&A over provided context
- Custom tools:
	- `extractive_hint`
	- `classify_text`
	- `context_answer_support`
- Model used for inference: `gemini-2.5-flash`

## Project Structure

```text
.
├─ summarizer_agent/
│  ├─ __init__.py
│  ├─ agent.py
│  ├─ requirements.txt
│  └─ .env.example
├─ .gitignore
└─ README.md
```

## 1) Local Setup

### Prerequisites

- Python 3.10+
- Google Cloud SDK (`gcloud`) authenticated
- ADK CLI available after `pip install google-adk`

### Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r .\summarizer_agent\requirements.txt
```

Set environment variables (PowerShell example):

```powershell
$env:GOOGLE_GENAI_USE_VERTEXAI="True"
$env:GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
$env:GOOGLE_CLOUD_LOCATION="us-central1"
```

## 2) Run Locally (HTTP)

From repo root:

```powershell
adk api_server
```

By default, server runs at `http://localhost:8000`.

### Create a session

```powershell
curl -X POST http://localhost:8000/apps/summarizer_agent/users/u1/sessions/s1 -H "Content-Type: application/json" -d "{}"
```

### Call the agent

```powershell
curl -X POST http://localhost:8000/run -H "Content-Type: application/json" -d "{\"appName\":\"summarizer_agent\",\"userId\":\"u1\",\"sessionId\":\"s1\",\"newMessage\":{\"role\":\"user\",\"parts\":[{\"text\":\"Summarize: Cloud Run is a serverless platform that automatically scales stateless containers and charges only for usage.\"}]}}"
```

### More example prompts

```text
Classify this text by topic and sentiment: "ADK makes cloud deployment easier but setup can be difficult at first."
```

```text
Using this context: "Cloud Run automatically scales stateless containers and charges by usage." Answer: "Why is Cloud Run cost efficient?"
```

## 3) Deploy to Cloud Run

Set deploy variables:

```powershell
$env:GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
$env:GOOGLE_CLOUD_LOCATION="us-central1"
$env:SERVICE_NAME="adk-summarizer"
```

Deploy (ADK recommended path):

```powershell
adk deploy cloud_run --project=$env:GOOGLE_CLOUD_PROJECT --region=$env:GOOGLE_CLOUD_LOCATION --service_name=$env:SERVICE_NAME .\summarizer_agent
```

The command outputs your Cloud Run URL (submission link).

## 4) Secure Service-to-Service Authentication (IAM)

This keeps invocation private and role-based.

### Create a caller service account

```powershell
gcloud iam service-accounts create adk-caller --project $env:GOOGLE_CLOUD_PROJECT
```

### Allow caller to invoke Cloud Run service

```powershell
gcloud run services add-iam-policy-binding $env:SERVICE_NAME --region $env:GOOGLE_CLOUD_LOCATION --member "serviceAccount:adk-caller@$($env:GOOGLE_CLOUD_PROJECT).iam.gserviceaccount.com" --role "roles/run.invoker" --project $env:GOOGLE_CLOUD_PROJECT
```

### Invoke with identity token

```powershell
$SERVICE_URL = "https://YOUR_CLOUD_RUN_URL"
$TOKEN = gcloud auth print-identity-token
curl -H "Authorization: Bearer $TOKEN" "$SERVICE_URL/list-apps"
```

For strict service-to-service calls in production, generate the token from the workload identity of the caller service account.

## 5) Test Deployed Endpoint

```powershell
$SERVICE_URL = "https://YOUR_CLOUD_RUN_URL"
$TOKEN = gcloud auth print-identity-token

curl -X POST "$SERVICE_URL/apps/summarizer_agent/users/u1/sessions/s1" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "{}"

curl -X POST "$SERVICE_URL/run" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "{\"appName\":\"summarizer_agent\",\"userId\":\"u1\",\"sessionId\":\"s1\",\"newMessage\":{\"role\":\"user\",\"parts\":[{\"text\":\"Summarize: ADK enables code-first AI agents with tools and deploys cleanly to Cloud Run.\"}]}}"
```

## 6) Cleanup to Avoid Future Cost

```powershell
gcloud run services delete $env:SERVICE_NAME --region $env:GOOGLE_CLOUD_LOCATION --project $env:GOOGLE_CLOUD_PROJECT --quiet
gcloud iam service-accounts delete "adk-caller@$($env:GOOGLE_CLOUD_PROJECT).iam.gserviceaccount.com" --project $env:GOOGLE_CLOUD_PROJECT --quiet
```

If you created secrets:

```powershell
gcloud secrets delete GOOGLE_API_KEY --project $env:GOOGLE_CLOUD_PROJECT --quiet
```

## Submission Checklist

- Cloud Run service URL
- Repository link
- Evidence of successful `/run` invocation response
