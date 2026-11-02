interface SearchBoxProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

export function SearchBox({ label, value, onChange }: SearchBoxProps) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      <input
        type="search"
        value={value}
        placeholder="Search…"
        onChange={(event) => {
          onChange(event.target.value);
        }}
      />
    </label>
  );
}
