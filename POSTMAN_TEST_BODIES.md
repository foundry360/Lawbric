# Postman Test Bodies for Ollama Service

## Basic Test Bodies

### Test 1: Simple Query
Tests that the system instruction is applied and the model responds appropriately.

```json
{
  "prompt": "What is 2+2?"
}
```

**Expected Behavior:** The model should respond, but note that it's following the system instruction to use only provided text. Since no text is provided, it may say "Not found in the provided text."

---

### Test 2: Query with Document Text
Tests that the model uses only the provided text and cites verbatim.

```json
{
  "prompt": "Document text: 'The contract was signed on March 15, 2024. The payment amount is $50,000. The term is 12 months.'\n\nQuestion: What is the payment amount?"
}
```

**Expected Behavior:** The model should cite the exact text "$50,000" from the provided document text.

---

### Test 3: Query Without Answer in Text
Tests the "Not found in the provided text" response.

```json
{
  "prompt": "Document text: 'The contract was signed on March 15, 2024. The payment amount is $50,000.'\n\nQuestion: What is the contract termination date?"
}
```

**Expected Behavior:** The model should respond with exactly: "Not found in the provided text."

---

### Test 4: Legal Document Analysis
Tests legal document analysis with citation requirement.

```json
{
  "prompt": "Document text: 'Section 3.1: Confidentiality. All parties agree to maintain confidentiality of proprietary information for a period of 5 years from the date of termination. Section 3.2: Non-disclosure applies to all employees and contractors.'\n\nQuestion: What is the confidentiality period?"
}
```

**Expected Behavior:** The model should cite the exact text "5 years from the date of termination" from Section 3.1.

---

### Test 5: Multiple Questions
Tests that the model doesn't rely on outside knowledge.

```json
{
  "prompt": "Document text: 'The agreement is between Company A and Company B.'\n\nQuestion: What is the legal definition of a contract?"
}
```

**Expected Behavior:** The model should not provide a general legal definition. It should either say "Not found in the provided text" or only reference what's in the provided text.

---

### Test 6: Verbatim Citation Test
Tests that the model cites text verbatim.

```json
{
  "prompt": "Document text: 'Clause 7.3 states: \"In the event of breach, the non-breaching party may terminate this agreement with 30 days written notice.\"'\n\nQuestion: What does Clause 7.3 say about termination?"
}
```

**Expected Behavior:** The model should cite the exact text from Clause 7.3 verbatim.

---

## How to Use in Postman

1. **Open Postman** and select the "Query - Simple Question" request (or create a new POST request)

2. **Set the URL:** `http://localhost:8001/query`

3. **Set Method:** `POST`

4. **Set Headers:**
   - Key: `Content-Type`
   - Value: `application/json`

5. **Set Body:**
   - Select "raw"
   - Select "JSON" from the dropdown
   - Paste one of the test bodies above

6. **Click Send**

7. **Verify the Response:**
   - Check that the model follows the system instruction
   - Look for verbatim citations
   - Verify it says "Not found in the provided text" when appropriate
   - Confirm it doesn't provide legal advice or conclusions

---

## Expected Response Format

All responses will be in this format:

```json
{
  "response": "The model's answer here..."
}
```

The response should demonstrate that the system instruction is being followed:
- Uses only provided text
- Cites verbatim when making statements
- Says "Not found in the provided text" when answer isn't explicit
- Doesn't provide legal advice

---

## Quick Copy-Paste Examples

### Minimal Test
```json
{"prompt": "Hello"}
```

### With Document Context
```json
{"prompt": "Document: 'The meeting is scheduled for January 30, 2024.'\n\nQuestion: When is the meeting?"}
```

### Test "Not Found" Response
```json
{"prompt": "Document: 'The meeting is scheduled for January 30, 2024.'\n\nQuestion: Who is attending the meeting?"}
```




