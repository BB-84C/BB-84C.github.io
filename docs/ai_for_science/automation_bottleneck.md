# Automation Bottleneck

Many AI-for-science workflows bottleneck on automation, not model capability: data movement, provenance, experiment orchestration, and reliable evaluation.

## A simple checklist

- Inputs are versioned (data + prompts + code)
- Runs are reproducible (configs + seeds + environments)
- Results are queryable (metadata + artifacts)
- Failures are observable (logs + traces)

```mermaid
sequenceDiagram
  participant R as Researcher
  participant O as Orchestrator
  participant C as Compute
  R->>O: define experiment
  O->>C: run sweep
  C-->>O: metrics + artifacts
  O-->>R: report + provenance
```

