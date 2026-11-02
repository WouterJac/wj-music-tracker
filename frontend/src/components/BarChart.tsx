import { Link } from "react-router-dom";

export interface BarItem {
  label: string;
  count: number;
  /** Makes the row a link, for charts whose rows are things you can open. */
  href?: string;
}

interface BarChartProps {
  title: string;
  /** Singular noun for what is counted ("album"); read out with each value. */
  unit: string;
  items: BarItem[];
}

/**
 * A horizontal bar chart built from a list, so the data is plain text for screen readers.
 * The bars are decoration: the count is printed next to each one, never encoded by colour alone.
 */
export function BarChart({ title, unit, items }: BarChartProps) {
  const max = Math.max(1, ...items.map((item) => item.count));
  const headingId = `chart-${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
  return (
    <figure className="chart" aria-labelledby={headingId}>
      <figcaption id={headingId}>{title}</figcaption>
      {items.length === 0 ? (
        <p className="chart-empty">No data yet.</p>
      ) : (
        <ul className="bars">
          {items.map((item) => (
            <li key={item.label}>
              <Row item={item} unit={unit} max={max} />
            </li>
          ))}
        </ul>
      )}
    </figure>
  );
}

function Row({ item, unit, max }: { item: BarItem; unit: string; max: number }) {
  const content = (
    <>
      <span className="bar-label">{item.label}</span>
      <span className="bar-track" aria-hidden="true">
        <span className="bar-fill" style={{ width: `${String((item.count / max) * 100)}%` }} />
      </span>
      <span className="bar-value" aria-hidden="true">
        {item.count}
      </span>
      <span className="visually-hidden">
        {`${String(item.count)} ${item.count === 1 ? unit : `${unit}s`}`}
      </span>
    </>
  );
  return item.href ? (
    <Link to={item.href} className="bar-row">
      {content}
    </Link>
  ) : (
    <div className="bar-row">{content}</div>
  );
}
