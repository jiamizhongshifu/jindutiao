-- GaiYa Row Level Security (RLS) Policies
-- Enables RLS on all tables and defines access policies

-- ============================================
-- 1. progress_bar_styles (Progress Bar Styles Library)
-- Access: Public read for published, creators manage own
-- ============================================
ALTER TABLE progress_bar_styles ENABLE ROW LEVEL SECURITY;

-- Anyone can view published styles
CREATE POLICY "Anyone can view published styles" ON progress_bar_styles
    FOR SELECT
    USING (status = 'published');

-- Creators can manage their own styles (including drafts)
CREATE POLICY "Creators can manage own styles" ON progress_bar_styles
    FOR ALL
    USING (author_id = auth.uid());

-- ============================================
-- 2. time_markers (Time Markers Library)
-- Access: Public read for published, creators manage own
-- ============================================
ALTER TABLE time_markers ENABLE ROW LEVEL SECURITY;

-- Anyone can view published markers
CREATE POLICY "Anyone can view published markers" ON time_markers
    FOR SELECT
    USING (status = 'published');

-- Creators can manage their own markers
CREATE POLICY "Creators can manage own markers" ON time_markers
    FOR ALL
    USING (author_id = auth.uid());

-- ============================================
-- 3. user_purchased_styles (Purchase Records)
-- Access: Users can only view their own purchases
-- ============================================
ALTER TABLE user_purchased_styles ENABLE ROW LEVEL SECURITY;

-- Users can view their own purchases
CREATE POLICY "Users can view own purchases" ON user_purchased_styles
    FOR SELECT
    USING (user_id = auth.uid());

-- ============================================
-- 4. user_favorites (Favorites)
-- Access: Users can manage their own favorites
-- ============================================
ALTER TABLE user_favorites ENABLE ROW LEVEL SECURITY;

-- Users can manage their own favorites (view, add, remove)
CREATE POLICY "Users can manage own favorites" ON user_favorites
    FOR ALL
    USING (user_id = auth.uid());

-- ============================================
-- 5. creator_earnings (Creator Earnings)
-- Access: Creators can only view their own earnings
-- ============================================
ALTER TABLE creator_earnings ENABLE ROW LEVEL SECURITY;

-- Creators can view their own earnings
CREATE POLICY "Creators can view own earnings" ON creator_earnings
    FOR SELECT
    USING (user_id = auth.uid());

-- ============================================
-- 6. withdrawal_requests (Withdrawal Requests)
-- Access: Users can view/create their own requests
-- ============================================
ALTER TABLE withdrawal_requests ENABLE ROW LEVEL SECURITY;

-- Users can view their own withdrawal requests
CREATE POLICY "Users can view own withdrawals" ON withdrawal_requests
    FOR SELECT
    USING (user_id = auth.uid());

-- Users can create withdrawal requests for themselves
CREATE POLICY "Users can create withdrawals" ON withdrawal_requests
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- ============================================
-- 7. otp_codes (OTP Verification Codes)
-- Access: Service role only (sensitive data)
-- ============================================
ALTER TABLE otp_codes ENABLE ROW LEVEL SECURITY;

-- No policies = blocks all client access
-- Serverless Functions use service_role key to bypass RLS

-- ============================================
-- 8. rate_limits (API Rate Limiting)
-- Access: Service role only
-- ============================================
ALTER TABLE rate_limits ENABLE ROW LEVEL SECURITY;

-- No policies = blocks all client access
-- Serverless Functions use service_role key to bypass RLS

-- ============================================
-- 9. payment_cache (Payment Status Cache)
-- Access: Service role only
-- ============================================
ALTER TABLE payment_cache ENABLE ROW LEVEL SECURITY;

-- No policies = blocks all client access
-- Serverless Functions use service_role key to bypass RLS

-- ============================================
-- Notes:
-- ============================================
-- 1. Service role key (SUPABASE_SERVICE_ROLE_KEY) bypasses all RLS policies
-- 2. Anon key is restricted by RLS policies defined above
-- 3. Tables without policies (otp_codes, rate_limits, payment_cache)
--    block all direct client access - only accessible via Serverless Functions
