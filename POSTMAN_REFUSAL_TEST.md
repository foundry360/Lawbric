# Postman Test: Model Refusal Test

## Test Body for Postman

This test verifies that the model correctly refuses to answer when the information is not explicitly stated in the provided text.

### Copy this into Postman:

```json
{
  "prompt": "Based only on the text below, where was the witness at 10:30 PM?\n\nText:\n\"The witness stated they arrived home at 9 PM.\""
}
```

## Expected Response

The model should respond with exactly:
```
"Not found in the provided text."
```

Or a similar response indicating that the information about 10:30 PM is not available in the provided text.

## Why This Should Fail

- The text only mentions the witness arriving home at **9 PM**
- The question asks about **10:30 PM** (1.5 hours later)
- The text does not state where the witness was at 10:30 PM
- According to the system instruction, the model must respond "Not found in the provided text." when the answer is not explicitly stated

## Alternative Format (if the above doesn't work)

If you want to format it more clearly:

```json
{
  "prompt": "Text: \"The witness stated they arrived home at 9 PM.\"\n\nQuestion: Based only on the text above, where was the witness at 10:30 PM?"
}
```

## How to Test

1. Open Postman
2. Select POST request to `http://localhost:8001/query`
3. Set Headers: `Content-Type: application/json`
4. Set Body (raw JSON): Paste the test body above
5. Click Send
6. Verify the response says the information is not found




