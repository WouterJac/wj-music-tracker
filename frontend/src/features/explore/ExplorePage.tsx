import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { Link } from "react-router-dom";

import {
  fetchGenres,
  fetchRandomAlbums,
  fetchRediscoverAlbums,
  fetchYears,
} from "../../api/library";
import { QueryState } from "../../components/QueryState";
import { Skeleton } from "../../components/Skeleton";
import { AlbumCard } from "../albums/AlbumCard";

const RANDOM_COUNT = 6;
const REDISCOVER_COUNT = 6;

export function ExplorePage() {
  return (
    <>
      <h1>Explore</h1>
      <RandomPicks />
      <Rediscover />
      <Decades />
      <Genres />
    </>
  );
}

function RandomPicks() {
  // A pick stays put until the user asks for another, so it is not refetched on focus.
  const random = useQuery({
    queryKey: ["random-albums"],
    queryFn: () => fetchRandomAlbums({ count: RANDOM_COUNT }),
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  });
  return (
    <section aria-labelledby="random-heading">
      <h2 id="random-heading">Random picks</h2>
      <QueryState
        query={random}
        noun="random albums"
        skeleton={<Skeleton label="Loading random albums" className="album-grid" count={6} />}
        isEmpty={(data) => data.length === 0}
        empty={
          <p>
            No albums yet. Run <code>wj-music scan</code> to read your music folder.
          </p>
        }
      >
        {(data) => (
          <>
            <ul className="album-grid">
              {data.map((album) => (
                <AlbumCard key={album.id} album={album} />
              ))}
            </ul>
            <button
              type="button"
              disabled={random.isFetching}
              onClick={() => void random.refetch()}
            >
              {random.isFetching ? "Shuffling…" : "Shuffle again"}
            </button>
          </>
        )}
      </QueryState>
    </section>
  );
}

/** Albums not opened lately. A bonus, so a failure or an empty answer leaves it out. */
function Rediscover() {
  const rediscover = useQuery({
    queryKey: ["rediscover"],
    queryFn: () => fetchRediscoverAlbums(REDISCOVER_COUNT),
  });
  const { error } = rediscover;
  useEffect(() => {
    if (error) console.error(error);
  }, [error]);

  if (rediscover.isPending) {
    return (
      <Skeleton
        label="Loading albums to rediscover"
        className="album-grid"
        count={REDISCOVER_COUNT}
      />
    );
  }
  if (rediscover.isError || rediscover.data.length === 0) return null;
  return (
    <section aria-labelledby="rediscover-heading">
      <h2 id="rediscover-heading">Rediscover</h2>
      <p>Albums you have not opened in a while.</p>
      <ul className="album-grid">
        {rediscover.data.map((album) => (
          <AlbumCard key={album.id} album={album} />
        ))}
      </ul>
    </section>
  );
}

function Decades() {
  const years = useQuery({ queryKey: ["years"], queryFn: fetchYears });
  const decades = [...new Set((years.data ?? []).map((year) => Math.floor(year / 10) * 10))].sort(
    (a, b) => b - a,
  );
  if (decades.length === 0) return null;
  return (
    <section aria-labelledby="decades-heading">
      <h2 id="decades-heading">Browse by decade</h2>
      <ul className="chips">
        {decades.map((decade) => (
          <li key={decade}>
            <Link to={`/albums?decade=${String(decade)}`} className="chip">
              {`${String(decade)}s`}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}

function Genres() {
  const genres = useQuery({ queryKey: ["genres"], queryFn: fetchGenres });
  if (!genres.data || genres.data.length === 0) return null;
  return (
    <section aria-labelledby="genres-heading">
      <h2 id="genres-heading">Browse by genre</h2>
      <ul className="chips">
        {genres.data.map((genre) => (
          <li key={genre.name}>
            <Link
              to={`/albums?${new URLSearchParams({ genre: genre.name }).toString()}`}
              className="chip"
            >
              {genre.name}
              <span className="chip-count">{genre.album_count}</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
