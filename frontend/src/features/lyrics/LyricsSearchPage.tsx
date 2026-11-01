import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import { searchLyrics } from "../../api/library";
import { Highlight } from "../../components/Highlight";
import { Pagination } from "../../components/Pagination";
import { QueryState } from "../../components/QueryState";
import { SearchBox } from "../../components/SearchBox";
import { Skeleton } from "../../components/Skeleton";
import { toPositiveInt, withParam } from "../../lib/params";

const PAGE_SIZE = 24;
const MIN_QUERY_LENGTH = 2;

export function LyricsSearchPage() {
  const [params, setParams] = useSearchParams();
  const query = params.get("q") ?? "";
  const trimmed = query.trim();
  const page = toPositiveInt(params.get("page")) ?? 1;

  return (
    <>
      <h1>Lyrics</h1>
      <div className="filters" role="search">
        <SearchBox
          label="Search lyrics"
          value={query}
          onChange={(value) => {
            setParams((current) => withParam(current, { q: value, page: undefined }), {
              replace: true,
            });
          }}
        />
      </div>
      {trimmed === "" ? (
        <p className="state">Search the lyrics of your whole library.</p>
      ) : trimmed.length < MIN_QUERY_LENGTH ? (
        <p className="state">{`Type at least ${String(MIN_QUERY_LENGTH)} characters to search.`}</p>
      ) : (
        <Results
          query={trimmed}
          page={page}
          onPageChange={(next) => {
            setParams((current) => withParam(current, { page: next === 1 ? undefined : next }));
            window.scrollTo({ top: 0 });
          }}
        />
      )}
    </>
  );
}

interface ResultsProps {
  query: string;
  page: number;
  onPageChange: (page: number) => void;
}

function Results({ query, page, onPageChange }: ResultsProps) {
  const results = useQuery({
    queryKey: ["lyrics", query, page],
    queryFn: () => searchLyrics({ query, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE }),
    placeholderData: keepPreviousData,
  });
  return (
    <QueryState
      query={results}
      noun="lyrics"
      skeleton={<Skeleton label="Searching lyrics" className="lyrics-hits" count={6} />}
      isEmpty={(data) => data.items.length === 0}
      empty={<p>{`No lyrics match “${query}”.`}</p>}
    >
      {(data) => (
        <>
          <p className="result-count">{`${String(data.total)} ${data.total === 1 ? "track" : "tracks"}`}</p>
          <ul className="lyrics-hits">
            {data.items.map((hit) => (
              <li key={hit.track_id}>
                <Link
                  to={`/tracks/${String(hit.track_id)}?${new URLSearchParams({ find: query }).toString()}`}
                  className="lyrics-hit"
                >
                  <span className="album-title">{hit.title ?? "Untitled track"}</span>
                  <span className="album-meta">
                    {[hit.artist_name, hit.album_title].filter((part) => part !== null).join(" · ")}
                  </span>
                  <span className="lyrics-snippet">
                    <Highlight text={hit.snippet} query={query} />
                  </span>
                </Link>
              </li>
            ))}
          </ul>
          <Pagination
            page={page}
            pageCount={Math.ceil(data.total / PAGE_SIZE)}
            onChange={onPageChange}
          />
        </>
      )}
    </QueryState>
  );
}
