# Vertex AI Agent Builder (Discovery Engine) RAG

Grounded Q&A against a Vertex AI Search / Agent Builder **data store**, billed on
Agent Builder product credits — **not** Gemini API Studio or Vertex AI prediction.

## Env

```bash
PROJECT_ID=your-gcp-project
LOCATION=global          # or us, eu, us-central1 (regional API endpoint)
DATA_STORE_ID=your-data-store-id
# Prefer a Search app when using answer_query:
ENGINE_ID=your-search-app-id
```

Auth: Application Default Credentials (`gcloud auth application-default login`)
or the Cloud Run runtime service account with
`roles/discoveryengine.viewer` (or editor) on the data store / engine.

## Python helper

```python
from app.services.discovery_engine import query_knowledge_base

result = query_knowledge_base("What is our revision policy?")
print(result.answer)
for c in result.citations:
    print(c.title, c.uri, c.snippet)
```

## HTTP

```bash
# Status (no Google call)
curl -s -H "Authorization: Bearer $TOKEN" \
  "$API/api/v1/knowledge/status"

# Grounded query
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is our revision policy?"}' \
  "$API/api/v1/knowledge/query"
```

## Dependency

```text
google-cloud-discoveryengine>=0.13.0
```

Listed in `backend/pyproject.toml` and `backend/requirements-discoveryengine.txt`.

## Notes

- Existing keyword `project_templates` RAG (`app.services.rag`) is unchanged.
- Do **not** call this path via `google-generativeai` / `google-cloud-aiplatform`.
- For best `answer_query` results, create a **Search app (engine)** in Agent Builder
  that points at your data store and set `ENGINE_ID`.
