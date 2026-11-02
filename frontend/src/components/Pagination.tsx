interface PaginationProps {
  page: number;
  pageCount: number;
  onChange: (page: number) => void;
}

export function Pagination({ page, pageCount, onChange }: PaginationProps) {
  if (pageCount <= 1) return null;
  return (
    <nav className="pagination" aria-label="Pagination">
      <button
        type="button"
        disabled={page <= 1}
        onClick={() => {
          onChange(page - 1);
        }}
      >
        Previous page
      </button>
      <span>{`Page ${String(page)} of ${String(pageCount)}`}</span>
      <button
        type="button"
        disabled={page >= pageCount}
        onClick={() => {
          onChange(page + 1);
        }}
      >
        Next page
      </button>
    </nav>
  );
}
