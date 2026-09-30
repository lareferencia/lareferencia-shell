ALTER TABLE local_user DROP CONSTRAINT local_user_global_role_check;
ALTER TABLE local_user ADD CONSTRAINT local_user_global_role_check
    CHECK (global_role IN ('ADMIN', 'READER', 'DASHBOARD'));
