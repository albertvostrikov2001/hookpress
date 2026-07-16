"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Input,
  ProgressRail,
  SkeletonCard,
  Textarea,
  useToast,
} from "@hookpress/ui";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import { WaveformBars } from "@/components/studio/WaveformBars";
import { apiFetch, getToken } from "@/lib/api";
import { useRouter } from "@/i18n/navigation";
import { useTranslations } from "next-intl";

type LyricVersion = {
  id: string;
  version_number: number;
  content: string;
  prompt: string | null;
  created_at: string;
};

type AiTask = {
  id: string;
  task_type: string;
  status: string;
  result_payload: Record<string, unknown> | null;
  result_metadata: { peaks?: number[]; duration_sec?: number } | null;
};

type Project = {
  id: string;
  title: string;
  status: string;
  theme?: string | null;
  mood?: string | null;
  genre?: string | null;
  lyric_versions: LyricVersion[];
  ai_tasks: AiTask[];
};

type SyllableLine = { line_number: number; text: string; syllables: number };

function taskProgress(status: string) {
  switch (status) {
    case "PENDING":
      return 15;
    case "PROCESSING":
      return 55;
    case "SUCCEEDED":
      return 100;
    case "FAILED":
      return 100;
    default:
      return 0;
  }
}

function taskVariant(status: string): "default" | "success" | "warning" | "danger" {
  if (status === "SUCCEEDED") return "success";
  if (status === "FAILED") return "danger";
  if (status === "PROCESSING") return "warning";
  return "default";
}

export default function StudioPage() {
  const t = useTranslations("studio");
  const router = useRouter();
  const { toast } = useToast();
  const audioRef = useRef<HTMLAudioElement>(null);
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState<Project | null>(null);
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const [editorContent, setEditorContent] = useState("");
  const [assistantInput, setAssistantInput] = useState("");
  const [syllableLines, setSyllableLines] = useState<SyllableLine[]>([]);
  const [rhymeInfo, setRhymeInfo] = useState("");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [peaks, setPeaks] = useState<number[]>([]);
  const [title, setTitle] = useState("");
  const [theme, setTheme] = useState("");
  const [mood, setMood] = useState("");
  const [genre, setGenre] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [sentToOffice, setSentToOffice] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<{ items: Project[] }>("/api/v1/studio/projects");
      setProjects(data.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("error"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    if (!getToken()) router.push("/login");
    else void load();
  }, [router, load]);

  useEffect(() => {
    if (!selected) return;
    const versions = selected.lyric_versions ?? [];
    const version =
      versions.find((v) => v.id === selectedVersionId) ??
      versions.sort((a, b) => b.version_number - a.version_number)[0];
    if (version) {
      setSelectedVersionId(version.id);
      setEditorContent(version.content);
    } else {
      setSelectedVersionId(null);
      setEditorContent("");
    }
    const audioTask = (selected.ai_tasks ?? [])
      .filter((task) => task.task_type === "GENERATE_AUDIO" && task.status === "SUCCEEDED")
      .sort((a, b) => b.id.localeCompare(a.id))[0];
    setPeaks(audioTask?.result_metadata?.peaks ?? []);
  }, [selected, selectedVersionId]);

  async function refreshProject(projectId: string) {
    const project = await apiFetch<Project>(`/api/v1/studio/projects/${projectId}`);
    setSelected(project);
    setProjects((prev) => prev.map((p) => (p.id === projectId ? project : p)));
    return project;
  }

  async function createProject() {
    const p = await apiFetch<Project>("/api/v1/studio/projects", {
      method: "POST",
      body: JSON.stringify({ title, theme, mood, genre, description: theme }),
    });
    setProjects((prev) => [p, ...prev]);
    setSelected(p);
    setTitle("");
    setTheme("");
    setMood("");
    setGenre("");
    toast(t("create"), "success");
  }

  async function saveLyrics() {
    if (!selected || !selectedVersionId) return;
    setSaving(true);
    try {
      await apiFetch(`/api/v1/studio/projects/${selected.id}/lyrics/versions/${selectedVersionId}`, {
        method: "PATCH",
        body: JSON.stringify({ content: editorContent }),
      });
      await refreshProject(selected.id);
      toast(t("save"), "success");
    } finally {
      setSaving(false);
    }
  }

  async function analyzeSyllables() {
    if (!selected) return;
    const result = await apiFetch<{ lines: SyllableLine[] }>(
      `/api/v1/studio/projects/${selected.id}/lyrics/analyze-syllables`,
      { method: "POST", body: JSON.stringify({ text: editorContent, lyric_version_id: selectedVersionId }) },
    );
    setSyllableLines(result.lines);
    setRhymeInfo("");
  }

  async function analyzeRhymes() {
    if (!selected) return;
    const result = await apiFetch<{ rhyme_groups: { ending: string; line_numbers: number[] }[] }>(
      `/api/v1/studio/projects/${selected.id}/lyrics/analyze-rhymes`,
      { method: "POST", body: JSON.stringify({ text: editorContent, lyric_version_id: selectedVersionId }) },
    );
    setRhymeInfo(
      result.rhyme_groups.map((g) => `${g.ending}: ${g.line_numbers.join(", ")}`).join("\n") || t("analysisHint"),
    );
    setSyllableLines([]);
  }

  async function askAssistant() {
    if (!selected || !assistantInput.trim()) return;
    const result = await apiFetch<{ assistant_message: string }>(
      `/api/v1/studio/projects/${selected.id}/assistant/messages`,
      { method: "POST", body: JSON.stringify({ content: assistantInput }) },
    );
    setRhymeInfo(result.assistant_message);
    setAssistantInput("");
  }

  function pollTask(projectId: string, taskId: string, refreshAudio = false) {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const token = getToken();
    const es = new EventSource(
      `${apiUrl}/api/v1/studio/projects/${projectId}/tasks/${taskId}/events${token ? `?token=${token}` : ""}`,
    );
    es.onmessage = async (ev) => {
      if (ev.data.includes("SUCCEEDED") || ev.data.includes("FAILED")) {
        es.close();
        const project = await refreshProject(projectId);
        if (refreshAudio) {
          await loadAudioUrl(projectId);
          const audioTask = (project.ai_tasks ?? []).find((task) => task.id === taskId);
          if (audioTask?.result_metadata?.peaks) setPeaks(audioTask.result_metadata.peaks);
        }
      }
    };
    es.onerror = () => {
      es.close();
      void refreshProject(projectId);
    };
  }

  async function generateLyrics(id: string) {
    const task = await apiFetch<{ id: string }>(`/api/v1/studio/projects/${id}/generate-lyrics`, {
      method: "POST",
      body: JSON.stringify({ prompt: theme || "love song" }),
    });
    pollTask(id, task.id);
  }

  async function generateAudio(id: string) {
    const task = await apiFetch<{ id: string }>(`/api/v1/studio/projects/${id}/generate-audio`, {
      method: "POST",
      body: JSON.stringify({ lyric_version_id: selectedVersionId }),
    });
    pollTask(id, task.id, true);
  }

  async function loadAudioUrl(projectId: string) {
    try {
      const res = await apiFetch<{ url: string }>(`/api/v1/studio/projects/${projectId}/audio/presigned-url`);
      setAudioUrl(res.url);
      if (audioRef.current) {
        audioRef.current.src = res.url;
        void audioRef.current.load();
      }
    } catch {
      setAudioUrl(null);
    }
  }

  async function sendToOffice(id: string) {
    if (!window.confirm(t("toOfficeConfirm"))) return;
    const res = await apiFetch<{ office_project_id: string }>(`/api/v1/studio/projects/${id}/send-to-office`, {
      method: "POST",
      headers: { "Idempotency-Key": `send-${id}` },
    });
    setSentToOffice((prev) => new Set(prev).add(id));
    toast(`${t("toOffice")}: ${res.office_project_id}`, "success");
  }

  async function selectProject(p: Project) {
    const full = await apiFetch<Project>(`/api/v1/studio/projects/${p.id}`);
    setSelected(full);
    void loadAudioUrl(p.id);
  }

  const activeTasks = (selected?.ai_tasks ?? []).filter((task) => task.status !== "CANCELLED");

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
            <Button variant="secondary" className="mt-3" onClick={() => void load()}>
              {t("retry")}
            </Button>
          </Card>
        )}

        {!loading && !error && (
          <>
            <Card className="mb-6">
              <h2 className="mb-4 font-display text-lg font-semibold">{t("newProject")}</h2>
              <div className="grid gap-4 md:grid-cols-2">
                <Input label={t("titlePlaceholder")} value={title} onChange={(e) => setTitle(e.target.value)} />
                <Input
                  label={t("themePlaceholder")}
                  value={theme}
                  maxLength={200}
                  onChange={(e) => setTheme(e.target.value)}
                  hint={t("themeCounter", { count: theme.length })}
                />
                <Input label={t("moodPlaceholder")} value={mood} onChange={(e) => setMood(e.target.value)} />
                <Input label={t("genrePlaceholder")} value={genre} onChange={(e) => setGenre(e.target.value)} />
              </div>
              <Button className="mt-4" variant="primary" onClick={() => void createProject()} disabled={!title}>
                {t("create")}
              </Button>
            </Card>

            {projects.length === 0 ? (
              <EmptyState title={t("emptyTitle")} description={t("emptyDescription")} />
            ) : (
              <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
                <Card padding="sm">
                  <h2 className="mb-3 font-display text-sm font-semibold uppercase tracking-wide text-[var(--hp-fg-muted)]">
                    {t("projects")}
                  </h2>
                  <ul className="space-y-2">
                    {projects.map((p) => (
                      <li key={p.id}>
                        <button
                          type="button"
                          onClick={() => void selectProject(p)}
                          className={`w-full rounded-[var(--hp-radius)] border p-3 text-left transition ${
                            selected?.id === p.id
                              ? "border-[var(--hp-accent)] bg-[var(--hp-accent-muted)]"
                              : "border-[var(--hp-border)] hover:border-[var(--hp-accent)]/40"
                          }`}
                        >
                          <p className="font-medium">{p.title}</p>
                          <p className="font-mono text-xs text-[var(--hp-fg-muted)]">
                            {p.genre ?? "—"} · {p.mood ?? "—"}
                          </p>
                          <Badge variant="accent" className="mt-2">
                            {p.status}
                          </Badge>
                        </button>
                      </li>
                    ))}
                  </ul>
                </Card>

                {selected ? (
                  <div className="space-y-6">
                    <div className="flex flex-wrap gap-2">
                      <Button variant="secondary" onClick={() => void generateLyrics(selected.id)}>
                        {t("lyricsAi")}
                      </Button>
                      <Button variant="secondary" onClick={() => void generateAudio(selected.id)}>
                        {t("audioBtn")}
                      </Button>
                      <Button
                        variant="primary"
                        onClick={() => void sendToOffice(selected.id)}
                        disabled={sentToOffice.has(selected.id)}
                      >
                        {sentToOffice.has(selected.id) ? t("sentToOffice") : t("toOffice")}
                      </Button>
                    </div>

                    {activeTasks.length > 0 && (
                      <Card padding="sm">
                        <h3 className="mb-3 text-sm font-semibold text-[var(--hp-fg-muted)]">{t("taskStatus")}</h3>
                        <ul className="space-y-3">
                          {activeTasks.slice(0, 5).map((task) => (
                            <li key={task.id}>
                              <p className="mb-1 font-mono text-xs">
                                {task.task_type} · {task.status}
                              </p>
                              <ProgressRail
                                value={taskProgress(task.status)}
                                variant={taskVariant(task.status)}
                                size="sm"
                                showValue={false}
                              />
                            </li>
                          ))}
                        </ul>
                      </Card>
                    )}

                    <div className="grid gap-6 xl:grid-cols-2">
                      <Card>
                        <div className="mb-3 flex items-center justify-between gap-2">
                          <h3 className="font-display font-semibold">{t("textEditor")}</h3>
                          <select
                            value={selectedVersionId ?? ""}
                            onChange={(e) => setSelectedVersionId(e.target.value)}
                            className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-bg-elevated)] px-2 py-1 text-xs font-mono"
                          >
                            {(selected.lyric_versions ?? []).map((v) => (
                              <option key={v.id} value={v.id}>
                                v{v.version_number}
                              </option>
                            ))}
                          </select>
                        </div>
                        <Textarea
                          value={editorContent}
                          onChange={(e) => setEditorContent(e.target.value)}
                          rows={14}
                          className="font-mono"
                        />
                        <div className="mt-3 flex flex-wrap gap-2">
                          <Button variant="secondary" onClick={() => void saveLyrics()} disabled={saving || !selectedVersionId}>
                            {t("save")}
                          </Button>
                          <Button variant="secondary" onClick={() => void analyzeSyllables()}>
                            {t("syllables")}
                          </Button>
                          <Button variant="secondary" onClick={() => void analyzeRhymes()}>
                            {t("rhymes")}
                          </Button>
                        </div>
                      </Card>

                      <Card>
                        <h3 className="mb-3 font-display font-semibold">{t("analysisAssistant")}</h3>
                        <div className="min-h-[220px] rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-bg-subtle)] p-3 text-sm">
                          {syllableLines.length > 0 ? (
                            <ul className="space-y-1 font-mono">
                              {syllableLines.map((line) => (
                                <li key={line.line_number}>
                                  <span className="text-[var(--hp-accent)]">{line.syllables}s</span> {line.text || "—"}
                                </li>
                              ))}
                            </ul>
                          ) : rhymeInfo ? (
                            <pre className="whitespace-pre-wrap font-mono text-[var(--hp-fg-muted)]">{rhymeInfo}</pre>
                          ) : (
                            <p className="text-[var(--hp-fg-muted)]">{t("analysisHint")}</p>
                          )}
                        </div>
                        <div className="mt-3 flex gap-2">
                          <Input
                            className="flex-1"
                            placeholder={t("assistantPlaceholder")}
                            value={assistantInput}
                            onChange={(e) => setAssistantInput(e.target.value)}
                          />
                          <Button variant="secondary" onClick={() => void askAssistant()}>
                            {t("ask")}
                          </Button>
                        </div>
                      </Card>
                    </div>

                    <Card>
                      <h3 className="mb-3 font-display font-semibold">{t("audio")}</h3>
                      <audio ref={audioRef} controls className="mb-3 w-full" src={audioUrl ?? undefined} />
                      <WaveformBars peaks={peaks} className="mb-3 h-16" />
                      <Button variant="secondary" onClick={() => void loadAudioUrl(selected.id)}>
                        {t("refreshAudio")}
                      </Button>
                    </Card>
                  </div>
                ) : (
                  <Card>
                    <p className="text-sm text-[var(--hp-fg-muted)]">{t("open")}</p>
                  </Card>
                )}
              </div>
            )}
          </>
        )}
      </PageShell>
      <Footer />
    </>
  );
}
