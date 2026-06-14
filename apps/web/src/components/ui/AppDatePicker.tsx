import { useCallback, useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";

const WEEKDAY_LABELS = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"];
const MONTH_LABELS = [
  "Gennaio",
  "Febbraio",
  "Marzo",
  "Aprile",
  "Maggio",
  "Giugno",
  "Luglio",
  "Agosto",
  "Settembre",
  "Ottobre",
  "Novembre",
  "Dicembre",
];

export interface AppDatePickerProps {
  id?: string;
  label?: string;
  value: string;
  onChange: (value: string) => void;
  min?: string;
  max?: string;
  disabled?: boolean;
  placeholder?: string;
}

function parseDate(value: string): Date | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const [y, m, d] = value.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function formatDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function formatDisplay(value: string): string {
  const parsed = parseDate(value);
  if (!parsed) return value;
  return parsed.toLocaleDateString("it-IT", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function isBefore(date: Date, min: Date): boolean {
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const m = new Date(min.getFullYear(), min.getMonth(), min.getDate());
  return d < m;
}

function isAfter(date: Date, max: Date): boolean {
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const m = new Date(max.getFullYear(), max.getMonth(), max.getDate());
  return d > m;
}

export function AppDatePicker({
  id: idProp,
  label,
  value,
  onChange,
  min,
  max,
  disabled = false,
  placeholder = "Seleziona data…",
}: AppDatePickerProps) {
  const autoId = useId();
  const id = idProp ?? autoId;
  const [open, setOpen] = useState(false);
  const [viewMonth, setViewMonth] = useState(() => {
    const parsed = parseDate(value);
    return parsed ?? new Date();
  });
  const [menuStyle, setMenuStyle] = useState<{ top: number; left: number; width: number }>({
    top: 0,
    left: 0,
    width: 0,
  });
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const minDate = min ? parseDate(min) : null;
  const maxDate = max ? parseDate(max) : null;
  const selectedDate = parseDate(value);
  const today = useMemo(() => new Date(), []);

  const updatePosition = useCallback(() => {
    const el = triggerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    setMenuStyle({
      top: rect.bottom + 4,
      left: rect.left,
      width: Math.max(rect.width, 280),
    });
  }, []);

  useLayoutEffect(() => {
    if (!open) return;
    updatePosition();
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);
    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [open, updatePosition]);

  useEffect(() => {
    if (!open) return;
    function handleClickOutside(e: MouseEvent) {
      const target = e.target as Node;
      if (triggerRef.current?.contains(target) || menuRef.current?.contains(target)) {
        return;
      }
      setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  useEffect(() => {
    if (selectedDate) {
      setViewMonth(new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1));
    }
  }, [value]);

  const calendarDays = useMemo(() => {
    const year = viewMonth.getFullYear();
    const month = viewMonth.getMonth();
    const firstDay = new Date(year, month, 1);
    const startOffset = (firstDay.getDay() + 6) % 7;
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const cells: Array<{ date: Date; inMonth: boolean }> = [];

    for (let i = 0; i < startOffset; i++) {
      const d = new Date(year, month, -startOffset + i + 1);
      cells.push({ date: d, inMonth: false });
    }
    for (let day = 1; day <= daysInMonth; day++) {
      cells.push({ date: new Date(year, month, day), inMonth: true });
    }
    while (cells.length % 7 !== 0) {
      const last = cells[cells.length - 1].date;
      const next = new Date(last);
      next.setDate(last.getDate() + 1);
      cells.push({ date: next, inMonth: false });
    }
    return cells;
  }, [viewMonth]);

  function isDisabledDay(date: Date): boolean {
    if (minDate && isBefore(date, minDate)) return true;
    if (maxDate && isAfter(date, maxDate)) return true;
    return false;
  }

  function selectDate(date: Date) {
    if (isDisabledDay(date)) return;
    onChange(formatDate(date));
    setOpen(false);
  }

  function prevMonth() {
    setViewMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  }

  function nextMonth() {
    setViewMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
  }

  const menu =
    open && !disabled
      ? createPortal(
          <div
            ref={menuRef}
            className="app-date-picker-menu"
            role="dialog"
            aria-label="Calendario"
            style={{
              top: menuStyle.top,
              left: menuStyle.left,
              width: menuStyle.width,
            }}
          >
            <div className="app-date-picker-menu__header">
              <button
                type="button"
                className="app-date-picker-menu__nav"
                aria-label="Mese precedente"
                onClick={prevMonth}
              >
                ‹
              </button>
              <span className="app-date-picker-menu__title">
                {MONTH_LABELS[viewMonth.getMonth()]} {viewMonth.getFullYear()}
              </span>
              <button
                type="button"
                className="app-date-picker-menu__nav"
                aria-label="Mese successivo"
                onClick={nextMonth}
              >
                ›
              </button>
            </div>
            <div className="app-date-picker-menu__weekdays">
              {WEEKDAY_LABELS.map((day) => (
                <span key={day} className="app-date-picker-menu__weekday">
                  {day}
                </span>
              ))}
            </div>
            <div className="app-date-picker-menu__grid">
              {calendarDays.map(({ date, inMonth }) => {
                const selected = selectedDate ? isSameDay(date, selectedDate) : false;
                const isToday = isSameDay(date, today);
                const dayDisabled = isDisabledDay(date);
                return (
                  <button
                    key={formatDate(date)}
                    type="button"
                    className={[
                      "app-date-picker-day",
                      !inMonth ? "app-date-picker-day--outside" : "",
                      selected ? "app-date-picker-day--selected" : "",
                      isToday ? "app-date-picker-day--today" : "",
                      dayDisabled ? "app-date-picker-day--disabled" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    disabled={dayDisabled || !inMonth}
                    onClick={() => selectDate(date)}
                  >
                    {date.getDate()}
                  </button>
                );
              })}
            </div>
          </div>,
          document.body,
        )
      : null;

  return (
    <div className="app-date-picker-field">
      {label && (
        <label htmlFor={id} className="app-date-picker-field__label">
          {label}
        </label>
      )}
      <button
        ref={triggerRef}
        id={id}
        type="button"
        className={[
          "app-date-picker",
          open ? "app-date-picker--open" : "",
          disabled ? "app-date-picker--disabled" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        disabled={disabled}
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => !disabled && setOpen((v) => !v)}
      >
        <span
          className={[
            "app-date-picker__value",
            !value ? "app-date-picker__value--placeholder" : "",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          {value ? formatDisplay(value) : placeholder}
        </span>
        <span className="app-date-picker__icon" aria-hidden>
          📅
        </span>
      </button>
      {menu}
    </div>
  );
}
