import { Link } from "react-router-dom";

import type { Album } from "../../api/library";

export function coverAlt(album: Pick<Album, "title" | "artist_name">): string {
  return album.artist_name
    ? `Cover of ${album.title} by ${album.artist_name}`
    : `Cover of ${album.title}`;
}

export function AlbumCard({ album }: { album: Album }) {
  const meta = [album.artist_name, album.year].filter((part) => part !== null).join(" · ");
  return (
    <li>
      <Link to={`/albums/${String(album.id)}`} className="album-card">
        {album.cover_url ? (
          <img
            className="cover"
            src={album.cover_url}
            alt={coverAlt(album)}
            loading="lazy"
            width={300}
            height={300}
          />
        ) : (
          <span className="cover cover-placeholder" aria-hidden="true">
            ♪
          </span>
        )}
        <span className="album-title">{album.title}</span>
        <span className="album-meta" id={`album-${String(album.id)}-meta`}>
          {meta}
        </span>
      </Link>
    </li>
  );
}
