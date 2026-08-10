# Security Godmode — LLM Red-Team Lab

Native Evonic plugin for the programmatic Hermes Godmode flow.

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
