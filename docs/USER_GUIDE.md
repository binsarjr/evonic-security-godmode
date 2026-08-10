# Security Godmode User Guide

Security Godmode v0.1.9 is a native Evonic implementation of the Hermes Godmode
flow. All orchestration runs in program hooks. The agent is not given a
Godmode tool and cannot decide when discovery, transformation, scoring, retry,
profile persistence, or racing runs.

## Architecture

```text
Operator settings
    ├── activation
    ├── automatic discovery + one-shot refresh
    ├── preserve | append | override
    ├── optional forced request transform
    └── optional race after retry exhaustion
                    │
                    ▼
First active turn / model change
    baseline → family strategy ladder → prefill → Parseltongue → cached profile
                    │
                    ▼
Normal turn
    context → newest-user transform → provider
                                      │
                                      ▼
                    refusal score before chat output
                         ├── accepted → final response
                         └── refused → up to two program-selected retries
                                           └── optional Evonic fast race
```

The profile database is separate from chat history. System context, prefill, and
retry messages are ephemeral. Rejected responses are not saved as chat messages
or shown as intermediate bubbles. Existing provider usage/archive facilities may
still account for every provider request.

## Installation

```bash
evonic plugin install "$(pwd)/security-godmode.zip"
evonic plugin enable security_godmode
evonic restart
```

The package may also be imported from Evonic's Plugins page.

> **Preview compatibility:** the required generic core hooks are not yet in
> upstream Evonic. Until
> [anvie/evonic#103](https://github.com/anvie/evonic/pull/103) is merged, run
> `binsarjr/evonic:feature/plugin-prefill-context`, merge that branch into your
> own Evonic branch, or use the aggregate `binsarjr/evonic:dev` branch. The
> plugin can be installed on stock Evonic, but its complete runtime flow will
> not be available.

## Agent configuration

Open **Agent Settings → Plugin Settings**. Enabling the plugin globally does not
alter an agent until **Godmode injection** is enabled for that agent.

### Runtime settings

| Setting | Default | Behavior |
|---|---:|---|
| Godmode injection | Off | Enables the program flow for this agent. |
| Automatic profile discovery | On | Tests once for the exact current model before its first active turn. |
| Rediscover on next turn | Off | Forces one discovery attempt, then resets itself. |
| Force request transform | Off | Uses the saved encoding or L33T on each newest user request. |
| Race models after retries fail | Off | After two refusals, races up to ten other enabled Evonic models. |
| System prompt mode | `preserve` | Controls how Godmode system context relates to Evonic's compiled prompt. |

Racing consumes quota for every selected model. It is never activated by chat
instructions and does not use OpenRouter in the automatic runtime flow.

### System prompt modes

| Mode | Provider-bound behavior |
|---|---|
| `preserve` | Leaves Evonic's compiled system prompt unchanged and supplies only ephemeral prefill. |
| `append` | Keeps Evonic's compiled prompt and appends Godmode context. |
| `override` | Replaces the compiled prompt for that provider request only. |

Invalid values fall back to `preserve`. None of the modes writes, deletes, or
rewrites the agent's `SYSTEM.md`. `override` intentionally removes compiled tool,
knowledge, and agent instructions from that request, so use it only when desired.

## Automatic discovery

Discovery blocks the first active turn so that its normal request immediately
uses a tested profile. It runs again when the exact model ID changes or when the
operator sets **Rediscover on next turn**.

The program performs:

```text
Detect exact model and family
        ↓
Baseline canary without Godmode context
        ↓ refused
Family strategy without prefill
        ↓ refused
Same strategy with prefill
        ↓ refused
Next family strategy
        ↓
Parseltongue PLAIN → L33T → BUBBLE → BRAILLE → MORSE
        ↓
Persist winner, none-needed result, or failure receipt
```

A successful profile, `none_needed`, or an all-failed result is cached against
the exact model ID and plugin source version. Cached failures use the family
default and do not repeat on every chat turn; change model or request a one-shot
refresh to test again. Concurrent sessions share one discovery lock per agent.

### Strategy order

| Family | Order |
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

Winning system prompts and prefill messages are injected unchanged from the
Hermes-compatible strategy payload.

## Request transformation

Transformation happens after Evonic assembles normal context but before the
provider request. Only the newest user text is transformed; older history and
non-text media remain unchanged.

A discovered Parseltongue profile activates its saved encoding automatically.
The force toggle uses that encoding when available and otherwise L33T. During a
live refusal retry the program restores the original newest text, applies the
candidate encoding, then constructs the revised provider request. This avoids
stacking encodings across attempts.

The implementation retains all 33 Parseltongue techniques:

- Light: raw, leetspeak, Unicode homoglyph, bubble, spaced, fullwidth,
  zero-width joiner, mixed case, semantic replacement, dotted, underscored.
- Standard: light plus reversed, superscript, small caps, Morse, Pig Latin,
  brackets, math bold, math italic, strikethrough, heavy leet, hyphenated.
- Heavy: standard plus leet-Unicode, spaced-mixed, reversed-leet,
  bubble-spaced, Unicode-ZWJ, Base64 hint, hex, acrostic, dotted-Unicode,
  fullwidth-mixed, and triple-layer.

The automatic escalation ladder deliberately uses only PLAIN, L33T, BUBBLE,
BRAILLE, and MORSE, matching the discovery flow. The other transformations remain
internal library capabilities rather than agent actions.

## Response scoring and retries

The pre-final response handler runs only on a final response with no tool calls.
Tool-call and intermediate assistant messages continue through Evonic normally.

Hard refusal patterns receive `-9999`. Other responses are scored using hedge
penalties, useful length, structure, code blocks, specificity, actionable detail,
and query relevance.

When the initial response is a hard refusal:

1. Continue after the active profile in the current model-family ladder.
2. Rebuild the request with the next candidate and selected system-prompt mode.
3. Skip candidates whose effective payload is identical.
4. Stop at the first non-refusal or after two retries.
5. If all attempts refuse, return the highest-scoring attempt; the newest wins a tie.

Only the selected final response is emitted and saved. The Agent State and final
timeline record strategy, score, and attempt count without storing rejected
response bodies in the plugin database.

## Optional Evonic race

If **Race models after retries fail** is enabled, racing begins only after the
initial response and both progressive retries refuse.

- Uses up to ten other enabled models from Evonic's model registry.
- Excludes the current model because it has already been attempted.
- Selects family context independently for each target model.
- Uses configured Evonic provider credentials without accepting keys as arguments.
- Returns the best non-refusal race response; otherwise retains the best normal attempt.

If there are no alternate enabled models, Agent State reports the race as
unavailable and the normal exhausted result is returned.

## Agent State

The chat frontend displays `security_godmode` under
**Agent State → Plugin States**. Important fields include:

- activation and profile source;
- profile source, strategy, model family, current and tested model IDs;
- `system_prompt_mode`, transform mode, encoding, and force-transform state;
- `discovery_state`, `discovery_model_id`, and `last_discovery_at`;
- `response_retry_state`, `response_attempt_count`, `last_response_score`,
  `last_response_refused`, and `last_retry_strategy`;
- `race_state`;
- latest context and transformation receipts.

Discovery states are `idle`, `discovering`, `ready`, `none_needed`, or `failed`.
Retry states are `inactive`, `not_needed`, `retrying`, `recovered`, `exhausted`,
or `raced`. The state panel is read-only; enforcement occurs in the plugin hooks.

## Hermes compatibility

Hermes's optional Godmode skill documents loading `auto_jailbreak()` through
`execute_code`. Once invoked, its Python program chooses and tests strategies,
then writes the winning prompt and prefill to configuration. Normal Hermes chat
responses are not automatically scored and retried.

Evonic v0.1.9 keeps the strategy order, canary discovery, scoring, prefill,
Parseltongue escalation, and profile persistence, but adapts their lifecycle:

- no `execute_code` or agent-selected Godmode tool is required;
- discovery is triggered by active runtime state;
- context and transformation are request-scoped rather than config-file edits;
- final refusals receive up to two automatic retries;
- optional racing is an operator setting and uses the Evonic registry;

See the upstream reference:
https://hermes-agent.nousresearch.com/docs/user-guide/skills/optional/security/security-godmode

## Troubleshooting

### Discovery is slow

The first active turn intentionally waits for the canary ladder. Later turns
reuse its exact-model cache. Do not enable one-shot rediscovery unless a provider
or model changed.

### Request is not transformed

Check `transform_mode` and `encoding`. `profile` requires a discovered
Parseltongue winner; `forced` requires **Force request transform**. PLAIN may run
successfully without changing visible text.

### Response was not retried

Retries are triggered only by a hard-refusal match on a final no-tool response.
Soft hedges reduce the score but do not by themselves cause another provider call.

### Provider cost is high

Leave racing disabled. Normal live recovery adds at most two provider calls, while
discovery is cached for the exact model.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q plugin
./scripts/package.sh
```

The package includes the AGPL license and attribution notice. See `UPSTREAM.md`
for pinned source hashes.
