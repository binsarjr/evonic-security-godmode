# Evonic Security Godmode

Native Evonic plugin for authorized LLM robustness and red-team evaluation.
Version 0.1.7 runs the complete decision flow inside the program; it exposes no
Godmode tools to the agent and has no runtime dependency on another framework.

## Features

- Blocking profile discovery on the first authorized turn and after model changes.
- Program-selected model-family strategies, prefill, and Parseltongue encoding.
- Pre-provider transformation of only the newest user message.
- Pre-final refusal scoring and up to two invisible progressive retries.
- Optional operator-controlled race across ten other enabled Evonic models.
- Exact-model profile caching, manual refresh, and additive runtime receipts.
- Fail-closed authorization with exact scope, approver, and expiry.
- `preserve`, `append`, and request-scoped `override` system-prompt modes.
- Agent State visibility for discovery, injection, transformation, retries, and race.
- No writes to an agent's `SYSTEM.md`.

## Documentation

- [Complete user guide](docs/USER_GUIDE.md)
- [Security policy](SECURITY.md)
- [Source and attribution manifest](UPSTREAM.md)

## Requirements

- Evonic with the generic turn-context, user-transform, Agent State, and
  pre-final response-handler hooks. Until the upstream PR is merged, use
  `binsarjr/evonic:feature/plugin-prefill-context`, or `binsarjr/evonic:dev` for
  the aggregate development branch.
- At least one enabled Evonic model. Optional racing needs another enabled model.

## Install

Download `security-godmode.zip` from Releases:

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

In **Agent Settings → Plugin Settings**, complete the authorization record and
enable **Godmode injection**. The next turn performs discovery before the normal
provider request. Leave **System prompt mode** at `preserve` to keep the compiled
Evonic prompt unchanged. **Race models after retries fail** is disabled by
default because every raced model consumes quota.

The agent never selects or invokes a Godmode tool. The program applies this flow:

```text
authorization → cached discovery/profile → context + request transform
              → provider → refusal score → at most two retries
              → optional ten-model Evonic race → one visible final response
```

Hermes's optional skill starts `auto_jailbreak()` through `execute_code`; this
Evonic port moves that orchestration into native hooks. See the user guide for
the exact compatibility differences.

## Build and test

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q plugin
./scripts/package.sh
```

## License

AGPL-3.0-or-later. See `NOTICE` and `UPSTREAM.md` for attribution and the pinned
source revision.
