const TOKEN_ENDPOINT = "https://accounts.spotify.com/api/token";
const CURRENTLY_PLAYING_ENDPOINT = "https://api.spotify.com/v1/me/player/currently-playing";

type SpotifyArtist = {
  name: string;
};

type SpotifyTrack = {
  name: string;
  duration_ms: number;
  artists?: SpotifyArtist[];
  external_urls?: {
    spotify?: string;
  };
};

type SpotifyCurrentlyPlayingResponse = {
  is_playing: boolean;
  progress_ms: number | null;
  item: SpotifyTrack | null;
  currently_playing_type?: string;
};

export type NowPlayingTrack = {
  isPlaying: boolean;
  title: string;
  artist: string;
  progressMs: number;
  durationMs: number;
  spotifyUrl: string | null;
};

function requiredEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

export async function getSpotifyAccessToken(): Promise<string> {
  const clientId = requiredEnv("SPOTIFY_CLIENT_ID");
  const clientSecret = requiredEnv("SPOTIFY_CLIENT_SECRET");
  const refreshToken = requiredEnv("SPOTIFY_REFRESH_TOKEN");
  const credentials = Buffer.from(`${clientId}:${clientSecret}`).toString("base64");

  const response = await fetch(TOKEN_ENDPOINT, {
    method: "POST",
    headers: {
      Authorization: `Basic ${credentials}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      refresh_token: refreshToken,
    }),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Spotify token request failed with ${response.status}: ${body}`);
  }

  const payload = (await response.json()) as { access_token?: string };
  if (!payload.access_token) {
    throw new Error("Spotify token response did not include an access token.");
  }

  return payload.access_token;
}

export async function getCurrentlyPlaying(): Promise<NowPlayingTrack | null> {
  const accessToken = await getSpotifyAccessToken();

  const response = await fetch(CURRENTLY_PLAYING_ENDPOINT, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (response.status === 204) {
    return null;
  }

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Spotify currently-playing request failed with ${response.status}: ${body}`);
  }

  const payload = (await response.json()) as SpotifyCurrentlyPlayingResponse;
  if (!payload.item) {
    return null;
  }

  const artist = payload.item.artists?.map((entry) => entry.name).join(", ") || "Spotify";

  return {
    isPlaying: payload.is_playing,
    title: payload.item.name,
    artist,
    progressMs: payload.progress_ms ?? 0,
    durationMs: payload.item.duration_ms,
    spotifyUrl: payload.item.external_urls?.spotify ?? null,
  };
}
