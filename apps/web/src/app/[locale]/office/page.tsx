"use client";

import { useEffect, useState } from "react";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Input,
  SkeletonCard,
  StatusStepper,
  useToast,
} from "@hookpress/ui";
import { DistributionLog } from "@/components/office/DistributionLog";
import { MediaUploadPanel } from "@/components/media/MediaUploadPanel";
import { ScoringCard } from "@/components/office/ScoringCard";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import { useRouter } from "@/i18n/navigation";
import { apiFetch, getDistributionJobs, getScoringReports, getToken, updateOfficeRelease, updateOfficeTrack, type DistributionJob, type ScoringReport } from "@/lib/api";
import { useTranslations } from "next-intl";

type Track = {
  id: string;
  title: string;
  position: number;
  media_asset_id: string | null;
  isrc: string | null;
  is_test_code: boolean;
};

type Release = {
  id: string;
  title: string;
  status: string;
  release_type: string;
  explicit: boolean;
  cover_asset_id: string | null;
  upc: string | null;
  is_test_code: boolean;
};

type OfficeProject = {
  id: string;
  title: string;
  status: string;
  tracks: Track[];
  releases: Release[];
};

const RELEASE_STEPS = ["DRAFT", "VALIDATING", "MODERATION", "DELIVERED", "RELEASED"] as const;

export default function OfficePage() {
  const t = useTranslations("office");
  const router = useRouter();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [projects, setProjects] = useState<OfficeProject[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [releaseTitle, setReleaseTitle] = useState("");
  const [releaseType, setReleaseType] = useState("SINGLE");
  const [explicit, setExplicit] = useState(false);
  const [trackTitle, setTrackTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const [scoring, setScoring] = useState<ScoringReport[]>([]);
  const [distribution, setDistribution] = useState<DistributionJob[]>([]);

  const selected = projects.find((p) => p.id === selectedId) ?? null;
  const release = selected?.releases[0] ?? null;

  const stepLabels = {
    DRAFT: t("stepDraft"),
    VALIDATING: t("stepValidating"),
    MODERATION: t("stepModeration"),
    DELIVERED: t("stepDelivered"),
    RELEASED: t("stepReleased"),
    REJECTED: t("stepRejected"),
    FAILED: t("stepFailed"),
  };

  async function loadProjects() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<{ items: OfficeProject[] }>("/api/v1/office/projects");
      setProjects(data.items ?? []);
      if (!selectedId && data.items?.length) {
        selectProject(data.items[0]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : t("error"));
    } finally {
      setLoading(false);
    }
  }

  function selectProject(p: OfficeProject) {
    setSelectedId(p.id);
    const r = p.releases[0];
    if (r) {
      setReleaseTitle(r.title);
      setReleaseType(r.release_type);
      setExplicit(r.explicit);
    }
  }

  useEffect(() => {
    if (!getToken()) router.push("/login");
    else void loadProjects();
  }, [router]);

  useEffect(() => {
    if (!release?.id) {
      setScoring([]);
      setDistribution([]);
      return;
    }
    void getScoringReports(release.id)
      .then(setScoring)
      .catch(() => setScoring([]));
    void getDistributionJobs(release.id)
      .then(setDistribution)
      .catch(() => setDistribution([]));
  }, [release?.id]);

  async function saveRelease() {
    if (!release) return;
    setBusy(true);
    try {
      await apiFetch(`/api/v1/office/releases/${release.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          title: releaseTitle,
          release_type: releaseType,
          explicit,
          is_test_code: true,
          upc: "TEST-UPC-WEB",
        }),
      });
      toast(t("save"), "success");
      await loadProjects();
    } catch (e) {
      toast(e instanceof Error ? e.message : t("error"), "error");
    } finally {
      setBusy(false);
    }
  }

  async function addTrack() {
    if (!release || !trackTitle) return;
    setBusy(true);
    try {
      await apiFetch(`/api/v1/office/releases/${release.id}/tracks`, {
        method: "POST",
        body: JSON.stringify({ title: trackTitle, is_test_code: true, isrc: "TEST-ISRC-WEB" }),
      });
      setTrackTitle("");
      await loadProjects();
    } catch (e) {
      toast(e instanceof Error ? e.message : t("error"), "error");
    } finally {
      setBusy(false);
    }
  }

  async function markReady() {
    if (!selected) return;
    setBusy(true);
    try {
      await apiFetch(`/api/v1/office/projects/${selected.id}/ready`, { method: "POST" });
      await loadProjects();
    } catch (e) {
      toast(e instanceof Error ? e.message : t("error"), "error");
    } finally {
      setBusy(false);
    }
  }

  async function submitRelease() {
    if (!release) return;
    setBusy(true);
    try {
      await apiFetch(`/api/v1/office/releases/${release.id}/submit`, { method: "POST" });
      await loadProjects();
    } catch (e) {
      toast(e instanceof Error ? e.message : t("error"), "error");
    } finally {
      setBusy(false);
    }
  }

  const releaseStatus = release?.status ?? "DRAFT";
  const failedId = releaseStatus === "REJECTED" || releaseStatus === "FAILED" ? releaseStatus : undefined;
  const currentStep = failedId ?? (RELEASE_STEPS.includes(releaseStatus as (typeof RELEASE_STEPS)[number]) ? releaseStatus : "DRAFT");

  return (
    <>
      <PageShell size="wide">
        <PageHeader title={t("title")} subtitle={t("subtitle")} />

        {loading && (
          <div className="grid gap-4 lg:grid-cols-3">
            <SkeletonCard />
            <SkeletonCard />
          </div>
        )}

        {error && (
          <Card className="mb-6 border-[var(--hp-danger)]/30">
            <p className="text-sm text-[var(--hp-danger)]">{error}</p>
            <Button variant="secondary" className="mt-3" onClick={() => void loadProjects()}>
              {t("retry")}
            </Button>
          </Card>
        )}

        {!loading && !error && projects.length === 0 && (
          <EmptyState
            title={t("emptyTitle")}
            description={t("emptyDescription")}
            actionLabel={t("emptyCta")}
            onAction={() => router.push("/studio")}
          />
        )}

        {!loading && projects.length > 0 && (
          <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
            <Card padding="sm">
              <h2 className="mb-3 font-display text-sm font-semibold uppercase tracking-wide text-[var(--hp-fg-muted)]">
                {t("projects")}
              </h2>
              <ul className="space-y-2">
                {projects.map((p) => (
                  <li key={p.id}>
                    <button
                      type="button"
                      onClick={() => selectProject(p)}
                      className={`w-full rounded-[var(--hp-radius)] border p-3 text-left transition ${
                        selectedId === p.id
                          ? "border-[var(--hp-accent)] bg-[var(--hp-accent-muted)]"
                          : "border-[var(--hp-border)] hover:border-[var(--hp-accent)]/40"
                      }`}
                    >
                      <p className="font-medium">{p.title}</p>
                      <p className="font-mono text-xs text-[var(--hp-fg-muted)]">{p.status}</p>
                    </button>
                  </li>
                ))}
              </ul>
            </Card>

            {selected && release && (
              <div className="space-y-6">
                <Card>
                  <div className="mb-6 overflow-x-auto">
                    <StatusStepper
                      steps={[
                        { id: "DRAFT", label: stepLabels.DRAFT },
                        { id: "VALIDATING", label: stepLabels.VALIDATING },
                        { id: "MODERATION", label: stepLabels.MODERATION },
                        { id: "DELIVERED", label: stepLabels.DELIVERED },
                        { id: "RELEASED", label: stepLabels.RELEASED },
                      ]}
                      currentId={currentStep}
                      failedId={failedId}
                    />
                  </div>
                  <div className="mb-4 flex items-center gap-2">
                    <h2 className="font-display text-lg font-semibold">{t("release")}</h2>
                    <Badge variant="accent">{release.status}</Badge>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <Input label={t("releaseTitle")} value={releaseTitle} onChange={(e) => setReleaseTitle(e.target.value)} />
                    <label className="block space-y-1.5 text-sm">
                      <span className="text-[var(--hp-fg-muted)]">{t("releaseType")}</span>
                      <select
                        value={releaseType}
                        onChange={(e) => setReleaseType(e.target.value)}
                        className="w-full rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-bg-elevated)] px-3 py-2"
                      >
                        <option value="SINGLE">Single</option>
                        <option value="EP">EP</option>
                        <option value="ALBUM">Album</option>
                      </select>
                    </label>
                  </div>
                  <label className="mt-4 flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={explicit} onChange={(e) => setExplicit(e.target.checked)} />
                    {t("explicit")}
                  </label>
                  <div className="mt-4 border-t border-[var(--hp-border)] pt-4">
                    <p className="mb-2 text-sm font-medium">{t("releaseCover")}</p>
                    {release.cover_asset_id ? (
                      <p className="mb-2 font-mono text-xs text-[var(--hp-success)]">✓ {t("coverAttached")}</p>
                    ) : (
                      <MediaUploadPanel
                        accept="image/*"
                        label={t("uploadReleaseCover")}
                        onComplete={(assetId) => {
                          void updateOfficeRelease(release.id, { cover_asset_id: assetId })
                            .then(() => loadProjects())
                            .then(() => toast(t("coverAttached"), "success"))
                            .catch((e) => toast(e instanceof Error ? e.message : t("error"), "error"));
                        }}
                        onError={(msg) => toast(msg, "error")}
                      />
                    )}
                  </div>
                  <div className="mt-6 flex flex-wrap gap-2">
                    <Button onClick={() => void saveRelease()} disabled={busy}>
                      {t("save")}
                    </Button>
                    <Button variant="secondary" onClick={() => void markReady()} disabled={busy}>
                      {t("markReady")}
                    </Button>
                    <Button variant="secondary" onClick={() => void submitRelease()} disabled={busy}>
                      {t("submit")}
                    </Button>
                  </div>
                </Card>

                <Card>
                  <h3 className="mb-3 font-display font-semibold">
                    {t("tracks")} ({selected.tracks.length})
                  </h3>
                  <ul className="mb-4 space-y-3 text-sm">
                    {selected.tracks.map((tr) => (
                      <li key={tr.id} className="rounded border border-[var(--hp-border)] p-3">
                        <p className="font-mono text-[var(--hp-fg-muted)]">
                          {tr.position}. {tr.title}
                          {tr.isrc ? ` · ${tr.isrc}` : ""}
                          {tr.media_asset_id && (
                            <span className="ml-2 text-[var(--hp-success)]">✓ media</span>
                          )}
                        </p>
                        {!tr.media_asset_id && (
                          <MediaUploadPanel
                            accept="audio/*"
                            label={t("uploadTrackMedia")}
                            onComplete={(assetId) => {
                              void updateOfficeTrack(tr.id, assetId)
                                .then(() => loadProjects())
                                .then(() => toast(t("trackMediaAttached"), "success"))
                                .catch((e) => toast(e instanceof Error ? e.message : t("error"), "error"));
                            }}
                            onError={(msg) => toast(msg, "error")}
                          />
                        )}
                      </li>
                    ))}
                  </ul>
                  <div className="flex gap-2">
                    <Input
                      className="flex-1"
                      placeholder={t("trackTitlePlaceholder")}
                      value={trackTitle}
                      onChange={(e) => setTrackTitle(e.target.value)}
                    />
                    <Button variant="secondary" onClick={() => void addTrack()} disabled={busy || !trackTitle}>
                      {t("addTrack")}
                    </Button>
                  </div>
                </Card>

                <ScoringCard reports={scoring} />
                <DistributionLog jobs={distribution} />
              </div>
            )}
          </div>
        )}
      </PageShell>
      <Footer />
    </>
  );
}
