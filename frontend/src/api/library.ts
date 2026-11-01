export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Album {
  id: number;
  title: string;
  artist_id: number | null;
  artist_name: string | null;
  year: number | null;
  track_count: number;
  cover_url: string | null;
}

export interface Artist {
  id: number;
  name: string;
  album_count: number;
}

type Guard<T> = (value: unknown) => value is T;
type Record_ = Record<string, unknown>;

function isRecord(value: unknown): value is Record_ {
  return typeof value === "object" && value !== null;
}

function isNullableOf(type: "string" | "number", value: unknown): boolean {
  return value === null || typeof value === type;
}

function isAlbum(value: unknown): value is Album {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.title === "string" &&
    isNullableOf("number", value.artist_id) &&
    isNullableOf("string", value.artist_name) &&
    isNullableOf("number", value.year) &&
    typeof value.track_count === "number" &&
    isNullableOf("string", value.cover_url)
  );
}

function isArtist(value: unknown): value is Artist {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.name === "string" &&
    typeof value.album_count === "number"
  );
}

function pageOf<T>(isItem: Guard<T>): Guard<Page<T>> {
  return (value): value is Page<T> =>
    isRecord(value) &&
    Array.isArray(value.items) &&
    value.items.every(isItem) &&
    typeof value.total === "number" &&
    typeof value.limit === "number" &&
    typeof value.offset === "number";
}

function isYearList(value: unknown): value is number[] {
  return Array.isArray(value) && value.every((year) => typeof year === "number");
}

function withParams(path: string, params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `${path}?${query}` : path;
}

async function getJson<T>(url: string, isValid: Guard<T>): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${url} responded with ${String(response.status)}`);
  }
  const body: unknown = await response.json();
  if (!isValid(body)) {
    throw new Error(`${url} returned an unexpected body`);
  }
  return body;
}

export interface AlbumFilters {
  query?: string;
  year?: number;
  artistId?: number;
  limit: number;
  offset: number;
}

export function fetchAlbums(filters: AlbumFilters): Promise<Page<Album>> {
  const url = withParams("/api/albums", {
    q: filters.query,
    artist_id: filters.artistId,
    year: filters.year,
    limit: filters.limit,
    offset: filters.offset,
  });
  return getJson(url, pageOf(isAlbum));
}

export interface ArtistFilters {
  query?: string;
  limit: number;
  offset: number;
}

export function fetchArtists(filters: ArtistFilters): Promise<Page<Artist>> {
  const url = withParams("/api/artists", {
    q: filters.query,
    limit: filters.limit,
    offset: filters.offset,
  });
  return getJson(url, pageOf(isArtist));
}

export function fetchYears(): Promise<number[]> {
  return getJson("/api/years", isYearList);
}
