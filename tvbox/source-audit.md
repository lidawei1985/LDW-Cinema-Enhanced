# Source Audit

The supplied configuration was not imported automatically.

Observed in the attachment:

- 254 unique URLs
- 69 plain HTTP URLs
- 5 remote JAR URLs
- 43 URLs matching common parser/VIP-bypass patterns
- malformed JSON-like syntax and mojibake text

These findings make the file unsuitable for unattended execution. Entries should be added to `config.json` only after ownership/authorization, HTTPS transport, content legality, and endpoint behavior are individually confirmed.
