# RAG Is Not Learning

Retrieval-Augmented Generation (RAG) improves answers by providing relevant context at inference time. That is not the same thing as learning: the model parameters do not change.

## A minimal decomposition

```text
RAG = retrieval (index + query) + conditioning (prompt) + generation (decode)
Learning = parameter update (gradient-based or otherwise) + generalization
```

## Practical implication

If the index is stale, your “knowledge” is stale. If prompts change, behavior changes. Treat RAG as a *data plumbing* problem, not a training substitute.

