-- One-time WingerX / Shree Gajanand Jewellers administrator synchronization.
-- No credentials are stored in this file or written to logs.
\set ON_ERROR_STOP on
\getenv admin_email WHATOMATE_DEFAULT_ADMIN__EMAIL
\getenv admin_password WHATOMATE_DEFAULT_ADMIN__PASSWORD
CREATE EXTENSION IF NOT EXISTS pgcrypto;
BEGIN;
CREATE TEMP TABLE sgj_recovery (email text NOT NULL, secret text NOT NULL) ON COMMIT DROP;
INSERT INTO sgj_recovery(email,secret) VALUES (:'admin_email',:'admin_password');

DO $reset$
DECLARE v_email text; v_password text; v_admin_id uuid;
BEGIN
 SELECT email,secret INTO v_email,v_password FROM sgj_recovery LIMIT 1;
 IF v_email <> 'praveer@shreegajanandjewellers.com' THEN
   RAISE EXCEPTION 'Unexpected SGJ admin email configuration';
 END IF;
 IF length(v_password) < 12 THEN
   RAISE EXCEPTION 'SGJ admin password must contain at least 12 characters';
 END IF;
 SELECT id INTO v_admin_id FROM users
  WHERE deleted_at IS NULL AND is_super_admin = true
  ORDER BY (email = v_email) DESC, created_at ASC
  LIMIT 1 FOR UPDATE;
 IF v_admin_id IS NULL THEN
  RAISE EXCEPTION 'Missing existing SGJ superadmin account';
 END IF;
 IF EXISTS (SELECT 1 FROM users WHERE email = v_email AND id <> v_admin_id AND deleted_at IS NULL) THEN
  RAISE EXCEPTION 'Target admin email is already in use by another user';
 END IF;
 UPDATE users SET email = v_email,
   password_hash = crypt(v_password,gen_salt('bf',12)),
   is_active = true,
   updated_at = NOW()
  WHERE id = v_admin_id;
END;
$reset$;
COMMIT;
