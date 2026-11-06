import { useEffect, useState } from "react";
import { apiFetch } from "../api";

export default function InstitutionPicker({ onChange }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [selected, setSelected] = useState(null);
  const [program, setProgram] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (query.trim().length < 2 || selected) {
      return;
    }

    const controller = new AbortController();

    const timer = setTimeout(async () => {
      try {
        const response = await apiFetch(
          `/institutions?q=${encodeURIComponent(query)}`,
          { signal: controller.signal },
        );
        const data = await response.json();

        if (!controller.signal.aborted) {
          setResults(data);
          setError("");
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err.message);
        }
      }
    }, 300);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, selected]);

  async function choose(id) {
    try {
      const response = await apiFetch(`/institutions/${id}`);
      const data = await response.json();

      setSelected(data);
      setQuery(data.name);
      setProgram("");
      setResults([]);
      onChange({ scorecard_id: data.id, program: "" });
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <fieldset>
      <legend>Institution and major</legend>

      <label>
        US institution
        <input
          value={query}
          required
          onChange={(event) => {
            setQuery(event.target.value);
            setSelected(null);
            setResults([]);
            setProgram("");
            onChange(null);
          }}
        />
      </label>

      {error && <p role="alert">{error}</p>}

      {results.map((school) => (
        <button key={school.id} type="button" onClick={() => choose(school.id)}>
          {school.name} — {school.city}, {school.state}
        </button>
      ))}

      {selected && (
        <label>
          Major / program
          <input
            list="institution-programs"
            value={program}
            placeholder="Undeclared / not listed"
            onChange={(event) => {
              const value = event.target.value;
              const option = selected.programs.find(
                (item) => item.label === value,
              );

              event.target.setCustomValidity(
                value && !option
                  ? "Select a program from the options or leave this blank."
                  : "",
              );

              setProgram(value);
              onChange({
                scorecard_id: selected.id,
                program: option?.value ?? "",
              });
            }}
          />
          <datalist id="institution-programs">
            {selected.programs.map((item) => (
              <option key={item.value} value={item.label} />
            ))}
          </datalist>
        </label>
      )}
    </fieldset>
  );
}
