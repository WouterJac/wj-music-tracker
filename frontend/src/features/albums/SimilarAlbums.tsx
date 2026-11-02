import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";

import { fetchSimilarAlbums } from "../../api/library";
import { Skeleton } from "../../components/Skeleton";
import { AlbumCard } from "./AlbumCard";

/**
 * Albums from the collection that share genres, label, composer or era with this one.
 * It is a bonus, so a failure or an empty answer leaves it out instead of interrupting the page.
 */
export function SimilarAlbums({ albumId }: { albumId: number }) {
  const similar = useQuery({
    queryKey: ["similar", albumId],
    queryFn: () => fetchSimilarAlbums(albumId),
  });
  const { error } = similar;
  useEffect(() => {
    if (error) console.error(error);
  }, [error]);

  if (similar.isPending) {
    return <Skeleton label="Loading suggestions" className="album-grid" count={3} />;
  }
  if (similar.isError || similar.data.length === 0) return null;
  return (
    <section aria-labelledby="similar-heading" className="similar">
      <h2 id="similar-heading">You might also like</h2>
      <ul className="album-grid">
        {similar.data.map(({ album, reasons }) => (
          <AlbumCard
            key={album.id}
            album={album}
            note={
              <ul className="reasons">
                {reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            }
          />
        ))}
      </ul>
    </section>
  );
}
