import { getToken } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const CHUNK_SIZE = 5 * 1024 * 1024;
const MAX_RETRIES = 3;

type UploadPart = { PartNumber: number; ETag: string };

export async function uploadMediaFile(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<string> {
  const token = getToken();
  if (!token) throw new Error("Authentication required");

  const authHeaders = { Authorization: `Bearer ${token}` };

  const initRes = await fetch(`${API_URL}/api/v1/media/uploads/initiate`, {
    method: "POST",
    headers: { ...authHeaders, "Content-Type": "application/json" },
    body: JSON.stringify({
      filename: file.name,
      content_type: file.type || "application/octet-stream",
      total_size: file.size,
    }),
  });
  if (!initRes.ok) {
    throw new Error(`Upload initiate failed: ${initRes.statusText}`);
  }
  const init = (await initRes.json()) as { upload_id: string };
  const uploadId = init.upload_id;

  const totalParts = Math.max(1, Math.ceil(file.size / CHUNK_SIZE));
  const parts: UploadPart[] = [];

  for (let i = 0; i < totalParts; i++) {
    const partNumber = i + 1;
    const chunk = file.slice(i * CHUNK_SIZE, (i + 1) * CHUNK_SIZE);
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
      try {
        const form = new FormData();
        form.append("part_number", String(partNumber));
        form.append("file", chunk, file.name);
        const partRes = await fetch(`${API_URL}/api/v1/media/uploads/${uploadId}/parts`, {
          method: "POST",
          headers: authHeaders,
          body: form,
        });
        if (!partRes.ok) {
          throw new Error(partRes.statusText);
        }
        const part = (await partRes.json()) as { part_number: number; etag: string };
        parts.push({ PartNumber: part.part_number, ETag: part.etag });
        lastError = null;
        break;
      } catch (e) {
        lastError = e instanceof Error ? e : new Error("Part upload failed");
        if (attempt < MAX_RETRIES - 1) {
          await new Promise((r) => setTimeout(r, 500 * (attempt + 1)));
        }
      }
    }

    if (lastError) throw lastError;
    onProgress?.(Math.round(((i + 1) / totalParts) * 100));
  }

  const completeRes = await fetch(`${API_URL}/api/v1/media/uploads/${uploadId}/complete`, {
    method: "POST",
    headers: { ...authHeaders, "Content-Type": "application/json" },
    body: JSON.stringify({ parts }),
  });
  if (!completeRes.ok) {
    throw new Error(`Upload complete failed: ${completeRes.statusText}`);
  }
  const asset = (await completeRes.json()) as { id: string };
  return asset.id;
}
