import { Navigate, Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { NotFound } from "./components/NotFound";
import { AlbumsPage } from "./features/albums/AlbumsPage";
import { ArtistsPage } from "./features/artists/ArtistsPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/albums" replace />} />
        <Route path="albums" element={<AlbumsPage />} />
        <Route path="artists" element={<ArtistsPage />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
