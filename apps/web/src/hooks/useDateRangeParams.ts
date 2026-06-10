import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import type { DateRangeParams, DateRangePreset } from "@gcr/shared";
import { mergeDateRangeSearchParams, parseDateRangeFromSearchParams } from "../lib/date-range";

export function useDateRangeParams() {
  const [searchParams, setSearchParams] = useSearchParams();

  const dateRange = useMemo(
    () => parseDateRangeFromSearchParams(searchParams),
    [searchParams],
  );

  const setDateRange = useCallback(
    (nextRange: DateRangeParams) => {
      setSearchParams(mergeDateRangeSearchParams(searchParams, nextRange), { replace: true });
    },
    [searchParams, setSearchParams],
  );

  const setPreset = useCallback(
    (preset: DateRangePreset) => {
      if (preset === "custom") {
        setDateRange({ range: "custom", startDate: dateRange.startDate, endDate: dateRange.endDate });
        return;
      }
      setDateRange({ range: preset });
    },
    [dateRange.endDate, dateRange.startDate, setDateRange],
  );

  const setCustomRange = useCallback(
    (startDate: string, endDate: string) => {
      setDateRange({ range: "custom", startDate, endDate });
    },
    [setDateRange],
  );

  return {
    dateRange,
    setDateRange,
    setPreset,
    setCustomRange,
  };
}
