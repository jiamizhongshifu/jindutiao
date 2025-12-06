-- 创建 RPC 函数用于升级用户订阅
-- 这个函数绕过 PostgREST schema cache 问题

CREATE OR REPLACE FUNCTION upgrade_user_subscription(
    p_user_id UUID,
    p_tier TEXT,
    p_expires_at TIMESTAMPTZ
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_result JSON;
BEGIN
    -- 更新用户订阅信息
    UPDATE users
    SET 
        tier = p_tier,
        subscription_expires_at = p_expires_at,
        updated_at = NOW()
    WHERE id = p_user_id;

    -- 检查是否更新成功
    IF NOT FOUND THEN
        RAISE EXCEPTION 'User not found: %', p_user_id;
    END IF;

    -- 返回更新后的用户信息
    SELECT json_build_object(
        'user_id', id,
        'tier', tier,
        'subscription_expires_at', subscription_expires_at,
        'updated_at', updated_at
    )
    INTO v_result
    FROM users
    WHERE id = p_user_id;

    RETURN v_result;
END;
$$;

-- 授权给 authenticated 和 anon 角色
GRANT EXECUTE ON FUNCTION upgrade_user_subscription(UUID, TEXT, TIMESTAMPTZ) TO authenticated, anon, service_role;

-- 添加注释
COMMENT ON FUNCTION upgrade_user_subscription IS '升级用户订阅等级和到期时间,绕过 PostgREST schema cache';
