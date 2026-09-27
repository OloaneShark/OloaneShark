import type { VercelRequest, VercelResponse } from "@vercel/node";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { getCurrentlyPlaying, type NowPlayingTrack } from "../lib/spotify.js";

const WIDTH = 500;
const HEIGHT = 90;

function escapeXml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function truncate(value: string, maxLength: number): string {
  if (value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, Math.max(0, maxLength - 1))}...`;
}

function formatTime(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function findCassetteImage(): string | null {
  const root = process.cwd();
  const sourceDir = join(root, "assets", "cassettes", "source");
  const fallback = join(root, "assets", "cassettes", "current-spotify.png");

  try {
    if (existsSync(sourceDir)) {
      const candidates = readdirSync(sourceDir)
        .filter((name) => name.toLowerCase().endsWith(".png"))
        .map((name) => join(sourceDir, name));

      if (candidates.length > 0) {
        return candidates[Math.floor(Math.random() * candidates.length)];
      }
    }
  } catch {
    // Use fallback below.
  }

  return existsSync(fallback) ? fallback : null;
}

function cassetteArtworkSvg(): string {
  const imagePath = findCassetteImage();

  if (imagePath) {
    const base64 = readFileSync(imagePath).toString("base64");
    return `<image href="data:image/png;base64,${base64}" x="14" y="15" width="60" height="60" preserveAspectRatio="xMidYMid meet" />`;
  }

  return `
    <rect x="14" y="18" width="60" height="54" fill="#101010" stroke="#e32636" />
    <rect x="22" y="27" width="44" height="12" fill="#e32636" opacity="0.85" />
    <circle cx="31" cy="53" r="8" fill="#080808" stroke="#66f7ff" />
    <circle cx="57" cy="53" r="8" fill="#080808" stroke="#66f7ff" />
    <text x="44" y="35" text-anchor="middle" font-size="6" fill="#080808">TAPE</text>
  `;
}

function renderSvg(track: NowPlayingTrack | null, errorMessage?: string): string {
  const title = track ? truncate(track.title, 34) : errorMessage ? "SPOTIFY ERROR" : "NOTHING PLAYING";
  const artist = track ? truncate(track.artist, 40) : "cassette standby";
  const progressMs = track?.progressMs ?? 0;
  const durationMs = track?.durationMs ?? 0;
  const progressWidth = durationMs > 0 ? Math.min(1, progressMs / durationMs) * 280 : 0;
  const elapsed = track ? formatTime(progressMs) : "--:--";
  const total = track ? formatTime(durationMs) : "--:--";
  const status = track?.isPlaying ? "ON AIR" : "SPOTIFY";

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${WIDTH}" height="${HEIGHT}" viewBox="0 0 ${WIDTH} ${HEIGHT}" role="img" aria-label="Now playing on Spotify">
  <rect width="${WIDTH}" height="${HEIGHT}" fill="#070707"/>
  <rect x="1" y="1" width="${WIDTH - 2}" height="${HEIGHT - 2}" fill="none" stroke="#2a2a2a"/>
  <rect x="0" y="0" width="4" height="${HEIGHT}" fill="#e32636"/>
  ${cassetteArtworkSvg()}
  <text x="92" y="24" fill="#e32636" font-family="monospace" font-size="10">${escapeXml(status)}</text>
  <text x="92" y="43" fill="#f2f2f2" font-family="monospace" font-size="16" font-weight="700">${escapeXml(title)}</text>
  <text x="92" y="59" fill="#66f7ff" font-family="monospace" font-size="11">${escapeXml(artist)}</text>
  <rect x="92" y="70" width="280" height="5" fill="#1a1a1a"/>
  <rect x="92" y="70" width="${progressWidth.toFixed(1)}" height="5" fill="#e32636"/>
  <text x="382" y="76" fill="#cfcfcf" font-family="monospace" font-size="10">${elapsed} / ${total}</text>
  <rect x="454" y="22" width="4" height="9" fill="#66f7ff"/>
  <rect x="462" y="17" width="4" height="14" fill="#e32636"/>
  <rect x="470" y="25" width="4" height="6" fill="#66f7ff"/>
  <text x="454" y="54" fill="#777777" font-family="monospace" font-size="8">SPOTIFY</text>
</svg>`;
}

export default async function handler(req: VercelRequest, res: VercelResponse): Promise<void> {
  res.setHeader("Cache-Control", "s-maxage=1, stale-while-revalidate");

  let track: NowPlayingTrack | null = null;
  let errorMessage: string | undefined;

  try {
    track = await getCurrentlyPlaying();
  } catch (error) {
    errorMessage = error instanceof Error ? error.message : "Unknown Spotify error";
  }

  if (req.query.open === "1" && track?.spotifyUrl) {
    res.redirect(302, track.spotifyUrl);
    return;
  }

  res.setHeader("Content-Type", "image/svg+xml; charset=utf-8");
  res.status(200).send(renderSvg(track, errorMessage));
}
