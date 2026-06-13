import {
  useAnalyzeCollectionsSeo,
  useAnalyzeProductsSeo,
  useSeoOptimizerSync,
} from "../../../hooks/useContentSeo";

export type ContentSeoFeedbackVariant = "success" | "warn" | "error";

export interface ContentSeoFeedback {
  message: string;
  variant: ContentSeoFeedbackVariant;
}

interface ContentSeoActionBarProps {
  projectId: string;
  onFeedback: (feedback: ContentSeoFeedback) => void;
}

function errorMessage(err: unknown): string {
  if (err instanceof Error && err.message) return err.message;
  return "Operazione non riuscita.";
}

export function ContentSeoActionBar({ projectId, onFeedback }: ContentSeoActionBarProps) {
  const syncMutation = useSeoOptimizerSync(projectId);
  const analyzeProductsMutation = useAnalyzeProductsSeo(projectId);
  const analyzeCollectionsMutation = useAnalyzeCollectionsSeo(projectId);

  return (
    <div className="content-seo-action-bar">
      <button
        type="button"
        className="gcr-btn gcr-btn--secondary gcr-btn--sm"
        disabled={syncMutation.isPending}
        onClick={() =>
          syncMutation.mutate(undefined, {
            onSuccess: (data) => {
              const base = `Sync: ${data.productsSynced} prodotti, ${data.collectionsSynced} categorie.`;
              if ((data.warnings?.length ?? 0) > 0) {
                onFeedback({
                  message: `${base} ${data.warnings!.join(" ")}${data.message ? ` ${data.message}` : ""}`,
                  variant: "warn",
                });
              } else {
                onFeedback({ message: base, variant: "success" });
              }
            },
            onError: (err) => onFeedback({ message: errorMessage(err), variant: "error" }),
          })
        }
      >
        {syncMutation.isPending ? "Sync…" : "Sincronizza Shopify"}
      </button>
      <button
        type="button"
        className="gcr-btn gcr-btn--secondary gcr-btn--sm"
        disabled={analyzeProductsMutation.isPending}
        onClick={() =>
          analyzeProductsMutation.mutate(undefined, {
            onSuccess: (data) =>
              onFeedback({
                message: `Prodotti analizzati: ${data.productsAnalyzed ?? 0}.`,
                variant: "success",
              }),
            onError: (err) => onFeedback({ message: errorMessage(err), variant: "error" }),
          })
        }
      >
        {analyzeProductsMutation.isPending ? "Analisi…" : "Analizza prodotti"}
      </button>
      <button
        type="button"
        className="gcr-btn gcr-btn--primary gcr-btn--sm"
        disabled={analyzeCollectionsMutation.isPending}
        onClick={() =>
          analyzeCollectionsMutation.mutate(undefined, {
            onSuccess: (data) =>
              onFeedback({
                message:
                  data.message ??
                  `Categorie analizzate: ${data.collectionsAnalyzed ?? 0}.`,
                variant: "success",
              }),
            onError: (err) => onFeedback({ message: errorMessage(err), variant: "error" }),
          })
        }
      >
        {analyzeCollectionsMutation.isPending ? "Analisi…" : "Analizza categorie"}
      </button>
    </div>
  );
}
