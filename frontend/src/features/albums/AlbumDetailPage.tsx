import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";

import { fetchAlbum, recordAlbumView, type AlbumDetail, type Track } from "../../api/library";
import { ItemNotFound } from "../../components/ItemNotFound";
import { QueryState } from "../../components/QueryState";
import { Skeleton } from "../../components/Skeleton";
import { formatChannels, formatQuality, formatTotalDuration } from "../../lib/format";
import { toPositiveInt } from "../../lib/params";
import { coverAlt } from "./AlbumCard";
import { SimilarAlbums } from "./SimilarAlbums";
import { TrackList } from "./TrackList";

const notFound = <ItemNotFound noun="Album" backTo="/albums" backLabel="Back to albums" />;

export function AlbumDetailPage() {
  const id = toPositiveInt(useParams().albumId ?? null);
  return id === undefined ? <div className="state">{notFound}</div> : <AlbumDetailView id={id} />;
}

/** Distinct values in the order they first appear, so a mixed album lists every format once. */
function distinct(values: string[]): string[] {
  return [...new Set(values)];
}

function TechnicalInfo({ tracks }: { tracks: Track[] }) {
  const quality = distinct(tracks.map((t) => formatQuality(t.bit_depth, t.sample_rate)));
  const channels = distinct(tracks.map((t) => formatChannels(t.channels)));
  return (
    <div role="group" aria-label="Technical info" className="technical-info">
      <dl>
        <dt>Quality</dt>
        <dd>{quality.join(", ")}</dd>
        <dt>Channels</dt>
        <dd>{channels.join(", ")}</dd>
      </dl>
    </div>
  );
}

function AlbumDetailView({ id }: { id: number }) {
  const album = useQuery({ queryKey: ["album", id], queryFn: () => fetchAlbum(id) });
  return (
    <QueryState
      query={album}
      noun="album"
      skeleton={<Skeleton label="Loading album" className="detail-skeleton" count={3} />}
      notFound={notFound}
      isEmpty={() => false}
      empty={null}
    >
      {(data) => <AlbumContent album={data} />}
    </QueryState>
  );
}

function AlbumContent({ album }: { album: AlbumDetail }) {
  // Only feeds rediscover, so a failure is logged and never shown.
  useEffect(() => {
    recordAlbumView(album.id).catch((error: unknown) => {
      console.error(error);
    });
  }, [album.id]);
  const meta = [
    album.year === null ? null : String(album.year),
    `${String(album.track_count)} ${album.track_count === 1 ? "track" : "tracks"}`,
    formatTotalDuration(album.total_duration_seconds),
  ]
    .filter((part) => part !== null)
    .join(" · ");
  return (
    <article className="album-detail">
      {album.cover_url ? (
        <img className="cover detail-cover" src={album.cover_url} alt={coverAlt(album)} />
      ) : (
        <span className="cover cover-placeholder detail-cover" aria-hidden="true">
          ♪
        </span>
      )}
      <div className="album-detail-body">
        <h1>{album.title}</h1>
        {album.artist_id !== null && album.artist_name !== null && (
          <p className="album-artist">
            <Link to={`/artists/${String(album.artist_id)}`}>{album.artist_name}</Link>
          </p>
        )}
        <p className="album-meta">{meta}</p>
        {album.tracks.length > 0 && <TechnicalInfo tracks={album.tracks} />}
      </div>
      <div className="album-tracks">
        {album.tracks.length === 0 ? (
          <p>No tracks recorded for this album.</p>
        ) : (
          <TrackList tracks={album.tracks} />
        )}
      </div>
      <div className="album-similar">
        <SimilarAlbums albumId={album.id} />
      </div>
    </article>
  );
}
