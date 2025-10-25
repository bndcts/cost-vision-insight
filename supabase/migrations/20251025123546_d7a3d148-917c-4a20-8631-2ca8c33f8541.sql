-- Create indices table
CREATE TABLE public.indices (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  value NUMERIC NOT NULL,
  unit TEXT NOT NULL,
  price_factor NUMERIC NOT NULL,
  date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create articles table
CREATE TABLE public.articles (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  drawing_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create cost_models table (junction table linking articles to indices)
CREATE TABLE public.cost_models (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  article_id UUID NOT NULL REFERENCES public.articles(id) ON DELETE CASCADE,
  index_id UUID NOT NULL REFERENCES public.indices(id) ON DELETE CASCADE,
  factor NUMERIC NOT NULL, -- percentage or factor of how the index contributes
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.indices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cost_models ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access (hackathon demo)
CREATE POLICY "Indices are publicly readable" 
ON public.indices 
FOR SELECT 
USING (true);

CREATE POLICY "Articles are publicly readable" 
ON public.articles 
FOR SELECT 
USING (true);

CREATE POLICY "Cost models are publicly readable" 
ON public.cost_models 
FOR SELECT 
USING (true);

-- Create indexes for performance
CREATE INDEX idx_cost_models_article_id ON public.cost_models(article_id);
CREATE INDEX idx_cost_models_index_id ON public.cost_models(index_id);
CREATE INDEX idx_indices_date ON public.indices(date DESC);