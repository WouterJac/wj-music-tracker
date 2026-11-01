interface SkeletonProps {
  /** Accessible name, for example "Loading albums". */
  label: string;
  count?: number;
  className: string;
}

/** Placeholder with the final layout's shape, announced to screen readers as a status. */
export function Skeleton({ label, count = 8, className }: SkeletonProps) {
  return (
    <div role="status" aria-label={label} className={className}>
      <span className="visually-hidden">{`${label}…`}</span>
      {Array.from({ length: count }, (_, index) => (
        <div key={index} className="skeleton-item" aria-hidden="true" />
      ))}
    </div>
  );
}
