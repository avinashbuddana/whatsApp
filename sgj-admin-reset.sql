-- One-time SGJ tenant admin recovery.
-- Uses variables passed to psql from Render env. Never log secret values.
\set ON_ERROR_STOP on
CREATE EXTENSION IF NOT EXISTS pgcrypto;
BEGIN;
CREATE TEMP TABLE sgj_admin_recovery_payload (
  desired_email text NOT NULL,
  desired_password text NOT NULL
) ON COMMIT DROP;
INSERT INTO sgj_admin_recovery_payload (desired_email, desired_password)
VALUES (:'admin_email', :'admin_password');

DO $wingerx$
DECLARE
  chosen_admin uuid;
  desired_email text;
  desired_password text;
BEGIN
  SELECT p.desired_email, p.desired_password
  INTO desired_email, desired_password
  FROM sgj_admin_recovery_payload p
  LIMIT 1;

  IF length(desired_password) < 12 THEN
    RAISE EXCEPTION 'The configured SGJ admin password must be at least 12 characters.';
  END IF;

  -- Prefer the already-existing desired email. If it doesn't exist,
  -- reuse the oldest superadmin rather than inserting another account.
  SELECT u.id INTO chosen_admin
    FROM users u
   WHERE u.deleted_at IS NULL AND u.is_super_admin = true
   ORDER BY (u.email = desired_email) DESC, u.created_at ASC
   LIMIT 1;

  IF chosen_admin IS NULL THEN
    RAISE EXCEPTION 'SGJ admin recovery: no existing superadmin in SGJ tenant database.';
  END IF;

  UPDATE users
     SET email = desired_email,
         password_hash = crypt(desired_password, gen_salt('bf', 12)),
         is_active = true,
         updated_at = NOW()
   WHERE id = chosen_admin;

  -- Deactivate an unneeded factory admin login if the client now uses
  -- a different address. Never delete any users or their data.
  IF desired_email <> 'admin@admin.com' THEN
    UPDATE users
       SET is_active = false, updated_at = NOW()
     WHERE email = 'admin@admin.com'
       AND is_super_admin = true
       AND id <> chosen_admin
       AND deleted_at IS NULL;
  END IF;
END;
$wingerx$;
COMMIT;
