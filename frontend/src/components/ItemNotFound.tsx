import { Link } from "react-router-dom";

interface ItemNotFoundProps {
  /** Singular noun, for example "Album". */
  noun: string;
  backTo: string;
  backLabel: string;
}

export function ItemNotFound({ noun, backTo, backLabel }: ItemNotFoundProps) {
  return (
    <>
      <h1>{`${noun} not found`}</h1>
      <p>It may have been removed from the library, or the address is wrong.</p>
      <Link to={backTo}>{backLabel}</Link>
    </>
  );
}
