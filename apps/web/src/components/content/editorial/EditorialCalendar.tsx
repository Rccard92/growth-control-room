import { useMemo } from "react";
import type { ContentSeoEditorialItem } from "@gcr/shared";
import { EditorialCalendarDay } from "./EditorialCalendarDay";

const WEEKDAY_LABELS = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"];

const MONTH_NAMES = [
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

function padMonth(year: number, month: number): string {
  return `${year}-${String(month + 1).padStart(2, "0")}`;
}

function parseMonth(month: string): { year: number; month: number } {
  const [y, m] = month.split("-").map(Number);
  return { year: y, month: m - 1 };
}

interface EditorialCalendarProps {
  month: string;
  items: ContentSeoEditorialItem[];
  onMonthChange: (month: string) => void;
  onItemClick: (item: ContentSeoEditorialItem) => void;
}

export function EditorialCalendar({
  month,
  items,
  onMonthChange,
  onItemClick,
}: EditorialCalendarProps) {
  const { year, month: monthIndex } = parseMonth(month);
  const today = new Date();
  const todayKey = today.toISOString().slice(0, 10);

  const itemsByDate = useMemo(() => {
    const map = new Map<string, ContentSeoEditorialItem[]>();
    for (const item of items) {
      const key = item.plannedDate.slice(0, 10);
      const list = map.get(key) ?? [];
      list.push(item);
      map.set(key, list);
    }
    return map;
  }, [items]);

  const cells = useMemo(() => {
    const first = new Date(year, monthIndex, 1);
    const startOffset = (first.getDay() + 6) % 7;
    const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
    const prevMonthDays = new Date(year, monthIndex, 0).getDate();
    const totalCells = Math.ceil((startOffset + daysInMonth) / 7) * 7;
    const result: {
      day: number;
      dateKey: string;
      isToday: boolean;
      isOutsideMonth: boolean;
    }[] = [];

    for (let i = 0; i < totalCells; i++) {
      let day: number;
      let cellYear = year;
      let cellMonth = monthIndex;
      let isOutsideMonth = false;

      if (i < startOffset) {
        day = prevMonthDays - startOffset + i + 1;
        cellMonth = monthIndex - 1;
        if (cellMonth < 0) {
          cellMonth = 11;
          cellYear -= 1;
        }
        isOutsideMonth = true;
      } else if (i >= startOffset + daysInMonth) {
        day = i - startOffset - daysInMonth + 1;
        cellMonth = monthIndex + 1;
        if (cellMonth > 11) {
          cellMonth = 0;
          cellYear += 1;
        }
        isOutsideMonth = true;
      } else {
        day = i - startOffset + 1;
      }

      const dateKey = `${cellYear}-${String(cellMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
      result.push({
        day,
        dateKey,
        isToday: dateKey === todayKey,
        isOutsideMonth,
      });
    }
    return result;
  }, [year, monthIndex, todayKey]);

  function shiftMonth(delta: number) {
    const d = new Date(year, monthIndex + delta, 1);
    onMonthChange(padMonth(d.getFullYear(), d.getMonth()));
  }

  return (
    <div className="editorial-calendar gcr-card">
      <div className="editorial-calendar__header">
        <button type="button" className="gcr-btn gcr-btn--ghost" onClick={() => shiftMonth(-1)}>
          ◀
        </button>
        <h3 className="editorial-calendar__title">
          {MONTH_NAMES[monthIndex]} {year}
        </h3>
        <button type="button" className="gcr-btn gcr-btn--ghost" onClick={() => shiftMonth(1)}>
          ▶
        </button>
      </div>
      <div className="editorial-calendar__weekdays">
        {WEEKDAY_LABELS.map((label) => (
          <span key={label} className="editorial-calendar__weekday">
            {label}
          </span>
        ))}
      </div>
      <div className="editorial-calendar__grid">
        {cells.map((cell) => (
          <EditorialCalendarDay
            key={cell.dateKey}
            day={cell.day}
            dateKey={cell.dateKey}
            isToday={cell.isToday}
            isOutsideMonth={cell.isOutsideMonth}
            items={itemsByDate.get(cell.dateKey) ?? []}
            onItemClick={onItemClick}
          />
        ))}
      </div>
    </div>
  );
}
