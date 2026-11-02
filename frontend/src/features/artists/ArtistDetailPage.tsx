import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { fetchArtist } from "../../api/library";
import { ItemNotFound } from "../../components/ItemNotFound";
import { QueryState } from "../../components/QueryState";
import { Skeleton } from "../../components/Skeleton";
import { toPositiveInt } from "../../lib/params";
import { AlbumCard } from "../albums/AlbumCard";

const notFound = <ItemNotFound noun="Artist" backTo="/artists" backLabel="Back to artists" />;

export function ArtistDetailPage() {
  const id = toPositiveInt(useParams().artistId ?? null);
  return id === undefined ? <div className="state">{notFound}</div> : <ArtistDetailView id={id} />;
}

function ArtistDetailView({ id }: { id: number }) {
  const artist = useQuery({ queryKey: ["artist", id], queryFn: () => fetchArtist(id) });
  return (
    <QueryState
      query={artist}
      noun="artist"
      skeleton={<Skeleton label="Loading artist" className="album-grid" count={6} />}
      notFound={notFound}
      isEmpty={() => false}
      empty={null}
    >
      {(data) => (
        <>
          <h1>{data.name}</h1>
          <p className="result-count">
            {`${String(data.albums.length)} ${data.albums.length === 1 ? "album" : "albums"}`}
          </p>
          {data.albums.length === 0 ? (
            <p>No albums found for this artist.</p>
          ) : (
            <ul className="album-grid">
              {data.albums.map((album) => (
                <AlbumCard key={album.id} album={album} />
              ))}
            </ul>
          )}
        </>
      )}
    </QueryState>
  );
}
