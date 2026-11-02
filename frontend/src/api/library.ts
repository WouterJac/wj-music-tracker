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

export interface Track {
  id: number;
  disc: number | null;
  number: number | null;
  title: string | null;
  duration_seconds: number;
  sample_rate: number;
  bit_depth: number;
  channels: number;
  has_lyrics: boolean;
}

export interface LyricLine {
  time_seconds: number;
  text: string;
}

export interface TrackLyrics {
  plain: string | null;
  synced_lines: LyricLine[] | null;
}

export interface TrackInfo {
  id: number;
  title: string | null;
  disc: number | null;
  number: number | null;
  duration_seconds: number;
  sample_rate: number;
  bit_depth: number;
  channels: number;
  album_id: number | null;
  album_title: string | null;
  artist_id: number | null;
  artist_name: string | null;
  cover_url: string | null;
  lyrics: TrackLyrics | null;
}

export interface LyricsHit {
  track_id: number;
  title: string | null;
  album_id: number | null;
  album_title: string | null;
  artist_id: number | null;
  artist_name: string | null;
  snippet: string;
}

export interface AlbumDetail extends Album {
  total_duration_seconds: number;
  tracks: Track[];
}

export interface ArtistDetail {
  id: number;
  name: string;
  albums: Album[];
}

/** The server answered 404: the item does not exist, which is not a failure to retry. */
export class NotFoundError extends Error {}

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

function isTrack(value: unknown): value is Track {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    isNullableOf("number", value.disc) &&
    isNullableOf("number", value.number) &&
    isNullableOf("string", value.title) &&
    typeof value.duration_seconds === "number" &&
    typeof value.sample_rate === "number" &&
    typeof value.bit_depth === "number" &&
    typeof value.channels === "number" &&
    typeof value.has_lyrics === "boolean"
  );
}

function isLyricLine(value: unknown): value is LyricLine {
  return (
    isRecord(value) && typeof value.time_seconds === "number" && typeof value.text === "string"
  );
}

function isTrackLyrics(value: unknown): value is TrackLyrics {
  return (
    isRecord(value) &&
    isNullableOf("string", value.plain) &&
    (value.synced_lines === null ||
      (Array.isArray(value.synced_lines) && value.synced_lines.every(isLyricLine)))
  );
}

function isTrackInfo(value: unknown): value is TrackInfo {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    isNullableOf("string", value.title) &&
    isNullableOf("number", value.disc) &&
    isNullableOf("number", value.number) &&
    typeof value.duration_seconds === "number" &&
    typeof value.sample_rate === "number" &&
    typeof value.bit_depth === "number" &&
    typeof value.channels === "number" &&
    isNullableOf("number", value.album_id) &&
    isNullableOf("string", value.album_title) &&
    isNullableOf("number", value.artist_id) &&
    isNullableOf("string", value.artist_name) &&
    isNullableOf("string", value.cover_url) &&
    (value.lyrics === null || isTrackLyrics(value.lyrics))
  );
}

function isLyricsHit(value: unknown): value is LyricsHit {
  return (
    isRecord(value) &&
    typeof value.track_id === "number" &&
    isNullableOf("string", value.title) &&
    isNullableOf("number", value.album_id) &&
    isNullableOf("string", value.album_title) &&
    isNullableOf("number", value.artist_id) &&
    isNullableOf("string", value.artist_name) &&
    typeof value.snippet === "string"
  );
}

function isAlbumDetail(value: unknown): value is AlbumDetail {
  return (
    isAlbum(value) &&
    isRecord(value) &&
    typeof value.total_duration_seconds === "number" &&
    Array.isArray(value.tracks) &&
    value.tracks.every(isTrack)
  );
}

function isArtistDetail(value: unknown): value is ArtistDetail {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.name === "string" &&
    Array.isArray(value.albums) &&
    value.albums.every(isAlbum)
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
  if (response.status === 404) {
    throw new NotFoundError(`${url} not found`);
  }
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
  decade?: number;
  genre?: string;
  artistId?: number;
  limit: number;
  offset: number;
}

export function fetchAlbums(filters: AlbumFilters): Promise<Page<Album>> {
  const url = withParams("/api/albums", {
    q: filters.query,
    artist_id: filters.artistId,
    year: filters.year,
    decade: filters.decade,
    genre: filters.genre,
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

export interface Bucket {
  label: string;
  count: number;
}

export interface TopArtist {
  id: number;
  name: string;
  tracks: number;
  albums: number;
}

export interface LibraryStats {
  tracks: number;
  albums: number;
  artists: number;
  total_duration_seconds: number;
  hires_tracks: number;
  albums_by_decade: Bucket[];
  albums_by_year: Bucket[];
  tracks_by_format: Bucket[];
  tracks_by_channels: Bucket[];
  tracks_by_genre: Bucket[];
  albums_by_track_count: Bucket[];
  albums_by_length: Bucket[];
  top_artists: TopArtist[];
}

function isBucketList(value: unknown): value is Bucket[] {
  return (
    Array.isArray(value) &&
    value.every(
      (item) => isRecord(item) && typeof item.label === "string" && typeof item.count === "number",
    )
  );
}

function isTopArtistList(value: unknown): value is TopArtist[] {
  return (
    Array.isArray(value) &&
    value.every(
      (item) =>
        isRecord(item) &&
        typeof item.id === "number" &&
        typeof item.name === "string" &&
        typeof item.tracks === "number" &&
        typeof item.albums === "number",
    )
  );
}

function isLibraryStats(value: unknown): value is LibraryStats {
  return (
    isRecord(value) &&
    typeof value.tracks === "number" &&
    typeof value.albums === "number" &&
    typeof value.artists === "number" &&
    typeof value.total_duration_seconds === "number" &&
    typeof value.hires_tracks === "number" &&
    isBucketList(value.albums_by_decade) &&
    isBucketList(value.albums_by_year) &&
    isBucketList(value.tracks_by_format) &&
    isBucketList(value.tracks_by_channels) &&
    isBucketList(value.tracks_by_genre) &&
    isBucketList(value.albums_by_track_count) &&
    isBucketList(value.albums_by_length) &&
    isTopArtistList(value.top_artists)
  );
}

export function fetchStats(): Promise<LibraryStats> {
  return getJson("/api/stats", isLibraryStats);
}

export interface Fact {
  key: string;
  title: string;
  text: string;
  link: { kind: "album" | "artist" | "track"; id: number };
}

function isFactList(value: unknown): value is { items: Fact[] } {
  return (
    isRecord(value) &&
    Array.isArray(value.items) &&
    value.items.every(
      (item) =>
        isRecord(item) &&
        typeof item.key === "string" &&
        typeof item.title === "string" &&
        typeof item.text === "string" &&
        isRecord(item.link) &&
        (item.link.kind === "album" || item.link.kind === "artist" || item.link.kind === "track") &&
        typeof item.link.id === "number",
    )
  );
}

export async function fetchFacts(): Promise<Fact[]> {
  return (await getJson("/api/facts", isFactList)).items;
}

export interface SimilarAlbum {
  album: Album;
  score: number;
  reasons: string[];
}

function isSimilarList(value: unknown): value is SimilarAlbum[] {
  return (
    Array.isArray(value) &&
    value.every(
      (item) =>
        isRecord(item) &&
        isAlbum(item.album) &&
        typeof item.score === "number" &&
        Array.isArray(item.reasons) &&
        item.reasons.every((reason) => typeof reason === "string"),
    )
  );
}

export function fetchSimilarAlbums(id: number): Promise<SimilarAlbum[]> {
  return getJson(`/api/albums/${String(id)}/similar`, isSimilarList);
}

export interface GenreCount {
  name: string;
  album_count: number;
}

function isAlbumList(value: unknown): value is Album[] {
  return Array.isArray(value) && value.every(isAlbum);
}

function isGenreList(value: unknown): value is GenreCount[] {
  return (
    Array.isArray(value) &&
    value.every(
      (item) =>
        isRecord(item) && typeof item.name === "string" && typeof item.album_count === "number",
    )
  );
}

export interface RandomAlbumFilters {
  count: number;
  decade?: number;
  genre?: string;
}

export function fetchRediscoverAlbums(count: number): Promise<Album[]> {
  return getJson(withParams("/api/albums/rediscover", { count }), isAlbumList);
}

/** Tells the backend this album was looked at, so rediscover can leave it for later. */
export async function recordAlbumView(id: number): Promise<void> {
  const response = await fetch(`/api/albums/${String(id)}/view`, { method: "POST" });
  if (!response.ok) {
    throw new Error(
      `Recording a view of album ${String(id)} responded with ${String(response.status)}`,
    );
  }
}

export function fetchRandomAlbums(filters: RandomAlbumFilters): Promise<Album[]> {
  const url = withParams("/api/albums/random", {
    count: filters.count,
    decade: filters.decade,
    genre: filters.genre,
  });
  return getJson(url, isAlbumList);
}

export function fetchGenres(): Promise<GenreCount[]> {
  return getJson("/api/genres", isGenreList);
}

export function fetchYears(): Promise<number[]> {
  return getJson("/api/years", isYearList);
}

export function fetchAlbum(id: number): Promise<AlbumDetail> {
  return getJson(`/api/albums/${String(id)}`, isAlbumDetail);
}

export function fetchArtist(id: number): Promise<ArtistDetail> {
  return getJson(`/api/artists/${String(id)}`, isArtistDetail);
}

export function fetchTrack(id: number): Promise<TrackInfo> {
  return getJson(`/api/tracks/${String(id)}`, isTrackInfo);
}

export interface LyricsSearchFilters {
  query: string;
  limit: number;
  offset: number;
}

export function searchLyrics(filters: LyricsSearchFilters): Promise<Page<LyricsHit>> {
  const url = withParams("/api/lyrics/search", {
    q: filters.query,
    limit: filters.limit,
    offset: filters.offset,
  });
  return getJson(url, pageOf(isLyricsHit));
}
