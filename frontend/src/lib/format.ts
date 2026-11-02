/** Track length as m:ss. */
export function formatDuration(seconds: number): string {
  const total = Math.round(seconds);
  const minutes = Math.floor(total / 60);
  const rest = total % 60;
  return `${String(minutes)}:${String(rest).padStart(2, "0")}`;
}

/** Album length in coarse units: "42 min" or "1 h 15 min". */
export function formatTotalDuration(seconds: number): string {
  const minutes = Math.max(1, Math.round(seconds / 60));
  if (minutes < 60) return `${String(minutes)} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest === 0 ? `${String(hours)} h` : `${String(hours)} h ${String(rest)} min`;
}

export function formatQuality(bitDepth: number, sampleRate: number): string {
  return `${String(bitDepth)}-bit / ${String(sampleRate / 1000)} kHz`;
}

export function formatChannels(channels: number): string {
  if (channels === 1) return "Mono";
  if (channels === 2) return "Stereo";
  return `${String(channels)} channels`;
}
