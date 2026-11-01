import { Navigate, Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { NotFound } from "./components/NotFound";
import { AlbumDetailPage } from "./features/albums/AlbumDetailPage";
import { AlbumsPage } from "./features/albums/AlbumsPage";
import { ArtistDetailPage } from "./features/artists/ArtistDetailPage";
import { ArtistsPage } from "./features/artists/ArtistsPage";
import { LyricsSearchPage } from "./features/lyrics/LyricsSearchPage";
import { StatsPage } from "./features/stats/StatsPage";
import { TrackPage } from "./features/tracks/TrackPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/albums" replace />} />
        <Route path="albums" element={<AlbumsPage />} />
        <Route path="albums/:albumId" element={<AlbumDetailPage />} />
        <Route path="artists" element={<ArtistsPage />} />
        <Route path="artists/:artistId" element={<ArtistDetailPage />} />
        <Route path="tracks/:trackId" element={<TrackPage />} />
        <Route path="lyrics" element={<LyricsSearchPage />} />
        <Route path="stats" element={<StatsPage />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
