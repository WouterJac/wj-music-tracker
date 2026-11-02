import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { fetchFacts, type Fact } from "../../api/library";
import { QueryState } from "../../components/QueryState";
import { Skeleton } from "../../components/Skeleton";

export function FactsPage() {
  const facts = useQuery({ queryKey: ["facts"], queryFn: fetchFacts });
  return (
    <>
      <h1>Facts</h1>
      <QueryState
        query={facts}
        noun="facts"
        skeleton={<Skeleton label="Loading facts" className="facts" count={4} />}
        isEmpty={(data) => data.length === 0}
        empty={
          <p>
            No facts yet. Run <code>wj-music scan</code> to read your music folder.
          </p>
        }
      >
        {(data) => (
          <ul className="facts">
            {data.map((fact) => (
              <li key={fact.key} className="fact">
                <FactCard fact={fact} />
              </li>
            ))}
          </ul>
        )}
      </QueryState>
    </>
  );
}

function FactCard({ fact }: { fact: Fact }) {
  return (
    <>
      <h2>{fact.title}</h2>
      <p>{fact.text}</p>
      <Link
        to={`/${fact.link.kind}s/${String(fact.link.id)}`}
        aria-label={`View ${fact.link.kind} for ${fact.title}`}
      >
        {`View ${fact.link.kind}`}
      </Link>
    </>
  );
}
