import type { Album, AlbumDetail, Artist, ArtistDetail, Track } from "../api/library";

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
};

export const lowDetail: AlbumDetail = {
  ...low,
  total_duration_seconds: 350,
  tracks: [breakingGlass, speedOfLife],
};

export const bowieDetail: ArtistDetail = { id: 1, name: "David Bowie", albums: [low, heroes] };
