# Frontend patterns

## Layout rules (apply from phase 0)
- Mobile-first CSS. Design for a narrow viewport, then widen.
- A 16px side gutter on every page. No horizontal page scroll at any width from 360px up.
- Touch targets at least 44px high.
- Album grids reflow by available width (CSS grid with `auto-fill` and a minimum card width).
- Test every new screen at phone width (about 390px) and desktop width (about 1280px). Screenshots go in the story.

## Structure
- `src/features/<area>/`: components, hooks and API calls for one area (library, stats, facts, explore).
- `src/components/`: shared, feature-agnostic UI only.
- `src/api/`: typed client. One function per endpoint.
- Keep page components thin. They compose feature components and hooks.

## Data fetching and states
- Every data view handles four states: loading, empty, error, and success. Never render a blank screen.
- Loading uses a skeleton with the final layout's shape, not a spinner in the middle of the page.
- Errors show a short message and a retry button. The raw error goes to the console only.
- Empty states explain why it's empty and what to do ("No albums found. Run `wj-music scan`.").

## Components and accessibility
- Use semantic HTML: `button` for actions, `a` for navigation, headings in order.
- Every image has `alt` text. Cover art alt is "Cover of <album> by <artist>".
- All interactive elements are keyboard reachable with a visible focus ring.
- Colour is never the only signal. Charts also use labels or patterns.
- Respect `prefers-reduced-motion`.

## Theming
- Colours are CSS custom properties on `:root`, with a dark theme via `prefers-color-scheme` and a manual override.
- Charts use the palette from the dataviz guidance so both themes stay readable.

## Routing
- URL reflects state: album detail, artist page, filters and search are bookmarkable.
