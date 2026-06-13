import { useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { ContentSeoFeedback, ContentSeoFeedbackVariant } from "./ContentSeoActionBar";

const AUTO_DISMISS_MS = 5500;

interface ContentSeoToastProps {
  feedback: ContentSeoFeedback | null;
  onDismiss: () => void;
}

function variantClass(variant: ContentSeoFeedbackVariant): string {
  if (variant === "error") return "content-seo-toast--error";
  if (variant === "warn") return "content-seo-toast--warn";
  return "content-seo-toast--success";
}

export function ContentSeoToast({ feedback, onDismiss }: ContentSeoToastProps) {
  useEffect(() => {
    if (!feedback || feedback.variant === "error") return;
    const timer = window.setTimeout(onDismiss, AUTO_DISMISS_MS);
    return () => window.clearTimeout(timer);
  }, [feedback, onDismiss]);

  return (
    <AnimatePresence>
      {feedback && (
        <motion.div
          key={feedback.message}
          className={`content-seo-toast ${variantClass(feedback.variant)}`}
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.2 }}
          role="status"
        >
          <span className="content-seo-toast__message">{feedback.message}</span>
          <button
            type="button"
            className="content-seo-toast__close"
            aria-label="Chiudi"
            onClick={onDismiss}
          >
            ×
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
