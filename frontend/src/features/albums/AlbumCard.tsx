import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import type { Album } from "../../api/library";
import { CoverImage } from "../../components/CoverImage";

export function coverAlt(album: Pick<Album, "title" | "artist_name">): string {
  return album.artist_name
    ? `Cover of ${album.title} by ${album.artist_name}`
    : `Cover of ${album.title}`;
}

/** A grid card for an album. `note` is extra content shown under the link, such as reasons. */
export function AlbumCard({ album, note }: { album: Album; note?: ReactNode }) {
  const meta = [album.artist_name, album.year].filter((part) => part !== null).join(" · ");
  return (
    <li>
      <Link to={`/albums/${String(album.id)}`} className="album-card">
        {album.cover_url ? (
          <CoverImage
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
      {note}
    </li>
  );
}
