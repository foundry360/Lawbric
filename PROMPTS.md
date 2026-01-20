# Example Prompts for Legal Discovery AI Platform

This document provides example prompts that attorneys and legal professionals can use with the Legal Discovery AI Platform. All prompts are designed to work with the source-grounded RAG system that only uses information from uploaded documents.

## General Question-Answering

### Fact-Finding Questions
- "What did the witness say about the incident on March 15th?"
- "What was the date of the contract execution?"
- "Who was present at the meeting on [specific date]?"
- "What are the key terms of the settlement agreement?"
- "What did the defendant state in their deposition regarding [topic]?"

### Document-Specific Queries
- "Summarize the key points from Document X"
- "What does the email from [sender] on [date] say about [topic]?"
- "Extract all dates mentioned in the contract"
- "What are the termination clauses in the agreement?"

## Discovery Analysis

### Document Review
- "List all privileged documents in the production"
- "Identify all documents related to [specific topic]"
- "Find all communications between [Person A] and [Person B]"
- "What documents mention [specific term or concept]?"

### Timeline Construction
- "Create a chronological timeline of all events related to [incident]"
- "List all communications in date order"
- "What happened between [date 1] and [date 2]?"
- "Show the sequence of contract negotiations"

## Legal Issue Analysis

### Issue Spotting
- "What facts support a negligence claim?"
- "Identify potential causation issues"
- "What evidence relates to damages?"
- "Find inconsistencies in witness statements"
- "What documents support the breach of contract claim?"

### Contradiction Analysis
- "Compare what [Witness A] said in their deposition versus their email"
- "Are there contradictions between the contract and the emails?"
- "What inconsistencies exist in the timeline?"

## Contract Analysis

### Clause Extraction
- "Extract all termination clauses from the contracts"
- "What are the indemnification provisions?"
- "List all payment terms"
- "What are the dispute resolution mechanisms?"

### Contract Comparison
- "Compare the terms in Contract A vs Contract B regarding [specific clause]"
- "What are the differences in termination provisions between the two agreements?"
- "How do the payment terms differ between the contracts?"

## Deposition Analysis

### Testimony Review
- "What did [witness name] say about [topic]?"
- "Summarize the key testimony from [witness]"
- "What questions were asked about [topic] in the depositions?"
- "Find all instances where the witness said [specific phrase]"

### Cross-Reference
- "How does the deposition testimony compare to the email correspondence?"
- "Are there contradictions between the deposition and the documents?"

## Entity and Person Analysis

### Entity Extraction
- "List all companies mentioned in the documents"
- "Who are the key individuals involved?"
- "What roles did [person] have in the case?"
- "Identify all parties to the agreements"

## Privilege and Confidentiality

### Privilege Identification
- "Flag all attorney-client communications"
- "Identify documents marked as confidential"
- "What documents contain privileged information?"
- "List all work product materials"

## Gap Analysis

### Missing Information
- "What information is missing from the timeline?"
- "Are there gaps in the document production?"
- "What questions remain unanswered by the documents?"

## Summary Generation

### Case Summaries
- "Provide a summary of the case facts"
- "Summarize the key issues in this matter"
- "Create an executive summary of the discovery"

### Document Summaries
- "Summarize all deposition transcripts"
- "Provide a summary of all contract documents"
- "Summarize the email correspondence"

## Best Practices

1. **Be Specific**: Include dates, names, and document references when possible
2. **Use Natural Language**: The system understands conversational queries
3. **Ask Follow-ups**: Build on previous queries for deeper analysis
4. **Verify Citations**: Always check the source citations for accuracy
5. **Combine Queries**: Use multiple queries to build a comprehensive understanding

## Important Notes

- The system will only answer based on uploaded documents
- If information is not in the documents, the system will state: "The provided documents do not contain sufficient information to answer this question."
- All answers include citations to source documents
- Confidence scores indicate how well the documents support the answer
- Always review citations to verify accuracy





