import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type SyntheticEvent } from "react";

import { pair } from "../../api/auth";

/** Shown instead of the app when the server wants an access token this browser does not have. */
export function PairingPage() {
  const queryClient = useQueryClient();
  const [code, setCode] = useState("");
  const pairing = useMutation({
    mutationFn: pair,
    // Whatever failed with 401 before is fetched again, now with the token.
    onSuccess: async () => {
      await queryClient.invalidateQueries();
    },
  });

  function submit(event: SyntheticEvent) {
    event.preventDefault();
    if (code.trim() === "") return;
    pairing.mutate(code.trim());
  }

  return (
    <main className="pairing">
      <h1>Pair this device</h1>
      <p>
        This server asks for a pairing code. Run <code>wj-music pair</code> on the PC and enter the
        code it shows. The code works once and expires after 5 minutes.
      </p>
      <form onSubmit={submit}>
        <label htmlFor="pairing-code">Pairing code</label>
        <input
          id="pairing-code"
          type="text"
          value={code}
          autoComplete="off"
          autoCapitalize="characters"
          autoCorrect="off"
          spellCheck={false}
          onChange={(event) => {
            setCode(event.target.value);
          }}
        />
        <button type="submit" disabled={pairing.isPending}>
          {pairing.isPending ? "Pairing…" : "Pair"}
        </button>
      </form>
      {pairing.isError && <p role="alert">{pairing.error.message}</p>}
    </main>
  );
}
