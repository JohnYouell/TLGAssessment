# The Lord's Gym — payment and account update 1.0.1

This is a source-file update for the complete version 1.0.0 WordPress plugin.
It is NOT a standalone plugin installation ZIP. Keep the original theme, data,
vendor dependencies, assets, and other plugin files.

## Apply to the complete plugin package

1. Make a backup of the site files and database. Use a private staging installation.
2. Unzip the original complete tlg-assessments.zip from TLG-WordPress-Recreation-v1.0.0.zip.
3. From this update, copy the tlg-assessments folder over the original
   tlg-assessments folder, replacing only these four files:
   - tlg-assessments.php
   - includes/core.php
   - includes/accounts.php
   - includes/content-payments.php
4. Keep includes/assessments.php, includes/email-pdf.php, data/, vendor/, and all
   other original files. Do not replace the complete plugin directory with this
   partial update.
5. Compress the COMPLETE updated tlg-assessments folder into a ZIP. That combined
   ZIP can be uploaded through WordPress Plugins > Add Plugin > Upload Plugin.
   Alternatively, replace the four files in an existing installation using your
   host's file manager, preserving the rest of the plugin.
6. Confirm the plugin shows version 1.0.1.

## Behavior changes

- Checkout requests are serialized per reader. Retries recover the same Stripe
  session using the original request body and idempotency key.
- Open sessions are reused. Changing discounts closes the prior payable session.
  A still-processing payment prevents another checkout.
- Existing pending transactions from version 1.0.0 are recovered. Multiple older
  pending sessions require reconciliation before another payment is allowed.
- A recorded paid transaction can restore a missing access flag.
- The handler verifies that access was persisted. Database read/write failures
  return HTTP 503 so Stripe can retry.
- Google sign-in uses an already-bound provider subject. An existing account
  with the same email is never silently merged. Such readers use password
  sign-in or Forgot Password; adding a future explicit Google linking interface
  is outside this update.
- The price remains $25 USD one time. No subscriptions or invoicing features
  were added, and no API credentials or webhook secrets are in this package.

## Required staging checks

Use sandbox credentials and a separate sandbox webhook endpoint:
https://YOUR-STAGING-DOMAIN/wp-json/tlg/v1/stripe/webhook

Check successful, failed, cancelled, and delayed payments; confirm access belongs
to the right reader. Replay an event and confirm the discount is counted once.
Check Google sign-in with the actual configured provider if enabled.
If a previous version linked Google to existing email/password accounts,
review those accounts and require a password reset where ownership is uncertain.

Automated regression tests use real WordPress/MySQL and mocked provider HTTP.
They do not replace end-to-end checks with Stripe, Google, the frontend, or
the actual host. Google OAuth UI and PHP vendor/data completeness are not tested
by the partial source update.
