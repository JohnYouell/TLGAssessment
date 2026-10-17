# Auth Testing Notes (The Lord's Gym)

Auth = custom JWT httpOnly cookies (access_token 15 min, refresh_token 7 days), with token version `v` checked against users.token_version (bumped on password reset so old sessions die).

## Email/password
- POST /api/auth/register, /api/auth/login, /api/auth/logout, /api/auth/refresh, GET /api/auth/me
- 5 failed logins per email -> 429 lockout for 15 min
- Seed test users directly in Mongo (bcrypt `$2b$` hash) to avoid real Brevo welcome emails. Delete TEST users afterwards.

## Forgot / reset password
- POST /api/auth/forgot-password {email} -> always {"ok": true} (no enumeration). At most 3 tokens per email per hour.
- Tokens are stored as a sha256 `token_hash` in password_reset_tokens (1 h TTL index on expires_at, single use).
- For tests, insert a token doc yourself: {token_hash: sha256(raw), user_id, email, used: false, created_at: iso, expires_at: datetime(+1h)} and use the raw token at /reset-password?token=RAW
- POST /api/auth/reset-password {token, password} -> sets new password, bumps token_version (old cookies get 401), logs the user in

## Emergent Google login
- The button redirects to https://auth.emergentagent.com/?redirect=<origin>/dashboard
- It returns to /dashboard#session_id=..., AuthCallback POSTs /api/auth/google {session_id, referred_by}
- The backend exchanges it at demobackend.emergentagent.com session-data, links by email (existing account kept) or creates a user (marketing_opt_in true, Brevo contact + welcome email), then sets our own JWT cookies
- The real Google flow can't be automated. Test that an invalid session_id gives 401 and the UI shows auth-callback-error, plus the button redirect URL.
