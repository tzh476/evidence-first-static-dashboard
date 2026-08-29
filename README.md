# Evidence-First Static Dashboard

A small, dependency-free reference implementation for building static status
dashboards without treating a successful scheduled build as proof that every
upstream value is current.

The generator takes one normalized snapshot and emits three artifacts:

- `dashboard.json` for machine consumers;
- `status.md` for pull-request review; and
- `index.html` for readers.

Every source must carry an explicit `ok`, `stale`, or `failed` state. A failed
source can remain visible in a reviewable partial snapshot, but it cannot be
silently rendered as a healthy metric.

## Run it

```bash
python3 generate_dashboard.py \
  --input source/metrics.json \
  --output public \
  --generated-at 2026-08-12T12:00:00+00:00
python3 -m unittest test_generate_dashboard.py
```

## Deploy on DigitalOcean

[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/tzh476/evidence-first-static-dashboard/tree/master)

The repository includes an App Platform specification and a one-click deploy
template. The build runs the unit tests before generating the static files in
`public/`; no runtime service, database, secret, or paid component is required.

The checked-in fixture intentionally contains one fresh source, one stale
source, and one failed source. It demonstrates that the generated HTML carries
a visible warning and preserves the upstream error instead of converting it to
zero or an empty card.

## What a green build proves

A successful run proves that the normalized snapshot passed validation and was
rendered consistently. It does not make a stale or failed upstream source
current. Production users should decide explicitly which source failures are
acceptable to publish and which must block a deployment.

## Boundaries

This is a reference implementation. It does not fetch live production data,
does not contain credentials, and makes no hosting or vendor-product claim.
Replace the fixture with a source-owned fetcher only after defining freshness,
failure, review, and publication rules for the actual system.

## Authorship and assistance disclosure

This repository was prepared by Stephen Smith (`tzh476`) with AI assistance for
research, drafting, and implementation. The code and documentation are
intended to be inspected, tested, corrected, and reused with that provenance
in mind. Do not represent this repository as an independently human-authored
client deployment or as proof of an accepted editorial commission.

## License

MIT. See [LICENSE](LICENSE).
