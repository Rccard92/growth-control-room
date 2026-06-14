import type { ContentSeoEditorialItem } from "@gcr/shared";
import { EditorialItemCard } from "./EditorialItemCard";

interface EditorialCalendarDayProps {
  day: number;
  dateKey: string;
  isToday: boolean;
  isOutsideMonth: boolean;
  items: ContentSeoEditorialItem[];
  onItemClick: (item: ContentSeoEditorialItem) => void;
}

export function EditorialCalendarDay({
  day,
  isToday,
  isOutsideMonth,
  items,
  onItemClick,
}: EditorialCalendarDayProps) {
  return (
    <div
      className={[
        "editorial-calendar__day",
        isToday ? "editorial-calendar__day--today" : "",
        isOutsideMonth ? "editorial-calendar__day--outside" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <span className="editorial-calendar__day-num">{day}</span>
      <div className="editorial-calendar__day-items">
        {items.map((item) => (
          <EditorialItemCard key={item.id} item={item} onClick={() => onItemClick(item)} />
        ))}
      </div>
    </div>
  );
}
