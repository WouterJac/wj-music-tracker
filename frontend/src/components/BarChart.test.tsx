import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { BarChart } from "./BarChart";

function renderChart(items: { label: string; count: number; href?: string }[]) {
  return render(
    <MemoryRouter>
      <BarChart title="Albums by decade" unit="album" items={items} />
    </MemoryRouter>,
  );
}

describe("BarChart", () => {
  it("is a named figure whose rows are readable as plain text", () => {
    renderChart([
      { label: "1970s", count: 4 },
      { label: "1980s", count: 1 },
    ]);

    const figure = screen.getByRole("figure", { name: "Albums by decade" });
    const rows = within(figure).getAllByRole("listitem");
    expect(rows).toHaveLength(2);
    expect(within(rows[0]).getByText("1970s")).toBeInTheDocument();
    expect(within(rows[0]).getByText("4 albums")).toBeInTheDocument();
    expect(within(rows[1]).getByText("1 album")).toBeInTheDocument();
  });

  it("sizes each bar relative to the largest value", () => {
    renderChart([
      { label: "A", count: 4 },
      { label: "B", count: 1 },
    ]);

    const bars = document.querySelectorAll<HTMLElement>(".bar-fill");
    expect(bars[0].style.width).toBe("100%");
    expect(bars[1].style.width).toBe("25%");
  });

  it("gives the unit to assistive tech without repeating it on screen", () => {
    renderChart([{ label: "1970s", count: 1 }]);

    expect(screen.getByText("1 album")).toHaveClass("visually-hidden");
  });

  it("links a row when it has a destination", () => {
    renderChart([{ label: "Brian Eno", count: 3, href: "/artists/2" }]);

    expect(screen.getByRole("link", { name: /Brian Eno/ })).toHaveAttribute("href", "/artists/2");
  });

  it("renders nothing visible but the title when there is no data", () => {
    renderChart([]);

    expect(screen.getByText("No data yet.")).toBeInTheDocument();
  });
});
