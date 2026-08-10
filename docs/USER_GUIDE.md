# Security Godmode User Guide

Security Godmode v0.1 is a native Evonic plugin for authorized LLM robustness
evaluation. All runtime logic lives inside the plugin; it does not import or
download another agent framework.

## Architecture

```text
Agent Detail > Plugin Settings
    │
    └── Godmode injection ── model-family default (no model call)
                              │
User or agent                 │
    │
    ├── godmode_auto ───── baseline → strategies → prefill → encoding
    ├── godmode_transform  trigger detection and 11/22/33 variants
    ├── godmode_score ──── refusal, hedge, and response-quality scoring
    ├── godmode_race ───── OpenRouter catalog or Evonic registry
    └── godmode_profile ── persistent per-agent payload and undo
                              │
                              ▼
                    Evonic turn-context hook
                  system prompt + ephemeral prefill
```

The profile database is separate from chat history. Prefill messages are inserted
after the main Evonic system prompt and before real conversation history. They are
not written to SQLite chat messages or JSONL trajectories.

## Installation

### Plugin

```bash
evonic plugin install "$(pwd)/security-godmode.zip"
evonic plugin enable security_godmode
evonic restart
```

The ZIP may also be imported from Evonic's Plugins page.

### Required Evonic support

Full prefill and chat status require the generic turn-context and Agent State
summary hooks. Use the `feature/godmode-integration` branch from
`binsarjr/evonic` until the core PR is merged upstream.

### Agent configuration

Open the agent's **Settings** tab, find **Plugin Settings**, and enable
**Godmode injection**. The next turn is injected directly; the agent does not
need to select or call a tool first. The toggle is disabled by default, so
enabling the plugin globally does not alter existing agents.

Tool assignment is optional. Assign these tools only if the agent also needs to
run the corresponding actions:

- `godmode_auto`
- `godmode_transform`
- `godmode_score`
- `godmode_profile`
- `godmode_race`

`godmode_auto(dry_run=false)` and `godmode_profile(action="enable")` also turn
on direct injection for the current agent.

## Direct injection

When the per-agent toggle is enabled, the turn-context provider runs before the
model request. It uses a saved manual or auto-discovered payload when available.
Otherwise it detects the current model family and uses the first strategy that
can be injected as context, together with standard prefill. Parseltongue is
skipped for this default because it transforms a concrete query rather than
providing persistent context.

Direct activation performs no baseline, evaluation, or race request and consumes
no additional provider quota. Its payload is ephemeral: it is placed after
Evonic's main system prompt and before real history, but never saved as chat
history. Use automatic discovery when a tested model-specific winner is required.

## Automatic workflow

The default command uses the agent's selected model and built-in canary:

```text
godmode_auto(dry_run=true)
```

The flow is:

```text
Detect agent model and family
        ↓
Baseline request with no system prompt or prefill
        ↓
High-quality unhedged compliance? ─ yes → no profile needed
        │ no
        ↓
Try the family-specific strategy
        ↓ refused
Retry the same strategy with standard prefill
        ↓ refused
Try the next strategy
        ↓ all refused
Parseltongue: plain → L33T → bubble → braille → Morse
        ↓
Persist the first non-refusal winner, or report total failure
        ↓ optional
Race selected models when race_on_failure=true
```

Use a custom canary or model:

```text
godmode_auto(
  canary="Authorized evaluation prompt",
  model_id="provider/model-id",
  dry_run=false,
  max_tokens=2048
)
```

`prompt` remains accepted as an alias for `canary` for compatibility with earlier
plugin versions.

### Strategy order

| Family | Ordered strategies |
|---|---|
| Claude | boundary inversion → refusal inversion → prefill only → Parseltongue |
| GPT/OpenAI | OG GODMODE → refusal inversion → prefill only → Parseltongue |
| Gemini | refusal inversion → boundary inversion → prefill only → Parseltongue |
| Grok | unfiltered liberated → prefill only |
| Hermes/Nous | prefill only |
| DeepSeek | Parseltongue → refusal inversion → prefill only |
| Llama | prefill only → refusal inversion → Parseltongue |
| Qwen | Parseltongue → refusal inversion → prefill only |
| Mistral | prefill only → refusal inversion → Parseltongue |
| Unknown | refusal inversion → prefill only → Parseltongue |

Every normal system strategy is first tested alone and, after a refusal, retried
with the standard user/assistant prefill.

## Parseltongue transformations

Transformations affect detected trigger words rather than rewriting unrelated
parts of the query. Add domain-specific triggers with `custom_triggers`.

```text
godmode_transform(
  prompt="...",
  tier="heavy",
  limit=33,
  custom_triggers=["project-specific-term"]
)
```

### Light tier — 11

Raw, leetspeak, Unicode homoglyph, bubble, spaced, fullwidth, zero-width joiner,
mixed case, semantic replacement, dotted, and underscored.

### Standard tier — 22

Light plus reversed, superscript, small caps, Morse, Pig Latin, bracketed,
mathematical bold, mathematical italic, strikethrough, heavy leet, and hyphenated.

### Heavy tier — 33

Standard plus leet/Unicode, spaced mixed case, reversed leet, bubble spaced,
Unicode/zero-width, Base64, hex, acrostic, dotted Unicode, fullwidth mixed case,
and triple-layer encoding.

Apply one technique:

```text
godmode_transform(prompt="...", technique="mathbold")
```

Apply one of the five automatic escalation levels:

```text
godmode_transform(prompt="...", escalation_level=3)
```

Levels are `0=PLAIN`, `1=L33T`, `2=BUBBLE`, `3=BRAILLE`, and `4=MORSE`.
Transformation tools never call a model.

## Scoring

```text
godmode_score(response="...", query="original prompt", latency_ms=900)
```

Hard refusal patterns immediately produce `-9999`. Otherwise the score combines:

- answer length and structure;
- code blocks, commands, tables, headers, lists, formulas, and concrete numbers;
- technical/domain terms and query-keyword relevance;
- penalties for disclaimers, hedges, deflection, filler, repetition, and
  meta-commentary.

The result exposes the current names (`is_refusal`, `hedge_count`) and legacy
aliases (`refused`, `hedges`). Scoring is deterministic and should not be treated
as a semantic truth or safety judgment.

## Multi-model racing

### Enabled Evonic models

```text
godmode_race(
  prompt="...",
  backend="evonic",
  tier="standard",
  model_ids=["model-a", "model-b"]
)
```

If `model_ids` is omitted, all enabled Evonic models are eligible. Tier sizes cap
the selected list at 10, 24, 38, 49, or 55. Responses are sent in parallel and
ranked with the same scoring engine.

### Original OpenRouter catalog

Configure and enable the OpenRouter provider in Evonic, then run:

```text
godmode_race(
  prompt="...",
  backend="openrouter",
  race_type="ultraplinian",
  tier="ultra",
  max_workers=10,
  timeout=60
)
```

Tier sizes:

| Tier | Models |
|---|---:|
| FAST | 10 |
| STANDARD | 24 |
| SMART | 38 |
| POWER | 49 |
| ULTRA | 55 |

The 55-model catalog is embedded in the plugin. Provider credentials are read
from Evonic's provider database and are never returned in tool output.

### GODMODE Classic

```text
godmode_race(
  prompt="...",
  backend="openrouter",
  race_type="classic"
)
```

Classic mode races five model/template pairs: Claude 3.5 Sonnet, Grok 3, Gemini
2.5 Flash, GPT-4o, and Hermes 4 405B.

Every race consumes provider quota. `dry_run` belongs to automatic discovery and
does not make a race free.

## Persistent profiles

Inspect the current agent:

```text
godmode_profile(action="status")
```

The saved payload contains:

- strategy name;
- exact system prompt;
- exact prefill message array;
- winning encoding label;
- detected model family;
- administrator context;
- pinned source revision.

Status also reports:

- `activation_enabled` — current per-agent toggle state;
- `payload_source` — `default`, `manual`, or `auto-discovered`;
- `effective_strategy` and `effective_model_family`;
- `last_context_provided_at`, `last_session_id`, and
  `context_provided_count`.

`last_context_provided_at` means the plugin handed a valid payload to Evonic's
turn-context hook. It is intentionally not a separate post-application receipt.
The same values appear as `security_godmode` under **Agent State → Plugin
States** in the chat frontend. This is a display-only Evonic plugin summary; it
does not create a workflow gate or add state text to the model prompt.

Disable injection while retaining the payload:

```text
godmode_profile(action="disable")
```

Delete it completely:

```text
godmode_profile(action="undo")
```

Existing enabled profiles are migrated to the per-agent toggle when first read.
An explicit administrator toggle always takes precedence.

## Failure modes

### OpenRouter provider is not configured

Use `backend="evonic"`, or configure the OpenRouter provider and API key. The
plugin does not accept or log API keys as tool arguments.

### All strategies fail

This is a valid result. Inspect `attempts`, test a different authorized canary,
or enable race fallback. Provider safeguards and model updates can invalidate
previously effective strategies.

### Prefill is absent from normal turns

Verify the Evonic core contains the generic prefill hook, the plugin is enabled,
and **Godmode injection** is enabled in the agent's Plugin Settings. Then inspect
`godmode_profile(action="status")`: `activation_enabled` should be true and
`context_provided_count` should increase after a turn.

### Provider cost is too high

Use transformation/scoring offline, restrict `model_ids`, select FAST, lower
`max_tokens`, or leave `race_on_failure=false`.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q plugin
./scripts/package.sh
```

The installable ZIP includes its AGPL license and attribution notice. See the
repository `UPSTREAM.md` for the pinned source hashes used during the native port.
