import { useQuery } from "@tanstack/react-query";

const API_BASE_URL = "http://localhost:8000/api/v1";

export interface IndexValuePoint {
  date: string;
  value: number;
}

export interface ArticleIndexData {
  index_id: number;
  index_name: string;
  unit: string;
  quantity_grams: number;
  values: IndexValuePoint[];
}

export interface ArticleIndicesValuesResponse {
  article_id: number;
  article_name: string;
  indices: ArticleIndexData[];
}

export interface ArticleStatusResponse {
  id: number;
  processing_status: "pending" | "processing" | "completed" | "failed";
  processing_error: string | null;
  processing_started_at: string | null;
  processing_completed_at: string | null;
}

export interface ArticleResponse {
  id: number;
  article_name: string;
  description?: string;
  unit_weight?: number;
  product_specification_filename?: string;
  drawing_filename?: string;
  comment?: string;
  processing_status: string;
  processing_error?: string | null;
  processing_started_at?: string | null;
  processing_completed_at?: string | null;
  created_at: string;
}

async function fetchArticleIndicesValues(
  articleId: number
): Promise<ArticleIndicesValuesResponse> {
  const response = await fetch(
    `${API_BASE_URL}/articles/${articleId}/indices-values`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch indices values");
  }

  return response.json();
}

async function fetchArticleStatus(
  articleId: number
): Promise<ArticleStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/articles/${articleId}/status`);

  if (!response.ok) {
    throw new Error(`Failed to fetch status: ${response.status}`);
  }

  return response.json();
}

async function fetchArticle(articleId: number): Promise<ArticleResponse> {
  const response = await fetch(`${API_BASE_URL}/articles/${articleId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch article: ${response.status}`);
  }

  return response.json();
}

export function useArticleIndicesValues(articleId: number | null) {
  return useQuery({
    queryKey: ["article-indices-values", articleId],
    queryFn: () => fetchArticleIndicesValues(articleId!),
    enabled: articleId !== null,
    staleTime: 1000 * 60 * 10, // 10 minutes - price data doesn't change frequently
  });
}

export function useArticleStatus(articleId: number | null) {
  return useQuery({
    queryKey: ["article-status", articleId],
    queryFn: () => fetchArticleStatus(articleId!),
    enabled: articleId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.processing_status;
      if (status === "pending" || status === "processing") {
        return 2000; // Poll every 2 seconds while processing
      }
      return false; // Stop polling when complete or failed
    },
  });
}

export function useArticle(articleId: number | null) {
  return useQuery({
    queryKey: ["article", articleId],
    queryFn: () => fetchArticle(articleId!),
    enabled: articleId !== null,
  });
}
