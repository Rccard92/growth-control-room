import { useEffect, useId, type ReactNode } from "react";
import { createPortal } from "react-dom";

export interface AppModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  maxWidth?: "sm" | "md" | "lg";
  closeOnOverlayClick?: boolean;
  header?: ReactNode;
  footer?: ReactNode;
  children: ReactNode;
}

export function AppModal({
  open,
  onClose,
  title,
  subtitle,
  maxWidth = "md",
  closeOnOverlayClick = true,
  header,
  footer,
  children,
}: AppModalProps) {
  const titleId = useId();

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div
      className="app-modal-overlay"
      role="presentation"
      onClick={closeOnOverlayClick ? onClose : undefined}
    >
      <div
        className={`app-modal app-modal--${maxWidth}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(e) => e.stopPropagation()}
      >
        {header ?? (
          <header className="app-modal__header">
            <div className="app-modal__header-main">
              <h2 id={titleId} className="app-modal__title">
                {title}
              </h2>
              {subtitle && <p className="app-modal__subtitle">{subtitle}</p>}
            </div>
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary gcr-btn--sm"
              onClick={onClose}
              aria-label="Chiudi"
            >
              Chiudi
            </button>
          </header>
        )}

        <div className="app-modal__body">{children}</div>

        {footer && <footer className="app-modal__footer">{footer}</footer>}
      </div>
    </div>,
    document.body,
  );
}
