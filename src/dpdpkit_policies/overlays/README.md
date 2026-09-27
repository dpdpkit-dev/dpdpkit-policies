# Overlays

Sector overlays add rules on top of a base pack. Planned for v0.5:

| Overlay | Adds | Task |
| --- | --- | --- |
| `cert-in-2022` | 6-hour incident reporting clock, 180-day log retention in India | POL-10 |
| `rbi-kyc` | Longer retention for KYC records, legal-hold reason codes | POL-11 |
| `health-abdm` | Health-record retention defaults, ABDM consent references | POL-12 |
| `education` | Fourth Schedule exemptions for schools and ed-tech | POL-13 |

Format:

```yaml
id: cert-in-2022
kind: overlay
source: "CERT-In Directions No. 20(3)/2022-CERT-In, 28 April 2022"
applies_to: [dpdp-rules-2025]   # pack id prefixes
set:                             # deep-merged into the pack; the result must validate against pack.schema.json
  breach:
    cert_in_report_hours: 6
```
