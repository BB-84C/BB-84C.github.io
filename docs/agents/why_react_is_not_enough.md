# Why ReAct Is Not Enough

ReAct (reasoning + acting) is a useful baseline, but it often fails in real systems without explicit state, constraints, and evaluation loops.

## Missing pieces in practice

- Durable memory with clear read/write semantics
- Explicit plans and step budgets
- Guardrails: schemas, validators, sandboxing
- Feedback: tests, critiques, automated checks

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class StepBudget:
    max_steps: int = 12
    max_tool_calls: int = 20
```

