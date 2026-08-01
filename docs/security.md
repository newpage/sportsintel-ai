# Security Foundation

## Passwords
Argon2 is used through `pwdlib.PasswordHash.recommended()`.

## Sessions
Access tokens expire quickly. Opaque refresh tokens are stored only as SHA-256 hashes and rotate on every refresh. Reuse of a revoked refresh token revokes its token family.

## Login protection
Both Redis-based attempt limiting and per-account lockout are enforced.

## Email workflows
Verification and password reset use single-use, hashed, expiring opaque tokens. Development can return tokens in API responses; production should set `AUTH_RETURN_TOKENS_IN_RESPONSE=false` and connect an email provider.

## MFA
TOTP enrollment, confirmation, login enforcement, and disablement are implemented. The next UI sprint can add QR-code rendering and account security screens.
