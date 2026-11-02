import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import { fetchArtists } from "../../api/library";
import { Pagination } from "../../components/Pagination";
import { QueryState } from "../../components/QueryState";
import { SearchBox } from "../../components/SearchBox";
import { Skeleton } from "../../components/Skeleton";
import { toPositiveInt, withParam } from "../../lib/params";

const PAGE_SIZE = 24;

export function ArtistsPage() {
  const [params, setParams] = useSearchParams();
  const query = params.get("q") ?? "";
  const page = toPositiveInt(params.get("page")) ?? 1;

  const artists = useQuery({
    queryKey: ["artists", query, page],
    queryFn: () => fetchArtists({ query, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE }),
    placeholderData: keepPreviousData,
  });

  return (
    <>
      <h1>Artists</h1>
      <div className="filters" role="search">
        <SearchBox
          label="Search artists"
          value={query}
          onChange={(value) => {
            setParams((current) => withParam(current, { q: value, page: undefined }), {
              replace: true,
            });
          }}
        />
      </div>
      <QueryState
        query={artists}
        noun="artists"
        skeleton={<Skeleton label="Loading artists" className="artist-list" count={8} />}
        isEmpty={(data) => data.items.length === 0}
        empty={
          query === "" ? (
            <p>
              No artists found. Run <code>wj-music scan</code>.
            </p>
          ) : (
            <>
              <p>No artists match your search.</p>
              <Link to="/artists">Clear search</Link>
            </>
          )
        }
      >
        {(data) => (
          <>
            <ul className="artist-list">
              {data.items.map((artist) => (
                <li key={artist.id}>
                  <Link to={`/artists/${String(artist.id)}`} className="artist-row">
                    <span className="artist-name">{artist.name}</span>
                    <span className="artist-count">
                      {`${String(artist.album_count)} ${artist.album_count === 1 ? "album" : "albums"}`}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
            <Pagination
              page={page}
              pageCount={Math.ceil(data.total / PAGE_SIZE)}
              onChange={(next) => {
                setParams((current) => withParam(current, { page: next === 1 ? undefined : next }));
                window.scrollTo({ top: 0 });
              }}
            />
          </>
        )}
      </QueryState>
    </>
  );
}
