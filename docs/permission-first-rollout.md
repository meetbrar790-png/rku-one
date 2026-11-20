# Permission First: staged rollout requirements

Default for new accounts: unknown IDs cannot place direct voice/video calls or deliver chat. A separate connection request may be sent only after server-side per-sender, per-recipient and per-IP quotas, abuse detection, and duplicate-request suppression. A rejected request must not be retried without recipient-initiated permission. A blocked sender cannot request or contact. The recipient can revoke an existing allowance at any time. No recipient's block state or presence should be leaked to the sender through detailed error messages.

**Server enforcement**: authenticate the acting account; resolve both numeric IDs; check the recipient-controlled permission relation on every call signaling, chat delivery, and request. Apply transactional, race-safe storage and audit logging with minimal retention. Prevent alternate-ID evasion using privacy-conscious signals and appeals. Do not promise that harassment is impossible.

**Mail**: separate consent and spam filtering design; do not silently drop essential messages. **Safety**: allow users to report abuse, manage blocks and privacy, and provide a reviewed exception policy for emergency/support contacts. Account recovery must not bypass recipient permission.

**Release gates**: schema design, integration tests, request flood tests, concurrency tests, security/privacy review, explicit approval. This draft only contains an isolated policy function and unit tests. It changes no live API routes, database schema or existing user permissions.
