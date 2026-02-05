# Test Queries for Query Panel - LLaMA-3.1 8B

## Simple Test Query (UI)
Use this in the Query panel input field:

```
What are the key facts mentioned in the documents?
```

## Legal Document Analysis Query
```
Extract all factual statements about dates, locations, and parties involved from the provided documents.
```

## Specific Information Query
```
What did the witness say about the incident on March 15th?
```

## Document Summary Query
```
Summarize the main points discussed in the contract.
```

## Timeline Query
```
List all events mentioned in chronological order.
```

---

## Direct API Test (Postman/cURL)

### Test Query via Ollama Service (Port 8001)

**POST** `http://localhost:8001/query`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "prompt": "What are the key facts mentioned in the documents?"
}
```

### Test Query via Main Backend (Port 9001)

**POST** `http://localhost:9001/api/v1/queries`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <your-jwt-token>
```

**Body:**
```json
{
  "question": "What are the key facts mentioned in the documents?",
  "case_id": 1,
  "max_citations": 5
}
```

---

## cURL Examples

### Direct Ollama Service Test
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are the key facts mentioned in the documents?"
  }'
```

### Main Backend Test (with auth)
```bash
curl -X POST http://localhost:9001/api/v1/queries \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "question": "What are the key facts mentioned in the documents?",
    "case_id": 1,
    "max_citations": 5
  }'
```

---

## Expected Response Format

### From Ollama Service:
```json
{
  "response": "- Page 1: \"The contract was signed on January 1st, 2024.\"\n- Page 2: \"The agreement term is 12 months.\"",
  "documents": null
}
```

### From Main Backend:
```json
{
  "id": 123,
  "question": "What are the key facts mentioned in the documents?",
  "answer": "- Page 1: \"The contract was signed on January 1st, 2024.\"\n- Page 2: \"The agreement term is 12 months.\"",
  "citations": [],
  "confidence_score": null,
  "query_type": null,
  "created_at": "2024-01-30T15:00:00Z"
}
```




