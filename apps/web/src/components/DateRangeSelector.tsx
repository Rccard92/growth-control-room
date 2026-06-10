import { useEffect, useRef, useState } from "react";
import { DATE_RANGE_OPTIONS, type DateRangeParams, type DateRangePreset } from "@gcr/shared";

interface DateRangeSelectorProps {
  value: DateRangeParams;
  onChange: (value: DateRangeParams) => void;
  disabled?: boolean;
}

export function DateRangeSelector({ value, onChange, disabled = false }: DateRangeSelectorProps) {
  const [open, setOpen] = useState(false);
  const [customStart, setCustomStart] = useState(value.startDate ?? "");
  const [customEnd, setCustomEnd] = useState(value.endDate ?? "");
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setCustomStart(value.startDate ?? "");
    setCustomEnd(value.endDate ?? "");
  }, [value.endDate, value.startDate, value.range]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selectedLabel =
    DATE_RANGE_OPTIONS.find((option) => option.value === value.range)?.label ?? "Periodo";

  function handlePresetSelect(preset: DateRangePreset) {
    if (preset === "custom") {
      onChange({ range: "custom", startDate: customStart || undefined, endDate: customEnd || undefined });
      return;
    }
    onChange({ range: preset });
    setOpen(false);
  }

  function handleApplyCustom() {
    if (!customStart || !customEnd) return;
    onChange({ range: "custom", startDate: customStart, endDate: customEnd });
    setOpen(false);
  }

  return (
    <div className="date-range-selector" ref={containerRef}>
      <button
        type="button"
        className="gcr-btn gcr-btn--secondary date-range-selector__trigger"
        onClick={() => setOpen((current) => !current)}
        disabled={disabled}
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        {selectedLabel}
      </button>

      {open && (
        <div className="date-range-selector__panel">
          <ul className="date-range-selector__options" role="listbox">
            {DATE_RANGE_OPTIONS.map((option) => (
              <li key={option.value}>
                <button
                  type="button"
                  className={`date-range-selector__option ${
                    value.range === option.value ? "date-range-selector__option--active" : ""
                  }`}
                  onClick={() => handlePresetSelect(option.value)}
                >
                  {option.label}
                </button>
              </li>
            ))}
          </ul>

          {value.range === "custom" && (
            <div className="date-range-selector__custom">
              <label className="date-range-selector__field">
                <span>Data inizio</span>
                <input
                  type="date"
                  value={customStart}
                  onChange={(event) => setCustomStart(event.target.value)}
                />
              </label>
              <label className="date-range-selector__field">
                <span>Data fine</span>
                <input
                  type="date"
                  value={customEnd}
                  onChange={(event) => setCustomEnd(event.target.value)}
                />
              </label>
              <button
                type="button"
                className="gcr-btn gcr-btn--primary date-range-selector__apply"
                onClick={handleApplyCustom}
                disabled={!customStart || !customEnd}
              >
                Applica
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
