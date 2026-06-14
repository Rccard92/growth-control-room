import { useCallback, useId, useLayoutEffect, useRef } from "react";

export interface AutoResizeTextareaProps {
  id?: string;
  label?: string;
  value: string;
  onChange: (value: string) => void;
  minRows?: number;
  maxRows?: number;
  placeholder?: string;
  disabled?: boolean;
  helpText?: string;
  error?: string;
  className?: string;
}

function lineHeightPx(el: HTMLTextAreaElement): number {
  const style = window.getComputedStyle(el);
  const lh = parseFloat(style.lineHeight);
  if (!Number.isNaN(lh)) return lh;
  const fontSize = parseFloat(style.fontSize) || 14;
  return fontSize * 1.35;
}

export function AutoResizeTextarea({
  id: idProp,
  label,
  value,
  onChange,
  minRows = 2,
  maxRows,
  placeholder,
  disabled = false,
  helpText,
  error,
  className,
}: AutoResizeTextareaProps) {
  const autoId = useId();
  const id = idProp ?? autoId;
  const ref = useRef<HTMLTextAreaElement>(null);

  const resize = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    const lh = lineHeightPx(el);
    const padding =
      parseFloat(window.getComputedStyle(el).paddingTop) +
      parseFloat(window.getComputedStyle(el).paddingBottom);
    const minHeight = lh * minRows + padding;
    el.style.height = "auto";
    let next = Math.max(el.scrollHeight, minHeight);
    if (maxRows) {
      const maxHeight = lh * maxRows + padding;
      if (next > maxHeight) {
        next = maxHeight;
        el.style.overflowY = "auto";
      } else {
        el.style.overflowY = "hidden";
      }
    } else {
      el.style.overflowY = "hidden";
    }
    el.style.height = `${next}px`;
  }, [minRows, maxRows]);

  useLayoutEffect(() => {
    resize();
  }, [value, resize]);

  return (
    <div className="auto-resize-textarea-field">
      {label && (
        <label htmlFor={id} className="auto-resize-textarea-field__label">
          {label}
        </label>
      )}
      <textarea
        ref={ref}
        id={id}
        className={[
          "gcr-input",
          "auto-resize-textarea",
          error ? "auto-resize-textarea--error" : "",
          className ?? "",
        ]
          .filter(Boolean)
          .join(" ")}
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        rows={minRows}
        onChange={(e) => onChange(e.target.value)}
        onInput={resize}
      />
      {error && <span className="auto-resize-textarea-field__error">{error}</span>}
      {!error && helpText && (
        <span className="auto-resize-textarea-field__help">{helpText}</span>
      )}
    </div>
  );
}
