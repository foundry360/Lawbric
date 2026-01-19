CREATE TABLE IF NOT EXISTS public.cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  case_number TEXT,
  description TEXT,
  created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

ALTER TABLE public.cases ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view all cases" ON public.cases;
CREATE POLICY "Users can view all cases"
  ON public.cases
  FOR SELECT
  TO authenticated
  USING (is_active = TRUE);

DROP POLICY IF EXISTS "Users can create cases" ON public.cases;
CREATE POLICY "Users can create cases"
  ON public.cases
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = created_by);

DROP POLICY IF EXISTS "Users can update own cases" ON public.cases;
CREATE POLICY "Users can update own cases"
  ON public.cases
  FOR UPDATE
  TO authenticated
  USING (
    created_by = auth.uid()
    OR
    (
      (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
      OR
      (auth.jwt() -> 'raw_user_meta_data' ->> 'role') = 'admin'
    )
  )
  WITH CHECK (
    created_by = auth.uid()
    OR
    (
      (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
      OR
      (auth.jwt() -> 'raw_user_meta_data' ->> 'role') = 'admin'
    )
  );

DROP POLICY IF EXISTS "Users can delete own cases" ON public.cases;
CREATE POLICY "Users can delete own cases"
  ON public.cases
  FOR DELETE
  TO authenticated
  USING (
    created_by = auth.uid()
    OR
    (
      (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
      OR
      (auth.jwt() -> 'raw_user_meta_data' ->> 'role') = 'admin'
    )
  );

CREATE OR REPLACE FUNCTION public.handle_cases_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = TIMEZONE('utc', NOW());
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS on_cases_updated ON public.cases;
CREATE TRIGGER on_cases_updated
  BEFORE UPDATE ON public.cases
  FOR EACH ROW EXECUTE FUNCTION public.handle_cases_updated_at();

