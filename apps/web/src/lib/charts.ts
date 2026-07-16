import { getApiUrl } from "./api";

export type ChartPayload = {
  source: { name: string; slug: string; is_mock: boolean; source_weights?: Record<string, number> };
  week_date: string;
  entries: {
    position: number;
    title: string;
    artist: string;
    previous_position?: number | null;
    position_change?: number | null;
  }[];
};

export async function fetchChartClient(slug = "demo-top-40"): Promise<ChartPayload> {
  const res = await fetch(`${getApiUrl()}/api/v1/charts/${slug}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API ${res.status}`);
  }
  return res.json();
}
