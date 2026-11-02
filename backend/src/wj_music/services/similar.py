"""Similar-album use case. Combines tag profiles with the album summaries to show."""

from wj_music.domain.repositories import LibraryReader, SimilarReader
from wj_music.domain.similar import DEFAULT_LIMIT, SimilarAlbum, rank_similar


class SimilarService:
    def __init__(self, profiles: SimilarReader, albums: LibraryReader) -> None:
        self._profiles = profiles
        self._albums = albums

    def similar_to(self, album_id: int, limit: int = DEFAULT_LIMIT) -> list[SimilarAlbum] | None:
        """Suggestions for an album, or None when there is no such album."""
        profiles = self._profiles.album_profiles()
        target = next((p for p in profiles if p.album_id == album_id), None)
        if target is None:
            return None
        ranked = rank_similar(target, profiles, limit)
        summaries = {a.id: a for a in self._albums.albums_by_ids([r.album_id for r in ranked])}
        return [
            SimilarAlbum(album=summaries[r.album_id], score=r.score, reasons=r.reasons)
            for r in ranked
            if r.album_id in summaries
        ]
