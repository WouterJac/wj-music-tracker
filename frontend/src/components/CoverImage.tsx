import { useEffect, useState, type ComponentProps } from "react";

import { apiFetch, getToken } from "../api/auth";

type CoverImageProps = Omit<ComponentProps<"img">, "src"> & { src: string };

/**
 * A cover image. An <img> cannot send the access token, so once the browser has paired the
 * image is fetched with the token and shown from a blob. Before that it is a plain image.
 */
export function CoverImage({ src, ...imgProps }: CoverImageProps) {
  const token = getToken();
  const [blobUrl, setBlobUrl] = useState<string | null>(null);

  useEffect(() => {
    if (token === null) return;
    let cancelled = false;
    let objectUrl: string | null = null;
    apiFetch(src)
      .then((response) => (response.ok ? response.blob() : null))
      .then((blob) => {
        if (blob === null || cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setBlobUrl(objectUrl);
      })
      .catch((error: unknown) => {
        console.error(error);
      });
    return () => {
      cancelled = true;
      if (objectUrl !== null) URL.revokeObjectURL(objectUrl);
    };
  }, [src, token]);

  if (token === null) {
    return <img src={src} {...imgProps} />;
  }
  if (blobUrl === null) {
    return (
      <span className={`${imgProps.className ?? ""} cover-placeholder`.trim()} aria-hidden="true">
        ♪
      </span>
    );
  }
  return <img src={blobUrl} {...imgProps} />;
}
