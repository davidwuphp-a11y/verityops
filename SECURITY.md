# Security and evidence handling

Run this demo locally with synthetic inputs. The action adapter intentionally writes to newly created fixture databases. The verification reader opens its own read-only connections. The demo requires no API keys or account credentials. It does not implement authentication, tenant isolation, encrypted evidence storage, redaction or retention scheduling.

Generated evidence can contain action inputs, replies, state snapshots and SQLite files. Keep run directories out of version control. Review any reproduction before sharing it. For a public issue, include only the synthetic case ID, versions and a minimal redacted description. For a sensitive report, use GitHub private vulnerability reporting if enabled, or request a private maintainer channel without disclosing sensitive details.

Only use customer-side records with written authorization, an isolated sandbox, scoped access and an agreed retention policy. See [readback preflight](READBACK_PREFLIGHT.md).
