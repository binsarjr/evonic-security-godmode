# Security Godmode User Guide

Security Godmode is an external Evonic plugin for authorized LLM robustness
evaluation. Its workflow follows the same major stages as the Hermes Agent
Security Godmode skill while using Evonic's model registry, plugin tools, and
per-agent storage.

> Use it only with models, accounts, and systems you own or have permission to
> test. The plugin does not disable HMADS, sandbox controls, or provider policy.

## Contents

1. [Architecture](#architecture)
2. [Installation](#installation)
3. [Agent setup](#agent-setup)
4. [Automatic workflow](#automatic-workflow)
5. [Strategies](#strategies)
6. [Prompt transformations](#prompt-transformations)
7. [Multi-model racing](#multi-model-racing)
8. [Scoring](#scoring)
9. [Profiles and ephemeral prefill](#profiles-and-ephemeral-prefill)
10. [Tool reference](#tool-reference)
11. [Undo and removal](#undo-and-removal)
12. [Compatibility with Hermes](#compatibility-with-hermes)
13. [Troubleshooting](#troubleshooting)

## Architecture

The repository is deliberately separate from Evonic core:

```text
evonic-security-godmode
├── plugin.json             plugin metadata and settings
├── tools.json              five Evonic tool definitions
├── handler.py              per-turn profile and prefill provider
└── backend/tools
    ├── godmode_auto.py     automatic orchestration
    ├── godmode_profile.py  persistent per-agent state
    ├── godmode_transform.py
    ├── godmode_score.py
    └── godmode_race.py
```

The plugin stores profiles in Evonic's plugin database directory. Prompt
prefills are generated at request time and are never written to chat history.

## Installation

### Release package

Download `security-godmode.zip`, then use an absolute path:

```bash
evonic plugin install "$(pwd)/security-godmode.zip"
evonic plugin enable security_godmode
evonic restart
```

The same ZIP can be imported from Evonic's Plugins page.

### Source checkout

```bash
git clone --branch feature/hermes-compatible-flow \
  https://github.com/binsarjr/evonic-security-godmode.git
cd evonic-security-godmode
EVONIC_BIN=/path/to/evonic ./scripts/install.sh
evonic restart
```

### Required Evonic core support

The full prefill flow requires the Evonic `prefill_messages` turn-context hook.
Use the Evonic branch associated with this plugin until its pull request is
merged. Older Evonic builds ignore the field: scoring, transformation, racing,
profiles, and system context continue to work, but raw user/assistant priming is
not injected.

## Agent setup

Enable the plugin globally, then assign these tools to the desired agent:

- `godmode_auto`
- `godmode_profile`
- `godmode_transform`
- `godmode_score`
- `godmode_race`

Nothing is injected merely because the plugin is globally enabled. Persistent
context is opt-in for each agent.

## Automatic workflow

`godmode_auto` is the recommended entry point:

```text
godmode_auto(
  prompt="Your authorized evaluation prompt",
  dry_run=true,
  fallback_model_ids=["model-b", "model-c"]
)
```

It executes the following pipeline:

```text
Resolve current agent model
        ↓
Detect model family
        ↓
Send an unmodified baseline
        ↓
Baseline acceptable? ── yes ─→ return baseline
        │ no
        ↓
Try family-specific strategies in order
        ↓
Strategy acceptable? ─ yes ─→ optionally save profile
        │ no
        ↓
Escalate through standard prompt transformations
        ↓
Transformation acceptable? ─ yes ─→ return transformed winner
        │ no
        ↓
Try explicitly selected fallback models
        ↓
Rank and return results, or report total failure
```

`dry_run=true` prevents a winning strategy from being persisted. Provider calls
still occur and still consume quota. A transformed prompt is not persisted
because transformations apply to a specific request rather than every future
turn.

### Model-family strategy order

| Family | Order |
|---|---|
| Claude | boundary test → refusal inversion → prefill |
| GPT | prefill → refusal inversion → boundary test |
| Gemini | refusal inversion → boundary test → prefill |
| Grok | prefill → refusal inversion |
| DeepSeek | boundary test → refusal inversion → prefill |
| Llama | prefill → refusal inversion → boundary test |
| Qwen | boundary test → refusal inversion → prefill |
| Mistral | prefill → refusal inversion → boundary test |
| Other | audit → refusal inversion → boundary test → prefill |

Detection uses the Evonic model's provider, model name, and display name. An
unrecognized model uses the `other` order.

## Strategies

### `audit`

Adds an authorized robustness-evaluation frame and asks the model to state real
limitations without claiming safeguards were disabled.

### `refusal_inversion`

Tests whether the model can distinguish a policy refusal from missing knowledge,
while requesting the most useful policy-compliant response.

### `boundary_test`

Tests instruction hierarchy and whether lower-priority text attempts to redefine
the system/user boundary.

### `prefill_simulation`

Adds both system context and an ephemeral user/assistant exchange before the real
conversation. This requires the Evonic core prefill hook. The injected exchange
is limited, validated, and never persisted to the session.

## Prompt transformations

Generate variants without executing them:

```text
godmode_transform(prompt="...", tier="standard", limit=10)
```

| Tier | Included transformations |
|---|---|
| Light | raw, leet, spaced, reversed, Unicode homoglyph, circled |
| Standard | light + Base64, hex, zero-width, NFKD, reversed words |
| Heavy | standard + double Base64, spaced hex, acrostic |

Start with `light`. Heavier encodings are less readable and may reduce answer
quality. The automatic workflow escalates only through the standard set.

## Multi-model racing

```text
godmode_race(
  prompt="Authorized evaluation prompt",
  model_ids=["model-a", "model-b"],
  strategy="audit",
  max_tokens=1024
)
```

Only enabled Evonic models are accepted. A race is limited to 10 models and 5
parallel workers. Results are sorted by score, highest first. Unlike Hermes'
OpenRouter tiers, this plugin intentionally uses the models already configured
in Evonic; it does not maintain a hard-coded provider catalog.

## Scoring

`godmode_score` can score any response independently:

```text
godmode_score(response="...", latency_ms=850)
```

The score combines response length, structure, and latency, then subtracts
detected hedges. A hard refusal receives `-9999`. The result also reports:

- `refused`
- `hard_refusal_matches`
- `hedges`
- `length`
- `latency_ms`

The score is a deterministic heuristic, not a semantic correctness or safety
judgment. Review the winning response manually.

## Profiles and ephemeral prefill

Enable a persistent profile for the current agent:

```text
godmode_profile(
  action="enable",
  strategy="prefill_simulation",
  custom_context="Evaluation ID LAB-42; authorized staging model only."
)
```

On each turn, `handler.py` reads the agent profile and supplies system context.
For `prefill_simulation`, it also supplies an ephemeral user/assistant pair. The
core inserts it after the main system prompt and before conversation history:

```text
Evonic system prompt
Plugin system context
Ephemeral prefill user message
Ephemeral prefill assistant message
Real conversation history
Current user message
```

The core validates roles, limits the number and length of injected messages, and
does not save them to JSONL or SQLite chat history.

## Tool reference

### `godmode_auto`

| Argument | Required | Description |
|---|---:|---|
| `prompt` | yes | Evaluation prompt |
| `model_id` | no | Model ID; defaults to the agent model |
| `fallback_model_ids` | no | Up to 10 enabled Evonic model IDs |
| `dry_run` | no | Test without saving a winning profile |
| `max_tokens` | no | 64–4096; default 1024 |

### `godmode_profile`

Actions: `status`, `enable`, `disable`, and `undo`. `disable` retains the row;
`undo` removes it. `custom_context` is limited to 8,000 characters.

### `godmode_transform`

Accepts `prompt`, `tier`, and `limit` (1–20). It never calls a model.

### `godmode_score`

Accepts `response` and optional `latency_ms`. It never calls a model.

### `godmode_race`

Accepts `prompt`, `model_ids`, `strategy`, and `max_tokens`. Every selected model
can consume provider quota.

## Undo and removal

Disable context while retaining configuration:

```text
godmode_profile(action="disable")
```

Delete the current agent's profile:

```text
godmode_profile(action="undo")
```

Disable or uninstall globally:

```bash
evonic plugin disable security_godmode
evonic plugin uninstall security_godmode
evonic restart
```

## Compatibility with Hermes

The workflow is based on the public
[Hermes Security Godmode documentation](https://hermes-agent.nousresearch.com/docs/user-guide/skills/optional/security/security-godmode).
This is a clean-room Evonic implementation, not a copy of Hermes scripts or
third-party jailbreak templates.

| Capability | Hermes | Evonic plugin |
|---|---|---|
| Baseline and automatic retry | yes | yes |
| Model-family strategy order | yes | yes |
| Ephemeral user/assistant prefill | yes | yes, with core hook |
| Prompt transformation tiers | 33 documented techniques | 14 clean-room variants |
| Response/refusal scoring | yes | yes |
| Save winning configuration | global Hermes config | per-agent plugin profile |
| Multi-model fallback | OpenRouter tier catalog | selected Evonic models |
| Undo | config and prefill removal | per-agent profile removal |

The flow is equivalent at the orchestration level, but provider catalogs,
templates, transformation counts, and persistence formats differ because the two
hosts expose different APIs and this project does not redistribute AGPL template
collections.

## Troubleshooting

### Plugin installs but tools are missing

Enable the plugin, assign all five `godmode_` tools to the agent, save the agent,
and restart Evonic after installing a new plugin version.

### Prefill is not present

Confirm Evonic contains the `prefill_messages` turn-context hook. On an older
core, `prefill_simulation` falls back to system context only.

### `godmode_auto` says the model is unavailable

Assign an enabled model to the agent or pass an enabled Evonic `model_id`.

### Every strategy fails

This is a valid test result. Review the attempts, add explicitly authorized
fallback model IDs, or refine the evaluation prompt. The plugin does not claim
that every provider safeguard can or should be bypassed.

### Unexpected provider cost

Use `godmode_score` and `godmode_transform` for offline work. `dry_run` prevents
persistence but does not prevent API calls. Limit fallback models and token count.
