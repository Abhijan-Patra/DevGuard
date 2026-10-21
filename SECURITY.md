# Security reporting

This is a public preview, not a security certification. Use the latest release. Older releases do not have a guaranteed security maintenance window.

Use GitHub's **Security → Report a vulnerability** for this repository when private reporting is available. If that option is absent, open a minimal issue asking the maintainer for a private reporting channel; do not include vulnerability details or sensitive material until a private channel is established.

Never include real secrets, private clipboard data, user databases, tokens or proprietary source. Use a minimal declared synthetic example, version/OS and the fixed reason code. Do not test against unrelated users or services.

The [threat model](docs/SECURITY_POLICY.md) defines the supported boundary. Local browser pairing grants operator controls on the loopback service; do not reverse-proxy it to the internet. Clipboard observation is advisory. Explicit supported gates, fixed tool scopes, independent tests, model digest checks and reviewed source hashes enforce their respective paths; none provide universal interception or perfect classification.
