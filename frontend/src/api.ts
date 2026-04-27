export type LiveConfigResponse = {
  model: string;
  systemInstruction: string;
  tools: any[];
  responseModalities: string[];
  voiceName: string;
  apiKey?: string;
};

const BACKEND_URL =
  import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";

export async function fetchLiveConfig(): Promise<LiveConfigResponse> {
  const res = await fetch(`${BACKEND_URL}/api/live/config`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch live config: ${res.statusText}`);
  }
  return (await res.json()) as LiveConfigResponse;
}

