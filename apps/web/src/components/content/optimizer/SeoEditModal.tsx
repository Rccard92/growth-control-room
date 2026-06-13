import { useEffect, type ReactNode } from "react";
import { createPortal } from "react-dom";

interface SeoEditModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  headerExtra?: ReactNode;
  footer?: ReactNode;
  children: ReactNode;
}

export function SeoEditModal({
  open,
  onClose,
  title,
  headerExtra,
  footer,
  children,
}: SeoEditModalProps) {
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
    <div className="seo-edit-modal" role="presentation">
      <div
        className="seo-edit-modal__overlay"
        aria-hidden="true"
        onClick={onClose}
      />
      <div
        className="seo-edit-modal__panel"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="seo-edit-modal__header">
          <div className="seo-edit-modal__header-main">
            <p className="seo-edit-modal__label">Modifica SEO</p>
            <h3 className="seo-edit-modal__title">{title}</h3>
            {headerExtra}
          </div>
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary"
            onClick={onClose}
            aria-label="Chiudi"
          >
            Chiudi
          </button>
        </header>

        <div className="seo-edit-modal__body">{children}</div>

        {footer && <footer className="seo-edit-modal__footer">{footer}</footer>}
      </div>
    </div>,
    document.body,
  );
}
