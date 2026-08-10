# Upstream source manifest

Source repository: `https://github.com/NousResearch/hermes-agent`

Pinned commit: `5a3920b7344787fa1d4f0d4cec1f8cf4a445c189`

Source path used for the native Evonic port: `optional-skills/security/godmode`

| File | Git blob SHA |
|---|---|
| `scripts/auto_jailbreak.py` | `5c7055a99b99a9c7bad1d69f111f2f185caea6c1` |
| `scripts/godmode_race.py` | `dbc4510308a6c5591add19f2116ae85d6f793cac` |
| `scripts/load_godmode.py` | `71cb2f224753053fdbfc59117125d197c88e94c0` |
| `scripts/parseltongue.py` | `0b24f15501875e3b94e86613a5659b34ca399cbd` |
| `references/jailbreak-templates.md` | `c7b901986b8411be8dd42911d6365fba8d985dff` |
| `references/refusal-detection.md` | `5fb3414c541b5033a76c963078bd3853c366117c` |
| `templates/prefill.json` | `e7ff485396e13413a7d7cacedd1203f9dd4a380a` |
| `templates/prefill-subtle.json` | `a8418962bd4bd2a11ccfe9cb98085062285b2c31` |

The implementation is copied and adapted into native Evonic modules. It has no
runtime import, download, or dependency on Hermes Agent. Evonic database/profile
storage and model-provider calls replace the original filesystem configuration.
