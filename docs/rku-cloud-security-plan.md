# RKU Cloud — secure storage implementation plan

Status: **design only**. No file upload, automatic phone backup, or restore service is enabled yet.

## First milestone: private manual upload
- Authenticate every request with the existing RKU session; authorize every file by owner ID.
- Keep file bytes in private object storage, **not** in the Render service filesystem or Postgres.
- Store metadata in Postgres: file ID, owner RKU ID, object key, original display name, MIME type, size, checksum, created time, and deletion state.
- Generate random opaque object keys; never use a supplied filename as a storage path.
- Use a short-lived signed upload URL after validating file size, MIME category and account quota. Verify final size/checksum and ownership on completion.
- Serve downloads only via short-lived signed URLs following owner authorization. Never expose public buckets or permanent file URLs.
- Apply per-account quotas, upload throttling, object expiration for abandoned uploads, and safe deletion rules.
- Encrypt in transit and at rest; keep storage keys in Render environment secrets, never in GitHub source or frontend.
- Add isolated tests for cross-account access, invalid filenames, size limits, expired upload URLs, quota enforcement, deletion, and checksum mismatches.

## Second milestone: backup and recovery
- Add a separate durable backup/restore strategy, recovery drills, and documented retention before claiming data is safe.
- Only then consider user-controlled mobile photo/video backup. Browsers cannot guarantee automatic background backup when a phone is offline or the app is closed.
- Clearly show upload completion, failure/retry, and storage usage; do not claim a file is backed up until confirmed in private storage.
- Verify privacy policy, data retention, Australian and international privacy obligations before public launch.

## Deployment gate
1. Choose an affordable private object-storage provider and budget.
2. Implement metadata schema and authenticated upload/download endpoints.
3. Test without using real user files.
4. Validate persistence, access isolation, and recovery on a staging setup.
5. Enable cloud features only after owner approval.

**Current hosting decision:** Stay on the free Render plan during development. Do not connect the custom domain or enable paid services without explicit approval.
**Database warning:** Free Render Postgres may expire; verify expiry and prepare an export/migration before any deadline. Do not assume backups are configured.
