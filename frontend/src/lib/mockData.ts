// Mock data for development - will be replaced with API calls later

export interface Index {
  id: string;
  name: string;
  value: number;
  unit: string;
  price_factor: number;
  date: string;
  created_at: string;
}

export interface Article {
  id: string;
  name: string;
  description: string | null;
  drawing_url: string | null;
  created_at: string;
}

export interface CostModel {
  id: string;
  article_id: string;
  index_id: string;
  factor: number;
  created_at: string;
  articles?: { name: string };
  indices?: { name: string; unit: string };
}

export const mockIndices: Index[] = [
  {
    id: "1",
    name: "Steel Price Index",
    value: 125.5,
    unit: "EUR/ton",
    price_factor: 1.15,
    date: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
  {
    id: "2",
    name: "Aluminum Index",
    value: 89.75,
    unit: "EUR/kg",
    price_factor: 1.08,
    date: new Date(Date.now() - 86400000).toISOString(), // Yesterday
    created_at: new Date().toISOString(),
  },
  {
    id: "3",
    name: "Copper Index",
    value: 156.2,
    unit: "EUR/kg",
    price_factor: 1.22,
    date: new Date(Date.now() - 172800000).toISOString(), // 2 days ago
    created_at: new Date().toISOString(),
  },
  {
    id: "4",
    name: "Energy Cost Index",
    value: 98.3,
    unit: "EUR/MWh",
    price_factor: 0.95,
    date: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
];

export const mockArticles: Article[] = [
  {
    id: "1",
    name: "Precision Gear Assembly",
    description:
      "High-precision gear assembly for industrial machinery. Manufactured from hardened steel with tight tolerances.",
    drawing_url: "https://example.com/drawings/gear-assembly.pdf",
    created_at: new Date().toISOString(),
  },
  {
    id: "2",
    name: "Motor Housing Unit",
    description:
      "Cast aluminum motor housing with integrated cooling fins. Suitable for 5-15kW motors.",
    drawing_url: null,
    created_at: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: "3",
    name: "Control Panel Enclosure",
    description:
      "Weather-resistant steel enclosure for outdoor electrical installations.",
    drawing_url: "https://example.com/drawings/enclosure.pdf",
    created_at: new Date(Date.now() - 172800000).toISOString(),
  },
];

export const mockCostModels: CostModel[] = [
  {
    id: "1",
    article_id: "1",
    index_id: "1",
    factor: 0.65,
    created_at: new Date().toISOString(),
    articles: { name: "Precision Gear Assembly" },
    indices: { name: "Steel Price Index", unit: "EUR/ton" },
  },
  {
    id: "2",
    article_id: "1",
    index_id: "4",
    factor: 0.35,
    created_at: new Date().toISOString(),
    articles: { name: "Precision Gear Assembly" },
    indices: { name: "Energy Cost Index", unit: "EUR/MWh" },
  },
  {
    id: "3",
    article_id: "2",
    index_id: "2",
    factor: 0.75,
    created_at: new Date().toISOString(),
    articles: { name: "Motor Housing Unit" },
    indices: { name: "Aluminum Index", unit: "EUR/kg" },
  },
  {
    id: "4",
    article_id: "2",
    index_id: "4",
    factor: 0.25,
    created_at: new Date().toISOString(),
    articles: { name: "Motor Housing Unit" },
    indices: { name: "Energy Cost Index", unit: "EUR/MWh" },
  },
  {
    id: "5",
    article_id: "3",
    index_id: "1",
    factor: 0.8,
    created_at: new Date().toISOString(),
    articles: { name: "Control Panel Enclosure" },
    indices: { name: "Steel Price Index", unit: "EUR/ton" },
  },
  {
    id: "6",
    article_id: "3",
    index_id: "4",
    factor: 0.2,
    created_at: new Date().toISOString(),
    articles: { name: "Control Panel Enclosure" },
    indices: { name: "Energy Cost Index", unit: "EUR/MWh" },
  },
];
