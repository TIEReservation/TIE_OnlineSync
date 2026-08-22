-- Create monthly_targets table for Monthly Target Management feature

-- Drop table if it exists (optional, for fresh setup)
-- DROP TABLE IF EXISTS monthly_targets;

-- Create the monthly_targets table
CREATE TABLE IF NOT EXISTS public.monthly_targets (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    property_name TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    target NUMERIC(15, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(property_name, year, month)
);

-- Create an index for faster queries
CREATE INDEX IF NOT EXISTS idx_monthly_targets_property_year_month 
ON public.monthly_targets(property_name, year, month);

CREATE INDEX IF NOT EXISTS idx_monthly_targets_year_month 
ON public.monthly_targets(year, month);

-- Enable Row Level Security (optional, for security)
ALTER TABLE public.monthly_targets ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow authenticated users to read all targets
CREATE POLICY "Allow authenticated users to read targets"
ON public.monthly_targets
FOR SELECT
TO authenticated
USING (true);

-- Create a policy to allow authenticated users to insert/update/delete targets
CREATE POLICY "Allow authenticated users to manage targets"
ON public.monthly_targets
FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Optional: Add comments to table and columns for documentation
COMMENT ON TABLE public.monthly_targets IS 'Stores monthly revenue targets for properties';
COMMENT ON COLUMN public.monthly_targets.id IS 'Unique identifier for the target record';
COMMENT ON COLUMN public.monthly_targets.property_name IS 'Name of the property';
COMMENT ON COLUMN public.monthly_targets.year IS 'Year of the target';
COMMENT ON COLUMN public.monthly_targets.month IS 'Month of the target (1-12)';
COMMENT ON COLUMN public.monthly_targets.target IS 'Revenue target amount in rupees';
COMMENT ON COLUMN public.monthly_targets.created_at IS 'Timestamp when record was created';
COMMENT ON COLUMN public.monthly_targets.updated_at IS 'Timestamp when record was last updated';
