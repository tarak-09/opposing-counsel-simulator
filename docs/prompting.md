# Prompting And Model Adapters

## Philosophy

The system avoids one giant "analyze this contract" prompt. Each model task is narrow, schema-constrained, and replaceable:

- semantic change summarization
- issue classification fallback
- clause simulation
- critique / validation

## Prompt Assets

Prompt templates live in:

- [packages/prompts/semantic_change.md](../packages/prompts/semantic_change.md)
- [packages/prompts/issue_classification.md](../packages/prompts/issue_classification.md)
- [packages/prompts/clause_simulation.md](../packages/prompts/clause_simulation.md)
- [packages/prompts/simulation_critic.md](../packages/prompts/simulation_critic.md)

## Provider Abstraction

Backend model adapters live in:

- [apps/api/app/llm/provider.py](../apps/api/app/llm/provider.py)

Implemented paths:

- `OpenAICompatibleReasoningProvider`
- `OpenAICompatibleEmbeddingProvider`
- `HashEmbeddingProvider` deterministic fallback

## Why JSON-Only

Every AI reasoning task validates against a Pydantic schema before persistence. This keeps the workflow deterministic enough for product surfaces such as:

- decision badges
- stance strength
- counterproposal text
- evidence grounding
- scoring handoff

## Retry / Validation Strategy

- hosted reasoning calls retry up to three times on malformed or empty structured output
- primary generation attempts strict JSON output
- Pydantic validation enforces shape
- critique pass repairs weak or contradictory outputs
- max repair attempts: `2`
- final fallback is safe escalation-oriented output rather than infinite looping

## Swapping Providers

Set these environment variables:

- `LLM_PROVIDER`
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `EMBEDDING_PROVIDER`
- `EMBEDDING_API_KEY`
- `EMBEDDING_BASE_URL`
- `EMBEDDING_MODEL`

The current implementation assumes an OpenAI-compatible API shape for hosted providers, but the provider boundary is isolated so additional providers can be added without changing the orchestration layer.

## Guardrails

- deterministic heuristics run first where feasible
- persona is structured data, not freeform prose
- evidence is passed in explicitly
- outputs are framed as negotiation simulation, not legal advice
