# Evonic Security Godmode

Native Evonic plugin for authorized LLM robustness and red-team evaluation.
Version 0.1.4 ports the complete Security Godmode workflow into Evonic without a
runtime dependency on another agent framework.

## Features

- Automatic baseline and model-family strategy selection.
- Direct per-agent injection without an agent tool call.
- Fail-closed per-agent authorization records with scope and expiry.
- Automatic request transformation for discovered Parseltongue profiles.
- Optional per-agent forced request transformation with saved encoding or L33T.
- Strategy-only and strategy-plus-prefill retries.
- Real ephemeral user/assistant prefill through Evonic's plugin context hook.
- Parseltongue trigger detection, 33 techniques, and five escalation levels.
- Full hard-refusal, hedge, quality, and relevance scoring.
- Five GODMODE Classic model/template combinations.
- ULTRAPLINIAN FAST/STANDARD/SMART/POWER/ULTRA tiers with all 55 models.
- OpenRouter catalog mode and dynamic Evonic model-registry mode.
- Complete per-agent winner persistence, disable, and undo.
- Chat Agent State receipts for context injection and request transformation.

## Documentation

- [Complete user guide](docs/USER_GUIDE.md)
- [Security policy](SECURITY.md)
- [Source and attribution manifest](UPSTREAM.md)

## Requirements

- Evonic with the generic prefill turn-context and Agent State summary hooks.
  Until the upstream PR is merged, use
  `binsarjr/evonic:feature/plugin-prefill-context` (clean integration branch),
  or `binsarjr/evonic:dev` for the aggregate development branch.
- One enabled Evonic model for automatic evaluation.
- An enabled OpenRouter provider with an API key for the original 55-model and
  five-model Classic races. Evonic-registry races do not require OpenRouter.

## Install

Download `security-godmode.zip` from Releases and use an absolute path:

```bash
evonic plugin install "$(pwd)/security-godmode.zip"
evonic plugin enable security_godmode
evonic restart
```

Or install from source:

```bash
git clone --branch feature/hermes-compatible-flow \
  https://github.com/binsarjr/evonic-security-godmode.git
cd evonic-security-godmode
EVONIC_BIN=/path/to/evonic ./scripts/install.sh
evonic restart
```

In the agent's **Settings** tab, open **Plugin Settings** and enable **Godmode
injection**. The next turn receives a model-family system prompt and ephemeral
prefill without calling a tool, but only after **Authorization confirmed**,
**Authorization scope**, **Authorized by**, and a future ISO-8601
**Authorization expiry** are all set. Enable **Force request transform** only
when every new user request should also be transformed before it reaches the model.
Assign the five `godmode_` tools only when the agent also needs discovery,
manual transformation, scoring, profile, or racing actions.

## Quick start

The direct toggle is quota-free. An incomplete or expired authorization record
blocks injection, transformation, discovery, and racing. Until automatic discovery saves a winner, the
plugin detects the selected model family and applies its first directly
injectable strategy with standard prefill.

The chat frontend shows authorization validity, scope and expiry, activation,
strategy source, model-family compatibility,
transform mode and encoding, plus the latest context and transformation receipts
under **Agent State → Plugin States**.

Run automatic discovery without saving:

```text
godmode_auto(dry_run=true)
```

Run it and persist the winning system prompt, prefill, and encoding profile:

```text
godmode_auto(dry_run=false)
```

Generate all prompt variants without calling a model:

```text
godmode_transform(prompt="...", tier="heavy", limit=33)
```

Race enabled Evonic models:

```text
godmode_race(prompt="...", backend="evonic", tier="ultra")
```

Run the original 55-model OpenRouter catalog:

```text
godmode_race(
  prompt="...",
  backend="openrouter",
  race_type="ultraplinian",
  tier="ultra"
)
```

Remove the saved profile:

```text
godmode_profile(action="undo")
```

## Build and test

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q plugin
./scripts/package.sh
```

## License

AGPL-3.0-or-later. See `NOTICE` and `UPSTREAM.md` for attribution and the pinned
source revision.
