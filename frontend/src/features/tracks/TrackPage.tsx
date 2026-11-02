import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { fetchTrack, type TrackInfo, type TrackLyrics } from "../../api/library";
import { Highlight } from "../../components/Highlight";
import { ItemNotFound } from "../../components/ItemNotFound";
import { QueryState } from "../../components/QueryState";
import { SearchBox } from "../../components/SearchBox";
import { Skeleton } from "../../components/Skeleton";
import { formatChannels, formatDuration, formatQuality } from "../../lib/format";
import { countMatches } from "../../lib/highlight";
import { toPositiveInt, withParam } from "../../lib/params";
import { coverAlt } from "../albums/AlbumCard";

const notFound = <ItemNotFound noun="Track" backTo="/albums" backLabel="Back to albums" />;

export function TrackPage() {
  const id = toPositiveInt(useParams().trackId ?? null);
  return id === undefined ? <div className="state">{notFound}</div> : <TrackView id={id} />;
}

function TrackView({ id }: { id: number }) {
  const track = useQuery({ queryKey: ["track", id], queryFn: () => fetchTrack(id) });
  return (
    <QueryState
      query={track}
      noun="track"
      skeleton={<Skeleton label="Loading track" className="detail-skeleton" count={3} />}
      notFound={notFound}
      isEmpty={() => false}
      empty={null}
    >
      {(data) => <TrackContent track={data} />}
    </QueryState>
  );
}

function TrackContent({ track }: { track: TrackInfo }) {
  const meta = [
    formatDuration(track.duration_seconds),
    formatQuality(track.bit_depth, track.sample_rate),
    formatChannels(track.channels),
  ].join(" · ");
  return (
    <article className="album-detail">
      {track.cover_url && track.album_title ? (
        <img
          className="cover detail-cover"
          src={track.cover_url}
          alt={coverAlt({ title: track.album_title, artist_name: track.artist_name })}
        />
      ) : (
        <span className="cover cover-placeholder detail-cover" aria-hidden="true">
          ♪
        </span>
      )}
      <div className="album-detail-body">
        <h1>{track.title ?? "Untitled track"}</h1>
        <p className="album-artist">
          {track.artist_id !== null && track.artist_name !== null && (
            <Link to={`/artists/${String(track.artist_id)}`}>{track.artist_name}</Link>
          )}
        </p>
        {track.album_id !== null && track.album_title !== null && (
          <p className="album-meta">
            From <Link to={`/albums/${String(track.album_id)}`}>{track.album_title}</Link>
          </p>
        )}
        <p className="album-meta">{meta}</p>
      </div>
      <div className="album-tracks">
        <LyricsSection lyrics={track.lyrics} />
      </div>
    </article>
  );
}

function LyricsSection({ lyrics }: { lyrics: TrackLyrics | null }) {
  const [params, setParams] = useSearchParams();
  const [showTimes, setShowTimes] = useState(true);
  const find = params.get("find") ?? "";

  if (lyrics === null) {
    return (
      <section aria-labelledby="lyrics-heading">
        <h2 id="lyrics-heading">Lyrics</h2>
        <p>
          No lyrics found for this track. Add a lyrics tag or a matching <code>.lrc</code> file next
          to the FLAC, then run <code>wj-music scan</code>.
        </p>
      </section>
    );
  }

  const lines = lyrics.synced_lines;
  const texts = lines ? lines.map((line) => line.text) : [lyrics.plain ?? ""];
  const matches = countMatches(texts, find);

  return (
    <section aria-labelledby="lyrics-heading">
      <h2 id="lyrics-heading">Lyrics</h2>
      <div className="filters">
        <SearchBox
          label="Find in lyrics"
          value={find}
          onChange={(value) => {
            setParams((current) => withParam(current, { find: value }), { replace: true });
          }}
        />
        {lines && (
          <label className="checkbox">
            <input
              type="checkbox"
              checked={showTimes}
              onChange={(event) => {
                setShowTimes(event.target.checked);
              }}
            />
            Show timestamps
          </label>
        )}
      </div>
      {find.trim() !== "" && (
        <p className="result-count" role="status">
          {matches === 0
            ? "No matches"
            : `${String(matches)} ${matches === 1 ? "match" : "matches"}`}
        </p>
      )}
      {lines ? (
        <ol className="lyrics-lines">
          {lines.map((line, index) => (
            <li key={index}>
              {showTimes && <time className="lyric-time">{formatDuration(line.time_seconds)}</time>}
              <span>
                <Highlight text={line.text} query={find} />
              </span>
            </li>
          ))}
        </ol>
      ) : (
        <p className="lyrics-plain">
          <Highlight text={lyrics.plain ?? ""} query={find} />
        </p>
      )}
    </section>
  );
}
