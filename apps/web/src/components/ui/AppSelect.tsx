import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

export interface AppSelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface AppSelectProps {
  id?: string;
  label?: string;
  value: string;
  options: AppSelectOption[];
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
  helpText?: string;
}

export function AppSelect({
  id: idProp,
  label,
  value,
  options,
  onChange,
  placeholder = "Seleziona…",
  disabled = false,
  error,
  helpText,
}: AppSelectProps) {
  const autoId = useId();
  const id = idProp ?? autoId;
  const [open, setOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const [menuStyle, setMenuStyle] = useState<{ top: number; left: number; width: number }>({
    top: 0,
    left: 0,
    width: 0,
  });
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLUListElement>(null);

  const selected = options.find((o) => o.value === value);
  const enabledOptions = options.filter((o) => !o.disabled);

  const updatePosition = useCallback(() => {
    const el = triggerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    setMenuStyle({
      top: rect.bottom + 4,
      left: rect.left,
      width: rect.width,
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
      if (
        triggerRef.current?.contains(target) ||
        menuRef.current?.contains(target)
      ) {
        return;
      }
      setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  useEffect(() => {
    if (!open) {
      setFocusedIndex(-1);
    }
  }, [open]);

  function selectOption(option: AppSelectOption) {
    if (option.disabled) return;
    onChange(option.value);
    setOpen(false);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (disabled) return;
    if (!open) {
      if (e.key === "Enter" || e.key === " " || e.key === "ArrowDown") {
        e.preventDefault();
        setOpen(true);
        const idx = enabledOptions.findIndex((o) => o.value === value);
        setFocusedIndex(idx >= 0 ? idx : 0);
      }
      return;
    }

    if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
      return;
    }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setFocusedIndex((prev) => {
        const next = prev < enabledOptions.length - 1 ? prev + 1 : 0;
        return next;
      });
      return;
    }

    if (e.key === "ArrowUp") {
      e.preventDefault();
      setFocusedIndex((prev) => {
        const next = prev > 0 ? prev - 1 : enabledOptions.length - 1;
        return next;
      });
      return;
    }

    if (e.key === "Enter" && focusedIndex >= 0 && focusedIndex < enabledOptions.length) {
      e.preventDefault();
      selectOption(enabledOptions[focusedIndex]);
    }
  }

  const menu =
    open && !disabled
      ? createPortal(
          <ul
            ref={menuRef}
            className="app-select-menu"
            role="listbox"
            id={`${id}-listbox`}
            style={{
              top: menuStyle.top,
              left: menuStyle.left,
              width: menuStyle.width,
            }}
          >
            {options.map((option) => {
              const enabledIdx = enabledOptions.indexOf(option);
              const isFocused = enabledIdx === focusedIndex;
              const isSelected = option.value === value;
              return (
                <li
                  key={option.value}
                  role="option"
                  aria-selected={isSelected}
                  className={[
                    "app-select-option",
                    isSelected ? "app-select-option--selected" : "",
                    isFocused ? "app-select-option--focused" : "",
                    option.disabled ? "app-select-option--disabled" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onMouseEnter={() => {
                    if (!option.disabled && enabledIdx >= 0) setFocusedIndex(enabledIdx);
                  }}
                  onClick={() => selectOption(option)}
                >
                  {option.label}
                </li>
              );
            })}
          </ul>,
          document.body,
        )
      : null;

  return (
    <div className="app-select-field">
      {label && (
        <label htmlFor={id} className="app-select-field__label">
          {label}
        </label>
      )}
      <button
        ref={triggerRef}
        id={id}
        type="button"
        className={[
          "app-select",
          open ? "app-select--open" : "",
          disabled ? "app-select--disabled" : "",
          error ? "app-select--error" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? `${id}-listbox` : undefined}
        onClick={() => !disabled && setOpen((v) => !v)}
        onKeyDown={handleKeyDown}
      >
        <span
          className={[
            "app-select__value",
            !selected ? "app-select__value--placeholder" : "",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          {selected?.label ?? placeholder}
        </span>
        <span className="app-select__chevron" aria-hidden>
          ▼
        </span>
      </button>
      {error && <span className="app-select-field__error">{error}</span>}
      {!error && helpText && (
        <span className="app-select-field__help">{helpText}</span>
      )}
      {menu}
    </div>
  );
}
