-- BE-008 security hardening: enable RLS and add least-privilege policies
-- for claim workflow tables exposed via Supabase Data API.
BEGIN;

ALTER TABLE public.claim_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.verification_events ENABLE ROW LEVEL SECURITY;

-- Ensure public roles do not get broad table privileges.
REVOKE ALL ON public.claim_requests FROM anon, authenticated;
REVOKE ALL ON public.verification_events FROM anon, authenticated;

-- Grant only the minimum operations needed for end-user claim flows.
GRANT SELECT, INSERT ON public.claim_requests TO authenticated;
GRANT SELECT ON public.verification_events TO authenticated;

DROP POLICY IF EXISTS claim_requests_select_own ON public.claim_requests;
CREATE POLICY claim_requests_select_own
ON public.claim_requests
FOR SELECT
TO authenticated
USING (user_id = auth.uid());

DROP POLICY IF EXISTS claim_requests_insert_own ON public.claim_requests;
CREATE POLICY claim_requests_insert_own
ON public.claim_requests
FOR INSERT
TO authenticated
WITH CHECK (
    user_id = auth.uid()
    AND lower(status) = 'pending'
);

DROP POLICY IF EXISTS verification_events_select_for_owned_claims ON public.verification_events;
CREATE POLICY verification_events_select_for_owned_claims
ON public.verification_events
FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1
        FROM public.claim_requests cr
        WHERE cr.id = verification_events.claim_request_id
          AND cr.user_id = auth.uid()
    )
);

COMMIT;
