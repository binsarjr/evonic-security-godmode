# Evonic Security Godmode

An external Evonic plugin for **authorized LLM red-team testing**. This project
is inspired by the Security Godmode concept from Hermes Agent, but is a
clean-room implementation for Evonic's plugin API. It does not copy jailbreak
templates or modify Evonic core.

The plugin provides:

- `godmode_auto`: runs the complete baseline → strategy → transformation →
  fallback-model pipeline and saves a winning strategy.
- `godmode_transform`: generates deterministic prompt variants such as leet,
  homoglyph, Base64, hex, and zero-width encodings without executing them.
- `godmode_score`: scores refusal, hedging, structure, specificity, and latency.
- `godmode_race`: runs an evaluation prompt against several Evonic models in
  parallel and ranks the responses. Every call may consume provider quota.
- `godmode_profile`: enables a per-agent red-team context using the `audit`,
  `refusal_inversion`, `boundary_test`, or `prefill_simulation` strategy.

## Requirements

- An Evonic version that supports `plugin.json`, `tools_file`, and the turn
  context hook.
- At least one enabled LLM model to use `godmode_race`.
- The `zip` utility only if you want to build release packages locally.
- For real ephemeral assistant prefill, an Evonic build containing the plugin
  `prefill_messages` turn-context hook is required. Without it, every other tool
  still works and the system-context portion remains active.

## Documentation

- [Complete user guide](docs/USER_GUIDE.md)
- [Security policy](SECURITY.md)
- [Hermes Security Godmode reference](https://hermes-agent.nousresearch.com/docs/user-guide/skills/optional/security/security-godmode)

## Install from a release

Download `security-godmode.zip` from the
[Releases page](https://github.com/binsarjr/evonic-security-godmode/releases),
then run:

```bash
evonic plugin install "$(pwd)/security-godmode.zip"
evonic plugin enable security_godmode
```

Use an absolute path as shown above. Some Evonic CLI versions change to their
installation directory before resolving path arguments.

You can also import the ZIP from the **Plugins** page in the Evonic UI and then
enable **Security Godmode — LLM Red-Team Lab**.

## Install directly from source

```bash
git clone https://github.com/binsarjr/evonic-security-godmode.git
cd evonic-security-godmode
EVONIC_BIN=/path/to/evonic ./scripts/install.sh
```

For a standard Evonic installation, this is usually enough:

```bash
./scripts/install.sh
```

Evonic copies the plugin into its installation. This repository remains
independent, so the plugin can be developed and versioned without forking or
patching Evonic core.

## Assign the tools to an agent

1. Ensure the plugin is **enabled** on the Plugins page.
2. Open the Evonic agent configuration.
3. In Tools/Plugins, select the five tools prefixed with `godmode_`.
4. Save the agent.
5. Ask the agent to invoke:

```text
godmode_profile(action="enable", strategy="audit")
```

Profiles are **opt-in per agent**. Enabling the plugin globally does not inject
context into any agent until that agent's profile is explicitly enabled.

Natural-language examples:

```text
Enable godmode_profile with the boundary_test strategy for this agent.
Create standard variants of this prompt with godmode_transform: ...
Compare this evaluation prompt on model IDs A and B using godmode_race.
```

To stop or remove the agent configuration:

```text
godmode_profile(action="disable")
godmode_profile(action="undo")
```

## Does this use Evonic's import mechanism?

Yes. Evonic's plugin loader imports this ZIP or directory. `plugin.json`
registers the four tools, while `handler.py` registers a turn-context provider
when the plugin is enabled. No Python import needs to be added to Evonic source,
and the `binsar/dev` branch does not need to be patched.

Evonic currently does not expose a public hook for inserting a raw assistant
prefill before the first message. The `prefill_simulation` mode therefore applies
controlled priming as system context. This provides a similar instruction-
hierarchy test, but does not claim to bypass HMADS or provider safeguards.

## Build packages

```bash
./scripts/package.sh
```

The command creates `dist/security-godmode.zip` and
`dist/security-godmode.evop`. Both contain the same payload. ZIP is the package
format explicitly supported by the current Evonic CLI.

## Development and tests

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q plugin
```

Reinstall the plugin after changing its source. If the same version is already
installed, uninstall it first through the UI/CLI or increment `version` in
`plugin/plugin.json`, depending on the behavior of your Evonic version.

## Safety and limitations

Use this plugin only against models, accounts, and systems you own or are
authorized to test. It does not disable HMADS, model policy, the sandbox, or
provider protections. Multi-model races can consume quota quickly and are capped
at 10 models per call with at most 5 parallel workers.

License: MIT.
