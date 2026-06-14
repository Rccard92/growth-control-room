import { useId } from "react";

export interface AppCheckboxProps {
  id?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  description?: string;
  disabled?: boolean;
  variant?: "inline" | "card";
}

export function AppCheckbox({
  id: idProp,
  checked,
  onChange,
  label,
  description,
  disabled = false,
  variant = "inline",
}: AppCheckboxProps) {
  const autoId = useId();
  const id = idProp ?? autoId;

  return (
    <label
      htmlFor={id}
      className={[
        "app-checkbox",
        variant === "card" ? "app-checkbox--card" : "",
        checked ? "app-checkbox--checked" : "",
        disabled ? "app-checkbox--disabled" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <input
        id={id}
        type="checkbox"
        className="app-checkbox__input"
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
      />
      <span className="app-checkbox__box" aria-hidden>
        {checked && (
          <svg className="app-checkbox__check" viewBox="0 0 12 10" fill="none">
            <path
              d="M1 5.5L4.5 9L11 1"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
      </span>
      <span className="app-checkbox__content">
        <span className="app-checkbox__label">{label}</span>
        {description && <span className="app-checkbox__description">{description}</span>}
      </span>
    </label>
  );
}
