import type {
  Album,
  AlbumDetail,
  Artist,
  ArtistDetail,
  LyricsHit,
  Track,
  TrackInfo,
} from "../api/library";

export const low: Album = {
  id: 1,
  title: "Low",
  artist_id: 1,
  artist_name: "David Bowie",
  year: 1977,
  track_count: 11,
  cover_url: "/api/albums/1/cover",
};

export const heroes: Album = {
  id: 2,
  title: '"Heroes"',
  artist_id: 1,
  artist_name: "David Bowie",
  year: 1977,
  track_count: 10,
  cover_url: null,
};

export const bowie: Artist = { id: 1, name: "David Bowie", album_count: 2 };
export const eno: Artist = { id: 2, name: "Brian Eno", album_count: 1 };

export function page<T>(items: T[], total = items.length, limit = 24, offset = 0) {
  return { items, total, limit, offset };
}

export const breakingGlass: Track = {
  id: 1,
  disc: 1,
  number: 1,
  title: "Breaking Glass",
  duration_seconds: 200,
  sample_rate: 44100,
  bit_depth: 16,
  channels: 2,
  has_lyrics: true,
};

export const speedOfLife: Track = {
  id: 2,
  disc: 1,
  number: 2,
  title: "Speed of Life",
  duration_seconds: 150,
  sample_rate: 44100,
  bit_depth: 16,
  channels: 2,
  has_lyrics: false,
};

export const lowDetail: AlbumDetail = {
  ...low,
  total_duration_seconds: 350,
  tracks: [breakingGlass, speedOfLife],
};

export const bowieDetail: ArtistDetail = { id: 1, name: "David Bowie", albums: [low, heroes] };

export const breakingGlassInfo: TrackInfo = {
  id: 1,
  title: "Breaking Glass",
  disc: null,
  number: 1,
  duration_seconds: 200,
  sample_rate: 44100,
  bit_depth: 16,
  channels: 2,
  album_id: 1,
  album_title: "Low",
  artist_id: 1,
  artist_name: "David Bowie",
  cover_url: "/api/albums/1/cover",
  lyrics: {
    plain: "Baby, I'm not special\nBreaking glass",
    synced_lines: [
      { time_seconds: 1, text: "Baby, I'm not special" },
      { time_seconds: 6.5, text: "Breaking glass" },
    ],
  },
};

export const plainOnlyInfo: TrackInfo = {
  ...breakingGlassInfo,
  id: 2,
  title: "Sky Saw",
  lyrics: { plain: "Wind in the sky\nand the moon is high", synced_lines: null },
};

export const noLyricsInfo: TrackInfo = { ...breakingGlassInfo, id: 3, lyrics: null };

export const campHit: LyricsHit = {
  track_id: 78,
  title: "Camera",
  album_id: 7,
  album_title: "The Back Room",
  artist_id: 2,
  artist_name: "Editors",
  snippet: "…Once we have black hearts / Then love dies / Look at us…",
};
