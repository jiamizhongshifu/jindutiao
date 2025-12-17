-- GaiYa Function Search Path Security Fix
-- Fixes "function_search_path_mutable" warnings by setting search_path = ''

-- ============================================
-- 1. update_updated_at_column
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

-- ============================================
-- 2. reset_daily_quotas
-- ============================================
CREATE OR REPLACE FUNCTION reset_daily_quotas()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    UPDATE public.user_quotas
    SET daily_ai_tasks = 0,
        updated_at = NOW()
    WHERE daily_ai_tasks > 0;
END;
$$;

-- ============================================
-- 3. reset_weekly_quotas
-- ============================================
CREATE OR REPLACE FUNCTION reset_weekly_quotas()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    UPDATE public.user_quotas
    SET weekly_ai_tasks = 0,
        updated_at = NOW()
    WHERE weekly_ai_tasks > 0;
END;
$$;

-- ============================================
-- 4. sync_email_verification
-- ============================================
CREATE OR REPLACE FUNCTION sync_email_verification()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    IF NEW.email_confirmed_at IS NOT NULL AND OLD.email_confirmed_at IS NULL THEN
        UPDATE public.users
        SET email_verified = TRUE,
            updated_at = NOW()
        WHERE id = NEW.id;
    END IF;
    RETURN NEW;
END;
$$;

-- ============================================
-- 5. handle_email_verification
-- ============================================
CREATE OR REPLACE FUNCTION handle_email_verification()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    IF NEW.email_verified = TRUE AND OLD.email_verified = FALSE THEN
        -- Additional logic when email is verified
        NULL;
    END IF;
    RETURN NEW;
END;
$$;

-- ============================================
-- 6. upgrade_user_subscription (from RPC file)
-- ============================================
CREATE OR REPLACE FUNCTION upgrade_user_subscription(
    p_user_id UUID,
    p_tier TEXT,
    p_expires_at TIMESTAMPTZ
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_result JSON;
BEGIN
    -- Update user subscription info
    UPDATE public.users
    SET
        tier = p_tier,
        subscription_expires_at = p_expires_at,
        updated_at = NOW()
    WHERE id = p_user_id;

    -- Check if update was successful
    IF NOT FOUND THEN
        RAISE EXCEPTION 'User not found: %', p_user_id;
    END IF;

    -- Return updated user info
    SELECT json_build_object(
        'user_id', id,
        'tier', tier,
        'subscription_expires_at', subscription_expires_at,
        'updated_at', updated_at
    )
    INTO v_result
    FROM public.users
    WHERE id = p_user_id;

    RETURN v_result;
END;
$$;

-- Re-grant permissions
GRANT EXECUTE ON FUNCTION upgrade_user_subscription(UUID, TEXT, TIMESTAMPTZ) TO authenticated, anon, service_role;

-- ============================================
-- Notes:
-- ============================================
-- 1. SET search_path = '' prevents search_path injection attacks
-- 2. All table references now use explicit schema (public.)
-- 3. SECURITY DEFINER runs function with owner privileges
-- 4. Run this SQL in Supabase Dashboard to fix all warnings
