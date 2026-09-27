# dpdpkit-policies

Versioned policy packs for India's Digital Personal Data Protection Act, 2023 and the DPDP Rules, 2025.
Every legal number that [dpdpkit](https://github.com/dpdpkit-dev) uses lives here. Examples are the 48-hour
pre-erasure warning, the one-year log floor and the 90-day grievance ceiling. None of them are in code.

> **Disclaimer.** dpdpkit is software that helps you implement obligations under India's Digital Personal
> Data Protection Act, 2023 and the DPDP Rules, 2025. It does not provide legal advice and does not
> guarantee compliance. Decisions about notices, purposes, retention and incident reporting must be made
> by you or your counsel.

## Install

Installed automatically with `pip install dpdpkit`. On its own:

```bash
pip install dpdpkit-policies
```

## Use

```python
from dpdpkit_policies import load_pack

pack = load_pack("dpdp-rules-2025.v1", overlays=[])
pack["retention"]["erasure_pre_notice_hours"]  # 48
```

```bash
dpdpkit-policies list
dpdpkit-policies validate                 # every shipped pack and overlay
dpdpkit-policies validate my-pack.yaml    # your own file
dpdpkit-policies rule-map --format md     # rule-to-code table for the docs site
```

## Versioning

- **Pack ids** (`dpdp-rules-2025.v1`, `.v2`…) change when the law or its numbers change. A pack is never
  edited after release; a new version is added instead.
- **The package** uses CalVer (`2026.10.0`) and is released independently of dpdpkit's code packages, so a
  rule change ships without a code release.

## Rule-change process

1. Watch official sources: MeitY notifications, the eGazette, the Data Protection Board website.
2. Open an issue with the `rule-change` label linking the official text.
3. Numbers only changed → new pack version + new release of this package. No code release.
4. New obligation → feature added to `dpdpkit-core` behind a flag, then enabled by the new pack.
5. Every `CHANGELOG.md` entry cites the notification.

## Pack format

See [`src/dpdpkit_policies/packs/dpdp-rules-2025.v1.yaml`](src/dpdpkit_policies/packs/dpdp-rules-2025.v1.yaml)
and the JSON Schema in [`src/dpdpkit_policies/schema/`](src/dpdpkit_policies/schema/). Overlays are
described in [`overlays/README.md`](src/dpdpkit_policies/overlays/README.md).

## Licence

Apache-2.0.
