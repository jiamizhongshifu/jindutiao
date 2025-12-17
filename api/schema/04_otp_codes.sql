-- GaiYa OTP Verification Codes Table
-- Used for email verification during signup and password reset

CREATE TABLE IF NOT EXISTS otp_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Email address to verify
    email TEXT NOT NULL,

    -- 6-digit OTP code
    code TEXT NOT NULL,

    -- Purpose: 'signup' or 'password_reset'
    purpose TEXT CHECK (purpose IN ('signup', 'password_reset')),

    -- Expiration timestamp (10 minutes from creation)
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Failed verification attempts (max 5)
    attempts INTEGER DEFAULT 0,

    -- Creation timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_otp_codes_email ON otp_codes(email);
CREATE INDEX IF NOT EXISTS idx_otp_codes_expires ON otp_codes(expires_at);

-- Comments
COMMENT ON TABLE otp_codes IS 'OTP verification codes for email verification';
COMMENT ON COLUMN otp_codes.email IS 'Email address to verify';
COMMENT ON COLUMN otp_codes.code IS '6-digit verification code';
COMMENT ON COLUMN otp_codes.purpose IS 'Purpose of OTP: signup or password_reset';
COMMENT ON COLUMN otp_codes.expires_at IS 'Code expiration time (10 minutes from creation)';
COMMENT ON COLUMN otp_codes.attempts IS 'Number of failed verification attempts (max 5)';

-- Optional: Auto-cleanup function for expired codes
CREATE OR REPLACE FUNCTION cleanup_expired_otp_codes()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    DELETE FROM public.otp_codes
    WHERE expires_at < NOW() - INTERVAL '1 hour';
END;
$$;

-- Note: Schedule this function using pg_cron if available:
-- SELECT cron.schedule('cleanup-otp', '0 * * * *', 'SELECT cleanup_expired_otp_codes()');
