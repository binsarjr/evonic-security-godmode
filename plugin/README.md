# Security Godmode — LLM Red-Team Lab

Native Evonic plugin for the programmatic Hermes Godmode flow.

## Important: transformation and readable responses

**Force request transform** is an escalation control, not a recommended default.
It encodes new requests and tool data using the discovered encoding, or L33T
when no encoding is saved. Some models, especially DeepSeek-family models, may
mirror that encoding in their replies and make otherwise useful output difficult
to read. Transformation can also change URLs, code, headers, hashes,
credentials, and other identifiers.

Leave **Force request transform** off unless the discovered profile requires
encoding. If Agent State reports `strategy: none_needed`, forced transformation
is unnecessary and should remain off. Responses are deliberately not decoded
automatically: substitutions such as `1` are ambiguous and decoding could
silently corrupt technical data. If encoded output appears, turn the setting off
and repeat the request in a new turn.

## Adaptive refusal recovery

Discovery checks three canaries and records `none_needed` only when every
baseline passes. Indonesian responses that provide partial analysis but withhold
the requested action under a **Batasan** section are treated as partial refusals,
so the invisible retry and optional race flow can run. A successful retry is
saved for the exact current model and reused on later turns.

With `preserve`, a `none_needed` profile remains passive until a refusal is
detected. Selecting `append` or `override` is explicit operator intent, so
readable runtime-recovery context remains active even after a baseline pass.

Preview requirement: until `anvie/evonic#103` is merged, use
`binsarjr/evonic:feature/plugin-prefill-context`, merge it into your Evonic
branch, or run `binsarjr/evonic:dev`. Stock Evonic does not yet provide every
runtime hook required by this plugin.

Enable **Godmode injection** in an agent's Plugin Settings. On the next turn the
plugin discovers and caches a profile for the exact selected model, injects
ephemeral context, transforms requests
when required, scores final responses, and performs at most two invisible retries.

No Godmode actions are exposed as agent tools. Optional ten-model Evonic racing
is controlled only by the operator and is disabled by default.

**System prompt mode** accepts `preserve` (default), `append`, or `override`.
All changes are provider-request scoped and never write `SYSTEM.md`.

Documentation:
https://github.com/binsarjr/evonic-security-godmode/blob/main/docs/USER_GUIDE.md

License: AGPL-3.0-or-later. See `LICENSE` and `NOTICE` in this package.
