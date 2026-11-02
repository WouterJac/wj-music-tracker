import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import { fetchAlbums, fetchYears } from "../../api/library";
import { Pagination } from "../../components/Pagination";
import { QueryState } from "../../components/QueryState";
import { SearchBox } from "../../components/SearchBox";
import { Skeleton } from "../../components/Skeleton";
import { toPositiveInt, withParam } from "../../lib/params";
import { AlbumCard } from "./AlbumCard";

export const PAGE_SIZE = 24;

export function AlbumsPage() {
  const [params, setParams] = useSearchParams();
  const query = params.get("q") ?? "";
  const year = toPositiveInt(params.get("year"));
  const page = toPositiveInt(params.get("page")) ?? 1;
  const filtered = query !== "" || year !== undefined;

  const albums = useQuery({
    queryKey: ["albums", query, year, page],
    queryFn: () => fetchAlbums({ query, year, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE }),
    placeholderData: keepPreviousData,
  });
  const years = useQuery({ queryKey: ["years"], queryFn: fetchYears });

  // Changing a filter returns to the first page. Typing replaces the history entry so Back
  // leaves the page instead of stepping through every keystroke.
  function setFilter(changes: { q?: string; year?: string }) {
    setParams((current) => withParam(current, { ...changes, page: undefined }), { replace: true });
  }

  return (
    <>
      <h1>Albums</h1>
      <div className="filters" role="search">
        <SearchBox
          label="Search albums"
          value={query}
          onChange={(value) => {
            setFilter({ q: value });
          }}
        />
        <label className="field">
          <span className="field-label">Year</span>
          <select
            value={year === undefined ? "" : String(year)}
            onChange={(event) => {
              setFilter({ year: event.target.value });
            }}
          >
            <option value="">All years</option>
            {years.data?.map((value) => (
              <option key={value} value={String(value)}>
                {String(value)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <QueryState
        query={albums}
        noun="albums"
        skeleton={<Skeleton label="Loading albums" className="album-grid" count={12} />}
        isEmpty={(data) => data.items.length === 0}
        empty={
          filtered ? (
            <>
              <p>No albums match your search.</p>
              <Link to="/albums">Clear filters</Link>
            </>
          ) : (
            <p>
              No albums found. Run <code>wj-music scan</code>.
            </p>
          )
        }
      >
        {(data) => (
          <>
            <p className="result-count">{`${String(data.total)} ${data.total === 1 ? "album" : "albums"}`}</p>
            <ul className="album-grid">
              {data.items.map((album) => (
                <AlbumCard key={album.id} album={album} />
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
