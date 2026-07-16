const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function getApiUrl(): string {
  return API_URL;
}

/** WebSocket base URL (wss in production when API is https). */
export function getWsBaseUrl(): string {
  const explicit = process.env.NEXT_PUBLIC_WS_URL;
  if (explicit) return explicit.replace(/\/$/, "");
  return API_URL.replace(/^https:\/\//, "wss://")
    .replace(/^http:\/\//, "ws://")
    .replace(/\/$/, "");
}

export type AuthTokens = { access_token: string; expires_in: number };

export type User = {
  id: string;
  email: string;
  display_name: string;
  roles: string[];
};

const TOKEN_KEY = "hookpress_access_token";
const TOKEN_COOKIE = "hookpress_access_token";
const CSRF_COOKIE = "hookpress_csrf";

type ApiFetchOptions = RequestInit & { _retry?: boolean };

let refreshPromise: Promise<string | null> | null = null;
let sessionRedirectPending = false;

function syncCookie(token: string | null) {
  if (typeof document === "undefined") return;
  if (token) {
    document.cookie = `${TOKEN_COOKIE}=${token}; path=/; max-age=604800; SameSite=Lax`;
  } else {
    document.cookie = `${TOKEN_COOKIE}=; path=/; max-age=0; SameSite=Lax`;
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
  syncCookie(token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  syncCookie(null);
}

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${name}=([^;]+)`));
  return match ? decodeURIComponent(match[1]) : null;
}

function isAuthFailure(status: number, body: { error?: { code?: string } }): boolean {
  if (status !== 401) return false;
  const code = body?.error?.code;
  return code === "invalid_token" || code === "unauthorized";
}

function redirectToLogin() {
  if (typeof window === "undefined" || sessionRedirectPending) return;
  sessionRedirectPending = true;
  const pathname = window.location.pathname;
  const localeMatch = pathname.match(/^\/(ru|en)(\/|$)/);
  const locale = localeMatch?.[1] ?? "ru";
  const redirect = encodeURIComponent(pathname + window.location.search);
  window.location.assign(
    `${window.location.origin}/${locale}/login?reason=session_expired&redirect=${redirect}`,
  );
}

async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      const token = getToken();
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      } else {
        const csrf = readCookie(CSRF_COOKIE);
        if (csrf) headers["X-CSRF-Token"] = csrf;
      }

      const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
        method: "POST",
        headers,
        credentials: "include",
      });

      if (!res.ok) {
        clearToken();
        return null;
      }

      const data = (await res.json()) as { tokens: AuthTokens };
      setToken(data.tokens.access_token);
      return data.tokens.access_token;
    } catch {
      clearToken();
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export async function logout() {
  try {
    await fetch(`${API_URL}/api/v1/auth/logout`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
      },
      credentials: "include",
    });
  } catch {
    // ignore network errors during logout
  } finally {
    clearToken();
  }
}

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<T> {
  const { _retry, ...fetchOptions } = options;
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, {
    ...fetchOptions,
    headers,
    credentials: "include",
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    if (
      isAuthFailure(res.status, err) &&
      !_retry &&
      path !== "/api/v1/auth/refresh" &&
      path !== "/api/v1/auth/dev-login"
    ) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        return apiFetch<T>(path, { ...options, _retry: true });
      }
      redirectToLogin();
    }
    throw new Error(err?.error?.message ?? res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export async function devLogin(email: string) {
  const res = await fetch(`${API_URL}/api/v1/auth/dev-login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
    credentials: "include",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message ?? res.statusText);
  }
  const data = (await res.json()) as { tokens: AuthTokens; user: User };
  setToken(data.tokens.access_token);
  return data;
}

export async function getMe() {
  return apiFetch<User>("/api/v1/users/me");
}

export type Notification = {
  id: string;
  type: string;
  title: string;
  body: string | null;
  data: Record<string, unknown> | null;
  read_at: string | null;
  created_at: string;
};

export type NotificationList = {
  items: Notification[];
  total: number;
  unread_count: number;
  has_more: boolean;
};

export async function listNotifications(unreadOnly = false) {
  const q = unreadOnly ? "?unread_only=true" : "";
  return apiFetch<NotificationList>(`/api/v1/notifications${q}`);
}

export async function markNotificationRead(id: string) {
  return apiFetch<Notification>(`/api/v1/notifications/${id}/read`, { method: "POST" });
}

export async function markAllNotificationsRead() {
  return apiFetch<{ marked: number }>("/api/v1/notifications/read-all", { method: "POST" });
}

export type Campaign = { id: string; name: string; budget_minor: number; status: string };

export async function listCampaigns() {
  return apiFetch<Campaign[]>("/api/v1/promotions/campaigns");
}

export async function createCampaign(name: string, budgetMinor = 100_000) {
  return apiFetch<Campaign>("/api/v1/promotions/campaigns", {
    method: "POST",
    body: JSON.stringify({
      name,
      budget_minor: budgetMinor,
      schedule_start: null,
      schedule_end: null,
    }),
  });
}

export type Dispute = {
  id: string;
  order_id: string;
  opened_by: string;
  status: string;
  reason: string;
  resolution: string | null;
  refund_amount_minor: number | null;
  created_at: string;
};

export async function getDispute(id: string) {
  return apiFetch<Dispute>(`/api/v1/disputes/${id}`);
}

export async function reviewDispute(id: string) {
  return apiFetch<Dispute>(`/api/v1/disputes/${id}/review`, { method: "POST" });
}

export async function resolveDispute(id: string, resolution: string, refundAmountMinor?: number) {
  return apiFetch<{ dispute: Dispute }>(`/api/v1/disputes/${id}/resolve`, {
    method: "POST",
    body: JSON.stringify({
      resolution,
      refund_amount_minor: refundAmountMinor ?? null,
    }),
  });
}

export type FeedArticle = {
  id: string;
  title: string;
  slug: string;
  summary: string | null;
  body: string;
  status: string;
  moderation_status: string;
  seo_title: string | null;
  seo_description: string | null;
  published_at: string | null;
  view_count?: number;
  like_count?: number;
  bookmark_count?: number;
  tags?: FeedTag[];
};

export type FeedTag = { id: string; slug: string; name: string };

export async function createFeedArticle(title: string, body: string) {
  return apiFetch<FeedArticle>("/api/v1/feed/articles", {
    method: "POST",
    body: JSON.stringify({ title, body }),
  });
}

export async function approveFeedArticle(id: string) {
  return apiFetch<FeedArticle>(`/api/v1/admin/feed/articles/${id}/approve`, { method: "POST" });
}

export async function rejectFeedArticle(id: string) {
  return apiFetch<FeedArticle>(`/api/v1/admin/feed/articles/${id}/reject`, { method: "POST" });
}

export type MarketOrder = {
  id: string;
  kwork_id: string;
  buyer_id: string;
  seller_id: string;
  amount_minor: number;
  status: string;
  created_at: string;
};

export async function getMarketOrder(id: string) {
  return apiFetch<MarketOrder>(`/api/v1/market/orders/${id}`);
}

export async function openDispute(orderId: string, reason: string) {
  return apiFetch<Dispute>(`/api/v1/disputes/orders/${orderId}`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export function buildKworksQuery(params: { q?: string; category?: string }) {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.category) search.set("category", params.category);
  const qs = search.toString();
  return `/api/v1/market/kworks${qs ? `?${qs}` : ""}`;
}

export type StudioProjectSummary = {
  id: string;
  title: string;
  status: string;
  genre?: string | null;
  mood?: string | null;
  updated_at?: string;
  ai_tasks?: { id: string; task_type: string; status: string }[];
};

export type OfficeProjectSummary = {
  id: string;
  title: string;
  status: string;
  releases: { id: string; title: string; status: string; release_type: string }[];
};

export async function listStudioProjects() {
  return apiFetch<{ items: StudioProjectSummary[]; total: number }>("/api/v1/studio/projects");
}

export async function listOfficeProjects() {
  return apiFetch<{ items: OfficeProjectSummary[] }>("/api/v1/office/projects");
}

export type WalletBalance = { account_id: string; balance_minor: number };

export async function getWalletBalance() {
  return apiFetch<WalletBalance>("/api/v1/billing/wallet");
}

export type SessionInfo = {
  id: string;
  created_at: string;
  expires_at: string;
  ip_address: string | null;
  user_agent: string | null;
};

export async function listSessions() {
  return apiFetch<SessionInfo[]>("/api/v1/auth/sessions");
}

export async function revokeSession(sessionId: string) {
  return apiFetch<void>(`/api/v1/auth/sessions/${sessionId}`, { method: "DELETE" });
}

export async function revokeAllSessions() {
  return apiFetch<void>("/api/v1/auth/sessions/revoke-all", { method: "POST" });
}

export type LoginEvent = {
  id: string;
  email: string;
  method: string;
  success: boolean;
  failure_reason: string | null;
  ip_address: string | null;
  created_at: string;
};

export async function listLoginEvents() {
  return apiFetch<LoginEvent[]>("/api/v1/users/me/login-events");
}

export type Kwork = {
  id: string;
  profile_id: string;
  title: string;
  description: string;
  price_minor: number;
  category: string;
  tags: string[] | null;
  status: string;
  cover_asset_id?: string | null;
  portfolio_asset_ids?: string[] | null;
  created_at: string;
};

export async function getKwork(kworkId: string) {
  return apiFetch<Kwork>(`/api/v1/market/kworks/${kworkId}`);
}

export async function listMyOrders() {
  return apiFetch<MarketOrder[]>("/api/v1/market/orders/mine");
}

export type OrderMessage = {
  id: string;
  order_id: string;
  sender_id: string;
  body: string;
  created_at: string;
};

export type OrderSpecVersion = {
  id: string;
  version_number: number;
  spec_body: string;
  created_at: string;
};

export type OrderDeliverable = {
  id: string;
  revision_number: number;
  description: string | null;
  created_at: string;
};

export async function getOrderMessages(orderId: string) {
  return apiFetch<OrderMessage[]>(`/api/v1/market/orders/${orderId}/messages`);
}

export async function sendOrderMessage(orderId: string, body: string) {
  return apiFetch<OrderMessage>(`/api/v1/market/orders/${orderId}/messages`, {
    method: "POST",
    body: JSON.stringify({ body }),
  });
}

export async function getOrderSpecVersions(orderId: string) {
  return apiFetch<OrderSpecVersion[]>(`/api/v1/market/orders/${orderId}/spec-versions`);
}

export async function createOrderSpecVersion(orderId: string, specBody: string) {
  return apiFetch<OrderSpecVersion>(`/api/v1/market/orders/${orderId}/spec-versions`, {
    method: "POST",
    body: JSON.stringify({ spec_body: specBody }),
  });
}

export async function getOrderDeliverables(orderId: string) {
  return apiFetch<OrderDeliverable[]>(`/api/v1/market/orders/${orderId}/deliverables`);
}

export async function payOrder(orderId: string) {
  return apiFetch<{ payment_id: string; status: string }>(`/api/v1/billing/orders/${orderId}/pay`, {
    method: "POST",
    headers: { "Idempotency-Key": `pay-${orderId}-${Date.now()}` },
  });
}

export type LedgerEntry = {
  id: string;
  transaction_id: string;
  account_id: string;
  amount_minor: number;
  entry_type: string;
  description: string;
  created_at: string;
};

export async function listWalletEntries() {
  return apiFetch<LedgerEntry[]>("/api/v1/billing/wallet/entries");
}

export type ChatRoom = { id: string; name: string; room_type: string; created_at: string };

export async function listChatRooms() {
  return apiFetch<ChatRoom[]>("/api/v1/chat/rooms");
}

export type ScoringReport = {
  id: string;
  release_id: string;
  track_id: string | null;
  bpm: number | null;
  energy: number | null;
  danceability: number | null;
  raw_json: Record<string, unknown> | null;
  created_at: string;
};

export async function getScoringReports(releaseId: string) {
  return apiFetch<ScoringReport[]>(`/api/v1/office/releases/${releaseId}/scoring-report`);
}

export async function likeFeedArticle(articleId: string) {
  return apiFetch<{ liked: boolean }>(`/api/v1/feed/articles/${articleId}/like`, { method: "POST" });
}

export async function bookmarkFeedArticle(articleId: string) {
  return apiFetch<{ bookmarked: boolean }>(`/api/v1/feed/articles/${articleId}/bookmark`, { method: "POST" });
}

export async function recordFeedView(articleId: string) {
  return apiFetch<{ view_count: number }>(`/api/v1/feed/articles/${articleId}/view`, { method: "POST" });
}

export type FeedComment = {
  id: string;
  article_id: string;
  user_id: string;
  body: string;
  parent_id: string | null;
  created_at: string;
};

export async function listFeedComments(articleId: string) {
  return apiFetch<FeedComment[]>(`/api/v1/feed/articles/${articleId}/comments`);
}

export async function addFeedComment(articleId: string, body: string) {
  return apiFetch<FeedComment>(`/api/v1/feed/articles/${articleId}/comments`, {
    method: "POST",
    body: JSON.stringify({ body }),
  });
}

export type KworkProfile = {
  id: string;
  user_id: string;
  title: string;
  bio: string | null;
  skills: string[] | null;
  is_active: boolean;
  created_at: string;
  kworks?: Kwork[];
};

export async function getKworkProfile(profileId: string) {
  return apiFetch<KworkProfile>(`/api/v1/market/profiles/${profileId}`);
}

export async function getKworkProfileByUser(userId: string) {
  return apiFetch<KworkProfile>(`/api/v1/market/profiles/by-user/${userId}`);
}

export async function publishKwork(kworkId: string) {
  return apiFetch<Kwork>(`/api/v1/market/kworks/${kworkId}/publish`, { method: "POST" });
}

export type DistributionJob = {
  id: string;
  release_id: string;
  provider: string;
  status: string;
  external_id: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export async function getDistributionJobs(releaseId: string) {
  return apiFetch<DistributionJob[]>(`/api/v1/office/releases/${releaseId}/distribution-jobs`);
}

export type ChartSource = {
  id: string;
  name: string;
  slug: string;
  is_mock: boolean;
  source_weights: Record<string, number>;
};

export async function getChartSource(slug: string) {
  return apiFetch<ChartSource>(`/api/v1/charts/sources/${slug}`);
}

export async function updateChartWeights(slug: string, weights: Record<string, number>) {
  return apiFetch<ChartSource>(`/api/v1/admin/charts/sources/${slug}/weights`, {
    method: "PATCH",
    body: JSON.stringify({ weights }),
  });
}

export type DisputeEvidence = {
  id: string;
  dispute_id: string;
  uploaded_by: string;
  body: string | null;
  media_asset_id: string | null;
  created_at: string;
};

export async function listDisputeEvidence(disputeId: string) {
  return apiFetch<DisputeEvidence[]>(`/api/v1/disputes/${disputeId}/evidence`);
}

export async function addDisputeEvidence(disputeId: string, body: string) {
  return apiFetch<DisputeEvidence>(`/api/v1/disputes/${disputeId}/evidence`, {
    method: "POST",
    body: JSON.stringify({ body }),
  });
}

export async function getDisputeByOrder(orderId: string) {
  return apiFetch<Dispute>(`/api/v1/disputes/by-order/${orderId}`);
}

export type FeedCategory = { id: string; slug: string; name: string };

export type FeedArticleList = {
  items: FeedArticle[];
  total: number;
  has_more: boolean;
};

export async function listFeedCategories() {
  return apiFetch<FeedCategory[]>("/api/v1/feed/categories");
}

export async function listFeedTags() {
  return apiFetch<FeedTag[]>("/api/v1/feed/tags");
}

export function buildFeedArticlesQuery(params: { category?: string; tag?: string; limit?: number; offset?: number }) {
  const search = new URLSearchParams();
  if (params.category) search.set("category", params.category);
  if (params.tag) search.set("tag", params.tag);
  if (params.limit != null) search.set("limit", String(params.limit));
  if (params.offset != null) search.set("offset", String(params.offset));
  const qs = search.toString();
  return `/api/v1/feed/articles${qs ? `?${qs}` : ""}`;
}

export async function listFeedArticles(params: { category?: string; tag?: string; limit?: number; offset?: number }) {
  return apiFetch<FeedArticleList>(buildFeedArticlesQuery(params));
}

export async function ingestRssFeed(feedUrl: string) {
  return apiFetch<{ status: string; ingested: number; feed_url: string }>("/api/v1/feed/ingest/rss", {
    method: "POST",
    body: JSON.stringify({ feed_url: feedUrl }),
  });
}

export type AuditLog = {
  id: string;
  actor_user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  metadata_json: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
};

export async function listAuditLogs(params: { limit?: number; offset?: number; actionPrefix?: string }) {
  const search = new URLSearchParams();
  if (params.limit != null) search.set("limit", String(params.limit));
  if (params.offset != null) search.set("offset", String(params.offset));
  if (params.actionPrefix) search.set("action_prefix", params.actionPrefix);
  const qs = search.toString();
  return apiFetch<{ items: AuditLog[]; total: number; has_more: boolean }>(
    `/api/v1/admin/audit-logs${qs ? `?${qs}` : ""}`,
  );
}

export async function getKworkPreviewUrl(kworkId: string) {
  return apiFetch<{ url: string; expires_in: number }>(`/api/v1/market/kworks/${kworkId}/preview-url`);
}

export async function setKworkCover(kworkId: string, coverAssetId: string) {
  return apiFetch<Kwork>(`/api/v1/market/kworks/${kworkId}/cover`, {
    method: "PATCH",
    body: JSON.stringify({ cover_asset_id: coverAssetId }),
  });
}

export async function updateOfficeTrack(trackId: string, mediaAssetId: string) {
  return apiFetch<{ id: string; media_asset_id: string | null }>(`/api/v1/office/tracks/${trackId}`, {
    method: "PATCH",
    body: JSON.stringify({ media_asset_id: mediaAssetId }),
  });
}

export async function updateOfficeRelease(
  releaseId: string,
  data: { cover_asset_id?: string | null; title?: string; release_type?: string; explicit?: boolean },
) {
  return apiFetch<{ id: string; cover_asset_id: string | null }>(`/api/v1/office/releases/${releaseId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function addKworkPortfolioAsset(kworkId: string, assetId: string) {
  return apiFetch<Kwork>(`/api/v1/market/kworks/${kworkId}/portfolio-assets`, {
    method: "POST",
    body: JSON.stringify({ asset_id: assetId }),
  });
}

export async function getKworkPortfolioUrls(kworkId: string) {
  return apiFetch<{ items: { asset_id: string; url: string; expires_in: number }[] }>(
    `/api/v1/market/kworks/${kworkId}/portfolio-urls`,
  );
}
