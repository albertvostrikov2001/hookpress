"use client";

import { useRef, useState } from "react";
import { Button, ProgressRail } from "@hookpress/ui";
import { uploadMediaFile } from "@/lib/media-upload";
import { useTranslations } from "next-intl";

type MediaUploadPanelProps = {
  accept?: string;
  onComplete: (assetId: string) => void;
  onError?: (message: string) => void;
  label?: string;
  disabled?: boolean;
};

export function MediaUploadPanel({
  accept = "audio/*,image/*",
  onComplete,
  onError,
  label,
  disabled,
}: MediaUploadPanelProps) {
  const t = useTranslations("media");
  const inputRef = useRef<HTMLInputElement>(null);
  const [progress, setProgress] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleFile(file: File) {
    setBusy(true);
    setProgress(0);
    try {
      const assetId = await uploadMediaFile(file, setProgress);
      onComplete(assetId);
      setProgress(null);
    } catch (e) {
      const msg = e instanceof Error ? e.message : t("uploadError");
      onError?.(msg);
      setProgress(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-2">
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        disabled={disabled || busy}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void handleFile(file);
          e.target.value = "";
        }}
      />
      <Button
        variant="secondary"
        size="sm"
        disabled={disabled || busy}
        onClick={() => inputRef.current?.click()}
      >
        {label ?? t("chooseFile")}
      </Button>
      {progress !== null && (
        <div className="space-y-1">
          <ProgressRail value={progress} max={100} />
          <p className="font-mono text-xs text-[var(--hp-fg-muted)]">
            {t("uploading")} {progress}%
          </p>
        </div>
      )}
    </div>
  );
}
