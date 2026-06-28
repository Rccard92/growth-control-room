import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  ContentSeoEditorialItem,
  ContentSeoEditorialObjective,
  ContentSeoEditorialStatus,
  EditorialArticlePayload,
  EditorialBriefPayload,
  EditorialImagePayload,
  EditorialPublishingPayload,
  EditorialPublishMode,
} from "@gcr/shared";
import {
  CONTENT_SEO_EDITORIAL_CONTENT_TYPE_LABELS,
  CONTENT_SEO_EDITORIAL_OBJECTIVE_LABELS,
  CONTENT_SEO_EDITORIAL_STATUS_LABELS,
} from "@gcr/shared";
import { EditorialAiGenerationAccordion } from "./EditorialAiGenerationAccordion";
import { EditorialBriefEditor } from "./EditorialBriefEditor";
import { EditorialArticleEditor } from "./EditorialArticleEditor";
import { EditorialArticlePreview } from "./EditorialArticlePreview";
import { EditorialPublishingTab } from "./EditorialPublishingTab";
import { EditorialImageTab } from "./EditorialImageTab";
import {
  hasEditorialBrief,
  parseEditorialBriefPayload,
} from "./editorial-brief-utils";
import {
  hasEditorialArticle,
  parseEditorialArticlePayload,
} from "./editorial-article-utils";
import {
  applyPedScheduleDefaults,
  buildPublishingPayloadFromArticle,
  classifyPlannedDate,
  formatPublishingError,
  getPrimaryPublishAction,
  isPublishingStale,
  isPublishingSeoComplete,
  parseEditorialPublishingPayload,
  resolveEditorialTimezone,
  validatePublishingPayload,
  validatePublishingPayloadWithWarnings,
} from "./editorial-publishing-utils";
import {
  emptyEditorialImagePayload,
  parseEditorialImagePayload,
} from "./editorial-image-utils";
import { getShopifyScopes } from "../../../lib/shopify-api";
import { useShopifyStatus } from "../../../hooks/useShopify";
import { useBrandProfile } from "../../../hooks/useBrandIntelligence";
import { queryKeys } from "../../../lib/queryKeys";
import { AppModal } from "../../ui/AppModal";
import { AppSelect } from "../../ui/AppSelect";
import { AppDatePicker } from "../../ui/AppDatePicker";
import { AppCheckbox } from "../../ui/AppCheckbox";
import { AutoResizeTextarea } from "../../ui/AutoResizeTextarea";
import { EditorialStatusBadge } from "./EditorialStatusLegend";
import {
  useDeleteEditorialItem,
  useGenerateEditorialArticle,
  useGenerateEditorialBrief,
  useGenerateEditorialImage,
  useEditEditorialImage,
  useApproveEditorialImage,
  useRemoveEditorialImage,
  useSyncEditorialImageFromTitle,
  usePublishEditorialShopify,
  useSyncEditorialPublishingFromArticle,
  useDisconnectEditorialShopifyArticle,
  useRescheduleEditorialItem,
  useShopifyBlogs,
  useUpdateEditorialArticle,
  useUpdateEditorialBrief,
  useUpdateEditorialItem,
  useUpdateEditorialPublishing,
} from "../../../hooks/useContentSeoEditorial";

interface EditorialItemModalProps {
  open: boolean;
  item: ContentSeoEditorialItem | null;
  projectId: string;
  allItems: ContentSeoEditorialItem[];
  onClose: () => void;
  onItemUpdated?: (item: ContentSeoEditorialItem) => void;
}

function formatPlannedDate(value: string): string {
  const parsed = new Date(value.slice(0, 10) + "T12:00:00");
  if (Number.isNaN(parsed.getTime())) return value.slice(0, 10);
  return parsed.toLocaleDateString("it-IT", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

export function EditorialItemModal({
  open,
  item,
  projectId,
  allItems,
  onClose,
  onItemUpdated,
}: EditorialItemModalProps) {
  const queryClient = useQueryClient();
  const updateMutation = useUpdateEditorialItem(projectId);
  const rescheduleMutation = useRescheduleEditorialItem(projectId);
  const deleteMutation = useDeleteEditorialItem(projectId);
  const generateBriefMutation = useGenerateEditorialBrief(projectId);
  const updateBriefMutation = useUpdateEditorialBrief(projectId);
  const generateArticleMutation = useGenerateEditorialArticle(projectId);
  const generateImageMutation = useGenerateEditorialImage(projectId);
  const editImageMutation = useEditEditorialImage(projectId);
  const approveImageMutation = useApproveEditorialImage(projectId);
  const removeImageMutation = useRemoveEditorialImage(projectId);
  const syncImageFromTitleMutation = useSyncEditorialImageFromTitle(projectId);
  const updateArticleMutation = useUpdateEditorialArticle(projectId);
  const updatePublishingMutation = useUpdateEditorialPublishing(projectId);
  const publishShopifyMutation = usePublishEditorialShopify(projectId);
  const syncPublishingMutation = useSyncEditorialPublishingFromArticle(projectId);
  const disconnectShopifyMutation = useDisconnectEditorialShopifyArticle(projectId);
  const { data: blogsData, isLoading: blogsLoading } = useShopifyBlogs(projectId, open);
  const { data: scopesData, isLoading: scopesLoading } = useQuery({
    queryKey: queryKeys.shopify.scopes(projectId),
    queryFn: () => getShopifyScopes(projectId),
    enabled: open,
    retry: false,
  });
  const { data: shopifyStatus } = useShopifyStatus(open ? projectId : undefined);
  const { data: brandProfile } = useBrandProfile(open ? projectId : undefined);

  const [title, setTitle] = useState("");
  const [plannedDate, setPlannedDate] = useState("");
  const [originalPlannedDate, setOriginalPlannedDate] = useState("");
  const [cascadeReschedule, setCascadeReschedule] = useState(false);
  const [status, setStatus] = useState<ContentSeoEditorialStatus>("idea");
  const [objective, setObjective] = useState<ContentSeoEditorialObjective | "">("");
  const [primaryKeyword, setPrimaryKeyword] = useState("");
  const [secondaryKeywords, setSecondaryKeywords] = useState("");
  const [notes, setNotes] = useState("");
  const [brief, setBrief] = useState<EditorialBriefPayload | null>(null);
  const [savedBriefSnapshot, setSavedBriefSnapshot] = useState("");
  const [article, setArticle] = useState<EditorialArticlePayload | null>(null);
  const [savedArticleSnapshot, setSavedArticleSnapshot] = useState("");
  const [articleView, setArticleView] = useState<"editor" | "preview">("editor");
  const [articleBodyMode, setArticleBodyMode] = useState<"html" | "markdown">("html");
  const [publishing, setPublishing] = useState<EditorialPublishingPayload | null>(null);
  const [image, setImage] = useState<EditorialImagePayload>(emptyEditorialImagePayload());
  const [imageRevisionNote, setImageRevisionNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [staleDismissed, setStaleDismissed] = useState(false);
  const [activeTab, setActiveTab] = useState<
    "detail" | "brief" | "article" | "image" | "publishing"
  >("detail");
  const lastItemIdRef = useRef<string | null>(null);

  function hydrateFromItem(source: ContentSeoEditorialItem, resetTab: boolean) {
    const date = source.plannedDate.slice(0, 10);
    if (resetTab) {
      setActiveTab("detail");
    }
    setTitle(source.title);
    setPlannedDate(date);
    setOriginalPlannedDate(date);
    setCascadeReschedule(false);
    setStatus(source.status);
    setObjective(source.objective ?? "");
    setPrimaryKeyword(source.primaryKeyword ?? "");
    setSecondaryKeywords((source.secondaryKeywords ?? []).join(", "));
    setNotes(source.notes ?? "");
    const parsed = parseEditorialBriefPayload(source.briefPayload ?? null);
    setBrief(hasEditorialBrief(source.briefPayload ?? null) ? parsed : null);
    setSavedBriefSnapshot(JSON.stringify(parsed));
    const parsedArticle = parseEditorialArticlePayload(
      (source.articlePayload ?? null) as Record<string, unknown> | null,
    );
    setArticle(hasEditorialArticle(source.articlePayload ?? null) ? parsedArticle : null);
    setSavedArticleSnapshot(JSON.stringify(parsedArticle));
    const parsedPublishing = source.publishingPayload
      ? parseEditorialPublishingPayload(
          source.publishingPayload as unknown as Record<string, unknown>,
        )
      : hasEditorialArticle(source.articlePayload ?? null)
        ? buildPublishingPayloadFromArticle(parsedArticle, {
            shopName: shopifyStatus?.shopName,
            brandName: brandProfile?.brandName,
            plannedDate: source.plannedDate,
            timezone: shopifyStatus?.timezone,
          })
        : null;
    const timezone = resolveEditorialTimezone(shopifyStatus?.timezone);
    const hydratedPublishing =
      parsedPublishing && source.plannedDate
        ? applyPedScheduleDefaults(parsedPublishing, {
            plannedDate: source.plannedDate,
            timezone,
          })
        : parsedPublishing;
    setPublishing(hydratedPublishing);
    setImage(parseEditorialImagePayload(source.imagePayload ?? null));
    setImageRevisionNote("");
    if (resetTab) {
      setArticleView("editor");
      setArticleBodyMode("html");
      setError(null);
      setWarning(null);
      setSuccess(null);
      setStaleDismissed(false);
    }
  }

  useEffect(() => {
    if (!open) {
      lastItemIdRef.current = null;
      return;
    }
    if (!item) return;
    const isNewItem = item.id !== lastItemIdRef.current;
    hydrateFromItem(item, isNewItem);
    lastItemIdRef.current = item.id;
  }, [item, open, shopifyStatus?.shopName, brandProfile?.brandName]);

  const briefDirty = useMemo(() => {
    if (!brief) return false;
    return JSON.stringify(brief) !== savedBriefSnapshot;
  }, [brief, savedBriefSnapshot]);

  const articleDirty = useMemo(() => {
    if (!article) return false;
    return JSON.stringify(article) !== savedArticleSnapshot;
  }, [article, savedArticleSnapshot]);

  const briefApproved = status === "brief_approved" || item?.status === "brief_approved";

  const dateChanged = plannedDate !== originalPlannedDate;
  const hasFollowingItems = useMemo(() => {
    if (!item) return false;
    return allItems.some(
      (i) =>
        i.id !== item.id && i.plannedDate.slice(0, 10) > originalPlannedDate,
    );
  }, [allItems, item, originalPlannedDate]);

  const showCascadeOption = dateChanged && hasFollowingItems;

  const statusOptions = Object.entries(CONTENT_SEO_EDITORIAL_STATUS_LABELS).map(
    ([value, label]) => ({ value, label }),
  );
  const objectiveOptions = [
    { value: "", label: "—" },
    ...Object.entries(CONTENT_SEO_EDITORIAL_OBJECTIVE_LABELS).map(([value, label]) => ({
      value,
      label,
    })),
  ];

  function syncItem(updated: ContentSeoEditorialItem) {
    onItemUpdated?.(updated);
    setStatus(updated.status);
    const parsed = parseEditorialBriefPayload(updated.briefPayload ?? null);
    if (hasEditorialBrief(updated.briefPayload ?? null)) {
      setBrief(parsed);
      setSavedBriefSnapshot(JSON.stringify(parsed));
    }
    const parsedArticle = parseEditorialArticlePayload(
      (updated.articlePayload ?? null) as Record<string, unknown> | null,
    );
    if (hasEditorialArticle(updated.articlePayload ?? null)) {
      setArticle(parsedArticle);
      setSavedArticleSnapshot(JSON.stringify(parsedArticle));
    }
    if (updated.publishingPayload) {
      const parsedPublishing = parseEditorialPublishingPayload(
        updated.publishingPayload as unknown as Record<string, unknown>,
      );
      setPublishing(parsedPublishing);
    }
    setImage(parseEditorialImagePayload(updated.imagePayload ?? null));
  }

  async function handleGenerateImage() {
    if (!item) return;
    setError(null);
    setWarning(null);
    setSuccess(null);
    try {
      const result = await generateImageMutation.mutateAsync(item.id);
      syncItem(result.item);
      if (result.warnings?.length) setWarning(result.warnings.join(" "));
      setSuccess("Immagine generata.");
      setActiveTab("image");
    } catch (err) {
      setError(formatPublishingError("Errore generazione immagine.", err));
    }
  }

  async function handleEditImage() {
    if (!item || !imageRevisionNote.trim()) return;
    setError(null);
    setWarning(null);
    setSuccess(null);
    try {
      const result = await editImageMutation.mutateAsync({
        itemId: item.id,
        revisionNote: imageRevisionNote.trim(),
      });
      syncItem(result.item);
      if (result.warnings?.length) setWarning(result.warnings.join(" "));
      setSuccess("Immagine aggiornata.");
      setImageRevisionNote("");
    } catch (err) {
      setError(formatPublishingError("Errore modifica immagine.", err));
    }
  }

  async function handleApproveImage() {
    if (!item) return;
    setError(null);
    setWarning(null);
    setSuccess(null);
    try {
      const result = await approveImageMutation.mutateAsync(item.id);
      syncItem(result.item);
      if (result.warnings?.length) setWarning(result.warnings.join(" "));
      setSuccess("Immagine approvata e sincronizzata con la pubblicazione.");
    } catch (err) {
      setError(formatPublishingError("Errore approvazione immagine.", err));
    }
  }

  async function handleRemoveImage() {
    if (!item) return;
    setError(null);
    setWarning(null);
    setSuccess(null);
    try {
      const result = await removeImageMutation.mutateAsync(item.id);
      syncItem(result.item);
      setImageRevisionNote("");
      setSuccess("Immagine rimossa.");
    } catch (err) {
      setError(formatPublishingError("Errore rimozione immagine.", err));
    }
  }

  async function handleSyncImageFromTitle() {
    if (!item) return;
    setError(null);
    setWarning(null);
    setSuccess(null);
    try {
      const result = await syncImageFromTitleMutation.mutateAsync(item.id);
      syncItem(result.item);
      if (result.warnings?.length) setWarning(result.warnings.join(" "));
      setSuccess("ALT e filename aggiornati dal titolo articolo.");
    } catch (err) {
      setError(formatPublishingError("Errore sincronizzazione immagine.", err));
    }
  }

  async function handleSave() {
    if (!item) return;
    setError(null);
    setWarning(null);
    setSuccess(null);
    try {
      const metadata = {
        title: title.trim(),
        status,
        objective: objective || null,
        primaryKeyword: primaryKeyword.trim() || null,
        secondaryKeywords: secondaryKeywords
          .split(",")
          .map((k) => k.trim())
          .filter(Boolean),
        notes: notes.trim() || null,
      };

      if (dateChanged) {
        const updated = await updateMutation.mutateAsync({
          itemId: item.id,
          data: metadata,
        });
        syncItem(updated);

        const rescheduleResult = await rescheduleMutation.mutateAsync({
          itemId: item.id,
          data: {
            plannedDate,
            cascade: cascadeReschedule,
          },
        });
        const current = rescheduleResult.items.find((i) => i.id === item.id);
        if (current) {
          syncItem(current);
          setOriginalPlannedDate(plannedDate);
        }
        if (rescheduleResult.warning) {
          setWarning(rescheduleResult.warning);
        }
        setSuccess(
          cascadeReschedule
            ? "Item e contenuti successivi riprogrammati."
            : "Data aggiornata.",
        );
      } else {
        const updated = await updateMutation.mutateAsync({
          itemId: item.id,
          data: {
            ...metadata,
            plannedDate,
          },
        });
        syncItem(updated);
        setSuccess("Item salvato.");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore durante il salvataggio.");
    }
  }

  async function handleDelete() {
    if (!item) return;
    if (!window.confirm("Eliminare questo item dal calendario?")) return;
    setError(null);
    try {
      await deleteMutation.mutateAsync(item.id);
      onClose();
    } catch {
      setError("Impossibile eliminare il contenuto editoriale.");
    }
  }

  async function handleGenerateBrief() {
    if (!item) return;
    if (
      brief &&
      briefDirty &&
      !window.confirm("Rigenerando perderai le modifiche non salvate. Continuare?")
    ) {
      return;
    }
    setError(null);
    try {
      const updated = await generateBriefMutation.mutateAsync(item.id);
      syncItem(updated);
      setActiveTab("brief");
      setSuccess("Brief generato.");
    } catch (e) {
      console.error(e);
      setError("Brief non generato per questo contenuto.");
    }
  }

  async function handleSaveBrief(approve = false) {
    if (!item || !brief) return;
    setError(null);
    try {
      const updated = await updateBriefMutation.mutateAsync({
        itemId: item.id,
        data: {
          briefPayload: brief,
          status: approve ? "brief_approved" : undefined,
        },
      });
      syncItem(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore durante il salvataggio del brief.");
    }
  }

  async function handleGenerateArticle() {
    if (!item) return;
    if (
      item?.publishingPayload &&
      !window.confirm(
        "Esiste già un payload di pubblicazione salvato. Rigenerare l'articolo potrebbe richiedere di aggiornarlo. Continuare?",
      )
    ) {
      return;
    }
    if (
      article &&
      articleDirty &&
      !window.confirm("Rigenerando perderai le modifiche non salvate. Continuare?")
    ) {
      return;
    }
    if (
      article &&
      !articleDirty &&
      !window.confirm("Rigenerare l'articolo sostituirà la bozza attuale. Continuare?")
    ) {
      return;
    }
    setError(null);
    try {
      const updated = await generateArticleMutation.mutateAsync(item.id);
      syncItem(updated);
      setStaleDismissed(false);
      setActiveTab("article");
      setArticleView("preview");
      setSuccess("Articolo generato.");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "";
      if (msg.includes("Approva il brief")) {
        setError("Approva il brief prima di generare l'articolo.");
      } else if (msg.includes("AI non configurata")) {
        setError("AI non configurata. Inserisci OPENAI_API_KEY per generare l'articolo.");
      } else {
        setError("Articolo non generato per questo contenuto.");
      }
    }
  }

  async function handleSaveArticle(markReady = false) {
    if (!item || !article) return;
    setError(null);
    try {
      const updated = await updateArticleMutation.mutateAsync({
        itemId: item.id,
        data: {
          articlePayload: article,
          status: markReady ? "ready_to_publish" : "draft_review",
        },
      });
      syncItem(updated);
      setSuccess(markReady ? "Articolo segnato pronto per pubblicazione." : "Bozza articolo salvata.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore durante il salvataggio dell'articolo.");
    }
  }

  async function handleSavePublishing() {
    if (!item || !publishing) return;
    const errors = validatePublishingPayload(publishing);
    if (errors.length > 0) {
      setError(errors.join(" "));
      return;
    }
    setError(null);
    setWarning(null);
    setSuccess(null);
    try {
      const updated = await updatePublishingMutation.mutateAsync({
        itemId: item.id,
        data: {
          publishingPayload: publishing,
          publishMode: publishing.mode,
          scheduledPublishAt: publishing.scheduledPublishAt ?? undefined,
        },
      });
      syncItem(updated);
      setSuccess("Impostazioni di pubblicazione salvate.");
    } catch (e) {
      setError(
        formatPublishingError("Errore salvataggio dati di pubblicazione.", e),
      );
    }
  }

  async function handleSyncPublishingFromArticle() {
    if (!item) return;
    setError(null);
    setSuccess(null);
    try {
      const updated = await syncPublishingMutation.mutateAsync(item.id);
      syncItem(updated);
      setStaleDismissed(false);
      setSuccess("Dati di pubblicazione aggiornati dall'articolo.");
    } catch (e) {
      setError(
        formatPublishingError("Errore aggiornamento dati di pubblicazione.", e),
      );
    }
  }

  async function handleDisconnectShopify() {
    if (!item) return;
    if (
      !window.confirm(
        "Scollegare l'articolo Shopify da questo contenuto editoriale? Non verrà eliminato su Shopify.",
      )
    ) {
      return;
    }
    setError(null);
    setSuccess(null);
    try {
      const updated = await disconnectShopifyMutation.mutateAsync(item.id);
      syncItem(updated);
      setSuccess("Articolo Shopify scollegato.");
    } catch (e) {
      setError(formatPublishingError("Errore scollegamento articolo Shopify.", e));
    }
  }

  function handleRestorePedDate() {
    if (!item || !publishing) return;
    const restored = applyPedScheduleDefaults(publishing, {
      plannedDate: item.plannedDate,
      timezone: resolveEditorialTimezone(shopifyStatus?.timezone),
      force: true,
    });
    setPublishing(restored);
  }

  async function handlePublishShopify(mode: EditorialPublishMode) {
    if (!item || !publishing) return;
    const { errors, warnings: seoWarnings } = validatePublishingPayloadWithWarnings(
      { ...publishing, mode },
      { forPublish: true },
    );
    if (errors.length > 0) {
      setError(errors.join(" "));
      return;
    }
    const hasShopifyLink = Boolean(item.shopifyArticleGid);
    const isPublishedOnShopify = item.publishStatus === "published";

    if (mode === "publish_now") {
      const confirmMessage = isPublishedOnShopify
        ? "Aggiornare l'articolo già pubblicato su Shopify con i dati attuali?"
        : hasShopifyLink
          ? "Pubblicare la bozza Shopify collegata? Sarà visibile nel blog selezionato."
          : "Pubblicare subito questo articolo su Shopify? Sarà visibile nel blog selezionato.";
      if (!window.confirm(confirmMessage)) {
        return;
      }
    }

    setError(null);
    if (seoWarnings.length > 0) {
      setWarning(seoWarnings.join(" "));
    } else {
      setWarning(null);
    }
    setSuccess(null);
    try {
      const payloadToSave = { ...publishing, mode };
      await updatePublishingMutation.mutateAsync({
        itemId: item.id,
        data: {
          publishingPayload: payloadToSave,
          publishMode: mode,
          scheduledPublishAt: payloadToSave.scheduledPublishAt ?? undefined,
        },
      });
      const result = await publishShopifyMutation.mutateAsync({
        itemId: item.id,
        data: { mode },
      });
      syncItem(result.item);
      if (result.warnings.length > 0) {
        setWarning(result.warnings.join(" "));
      }
      const successMessage =
        mode === "schedule"
          ? hasShopifyLink
            ? "Programmazione Shopify aggiornata."
            : "Articolo programmato su Shopify."
          : hasShopifyLink
            ? mode === "publish_now"
              ? isPublishedOnShopify
                ? "Articolo pubblicato su Shopify aggiornato."
                : "Bozza Shopify pubblicata."
              : "Bozza Shopify aggiornata."
            : mode === "publish_now"
              ? "Articolo pubblicato su Shopify."
              : "Bozza creata su Shopify.";
      setSuccess(successMessage);
    } catch (e) {
      void queryClient.invalidateQueries({
        queryKey: ["contentSeo", projectId, "editorialItems"],
      });
      setError(formatPublishingError("Errore invio articolo Shopify.", e));
    }
  }

  async function handlePrimaryShopifyAction() {
    if (!item) return;
    const timezone = resolveEditorialTimezone(shopifyStatus?.timezone);
    const primaryAction = getPrimaryPublishAction({
      plannedDate: item.plannedDate,
      timezone,
      publishingStale,
      hasShopifyLink: Boolean(item.shopifyArticleGid),
      isPublishedOnShopify: item.publishStatus === "published",
    });

    if (primaryAction.confirmMessage && !window.confirm(primaryAction.confirmMessage)) {
      return;
    }

    let currentPublishing = publishing;
    if (!currentPublishing && article) {
      currentPublishing = buildPublishingPayloadFromArticle(article, {
        shopName: shopifyStatus?.shopName,
        brandName: brandProfile?.brandName,
        plannedDate: item.plannedDate,
        timezone,
      });
    }
    if (!currentPublishing) return;

    setError(null);
    setSuccess(null);
    try {
      if (publishingStale) {
        const synced = await syncPublishingMutation.mutateAsync(item.id);
        syncItem(synced);
        currentPublishing = synced.publishingPayload
          ? parseEditorialPublishingPayload(
              synced.publishingPayload as unknown as Record<string, unknown>,
            )
          : currentPublishing;
        setStaleDismissed(false);
      }

      if (currentPublishing.scheduledPublishSource !== "manual") {
        currentPublishing = applyPedScheduleDefaults(currentPublishing, {
          plannedDate: item.plannedDate,
          timezone,
        });
      }
      currentPublishing = { ...currentPublishing, mode: primaryAction.mode };

      const { errors, warnings: seoWarnings } = validatePublishingPayloadWithWarnings(
        currentPublishing,
        { forPublish: true },
      );
      if (errors.length > 0) {
        setError(errors.join(" "));
        return;
      }
      if (seoWarnings.length > 0) {
        setWarning(seoWarnings.join(" "));
      }

      const updated = await updatePublishingMutation.mutateAsync({
        itemId: item.id,
        data: {
          publishingPayload: currentPublishing,
          publishMode: primaryAction.mode,
          scheduledPublishAt: currentPublishing.scheduledPublishAt ?? undefined,
        },
      });
      syncItem(updated);
      setPublishing(
        updated.publishingPayload
          ? parseEditorialPublishingPayload(
              updated.publishingPayload as unknown as Record<string, unknown>,
            )
          : currentPublishing,
      );

      const result = await publishShopifyMutation.mutateAsync({
        itemId: item.id,
        data: { mode: primaryAction.mode },
      });
      syncItem(result.item);
      if (result.warnings.length > 0) {
        setWarning(result.warnings.join(" "));
      }
      setSuccess(
        primaryAction.mode === "schedule"
          ? "Articolo programmato su Shopify."
          : primaryAction.mode === "publish_now"
            ? "Articolo pubblicato su Shopify."
            : "Bozza creata su Shopify.",
      );
    } catch (e) {
      void queryClient.invalidateQueries({
        queryKey: ["contentSeo", projectId, "editorialItems"],
      });
      setError(formatPublishingError("Errore invio articolo Shopify.", e));
    }
  }

  if (!item) return null;

  const hasBrief = Boolean(brief);
  const subtitle = [
    CONTENT_SEO_EDITORIAL_CONTENT_TYPE_LABELS[item.contentType],
    formatPlannedDate(item.plannedDate),
    CONTENT_SEO_EDITORIAL_STATUS_LABELS[item.status],
  ].join(" · ");

  const isSaving = updateMutation.isPending || rescheduleMutation.isPending;
  const itemHasBrief = hasEditorialBrief(item.briefPayload ?? null);
  const itemHasArticle = hasEditorialArticle(item.articlePayload ?? null);
  const hasArticle = Boolean(article);
  const itemHasImage = image.imageStatus !== "not_generated";
  const imageIsStale = item.imageIsStale ?? false;
  const publishingStale =
    item.publishingIsStale ?? isPublishingStale(article, publishing);
  const publishSeoIncomplete = !isPublishingSeoComplete(publishing);
  const hasShopifyLink = Boolean(item.shopifyArticleGid);
  const isPublishedOnShopify = item.publishStatus === "published";
  const canWriteContent = scopesData?.canWriteContent ?? false;
  const publishActionsDisabled =
    status !== "ready_to_publish" ||
    !canWriteContent ||
    scopesLoading ||
    publishShopifyMutation.isPending ||
    syncPublishingMutation.isPending ||
    updatePublishingMutation.isPending ||
    !publishing?.author.trim() ||
    publishingStale ||
    publishSeoIncomplete;

  const primaryPublishDisabled =
    status !== "ready_to_publish" ||
    !canWriteContent ||
    scopesLoading ||
    publishShopifyMutation.isPending ||
    syncPublishingMutation.isPending ||
    updatePublishingMutation.isPending ||
    !publishing?.author.trim() ||
    publishSeoIncomplete;

  const editorialTimezone = resolveEditorialTimezone(shopifyStatus?.timezone);
  const primaryPublishAction = getPrimaryPublishAction({
    plannedDate: item.plannedDate,
    timezone: editorialTimezone,
    publishingStale,
    hasShopifyLink,
    isPublishedOnShopify,
  });
  const plannedClassification = classifyPlannedDate(item.plannedDate, editorialTimezone);

  const footer =
    activeTab === "detail" ? (
      <>
        <button type="button" className="gcr-btn gcr-btn--secondary" onClick={onClose}>
          Chiudi
        </button>
        <button
          type="button"
          className="gcr-btn gcr-btn--danger"
          disabled={deleteMutation.isPending}
          onClick={() => void handleDelete()}
        >
          Elimina
        </button>
        <button
          type="button"
          className="gcr-btn gcr-btn--primary"
          disabled={isSaving || !title.trim()}
          onClick={() => void handleSave()}
        >
          {isSaving ? "Salvataggio…" : "Salva item"}
        </button>
      </>
    ) : activeTab === "brief" ? (
      <>
        <button type="button" className="gcr-btn gcr-btn--secondary" onClick={onClose}>
          Chiudi
        </button>
        {!hasBrief && (
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={generateBriefMutation.isPending}
            onClick={() => void handleGenerateBrief()}
          >
            {generateBriefMutation.isPending ? "Generazione…" : "Genera brief"}
          </button>
        )}
        {hasBrief && (
          <>
            <button
              type="button"
              className="gcr-btn gcr-btn--ghost"
              disabled={generateBriefMutation.isPending}
              onClick={() => void handleGenerateBrief()}
            >
              {generateBriefMutation.isPending ? "Rigenerazione…" : "Rigenera brief"}
            </button>
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary"
              disabled={updateBriefMutation.isPending}
              onClick={() => void handleSaveBrief(false)}
            >
              Salva brief
            </button>
            <button
              type="button"
              className="gcr-btn gcr-btn--primary"
              disabled={updateBriefMutation.isPending}
              onClick={() => void handleSaveBrief(true)}
            >
              Approva brief
            </button>
          </>
        )}
      </>
    ) : activeTab === "article" ? (
      <>
        <button type="button" className="gcr-btn gcr-btn--secondary" onClick={onClose}>
          Chiudi
        </button>
        {!hasArticle && (
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={!briefApproved || generateArticleMutation.isPending}
            onClick={() => void handleGenerateArticle()}
          >
            {generateArticleMutation.isPending ? "Generazione…" : "Genera articolo"}
          </button>
        )}
        {hasArticle && (
          <>
            <button
              type="button"
              className="gcr-btn gcr-btn--ghost"
              disabled={!briefApproved || generateArticleMutation.isPending}
              onClick={() => void handleGenerateArticle()}
            >
              {generateArticleMutation.isPending ? "Rigenerazione…" : "Rigenera articolo"}
            </button>
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary"
              disabled={updateArticleMutation.isPending}
              onClick={() => void handleSaveArticle(false)}
            >
              Salva bozza articolo
            </button>
            <button
              type="button"
              className="gcr-btn gcr-btn--primary"
              disabled={updateArticleMutation.isPending}
              onClick={() => void handleSaveArticle(true)}
            >
              Segna pronto per pubblicazione
            </button>
          </>
        )}
      </>
    ) : activeTab === "image" ? (
      <>
        <button type="button" className="gcr-btn gcr-btn--secondary" onClick={onClose}>
          Chiudi
        </button>
      </>
    ) : (
      <>
        <button type="button" className="gcr-btn gcr-btn--secondary" onClick={onClose}>
          Chiudi
        </button>
        <button
          type="button"
          className="gcr-btn gcr-btn--secondary"
          disabled={!publishing || updatePublishingMutation.isPending}
          onClick={() => void handleSavePublishing()}
        >
          {updatePublishingMutation.isPending ? "Salvataggio…" : "Salva publishing"}
        </button>
        {plannedClassification === "today" && !isPublishedOnShopify && (
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary"
            disabled={publishActionsDisabled || !publishing}
            onClick={() => void handlePublishShopify("draft")}
          >
            {publishShopifyMutation.isPending ? "Invio…" : "Crea bozza Shopify"}
          </button>
        )}
        <button
          type="button"
          className="gcr-btn gcr-btn--primary"
          disabled={primaryPublishDisabled || !publishing}
          onClick={() => void handlePrimaryShopifyAction()}
        >
          {publishShopifyMutation.isPending || syncPublishingMutation.isPending
            ? "Invio…"
            : primaryPublishAction.label}
        </button>
      </>
    );

  return (
    <AppModal
      open={open}
      onClose={onClose}
      title="Dettaglio contenuto editoriale"
      subtitle={subtitle}
      maxWidth="lg"
      footer={footer}
    >
      <div className="editorial-item-modal">
        {error && <div className="gcr-alert gcr-alert--error">{error}</div>}
        {warning && <div className="gcr-alert gcr-alert--warning">{warning}</div>}
        {success && <div className="gcr-alert gcr-alert--success">{success}</div>}

        <div className="editorial-item-modal__tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "detail"}
            className={[
              "editorial-item-modal__tab",
              activeTab === "detail" ? "editorial-item-modal__tab--active" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => setActiveTab("detail")}
          >
            Dettaglio
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "brief"}
            className={[
              "editorial-item-modal__tab",
              activeTab === "brief" ? "editorial-item-modal__tab--active" : "",
              itemHasBrief ? "editorial-item-modal__tab--has-content" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => setActiveTab("brief")}
          >
            Brief SEO
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "article"}
            className={[
              "editorial-item-modal__tab",
              activeTab === "article" ? "editorial-item-modal__tab--active" : "",
              itemHasArticle ? "editorial-item-modal__tab--has-content" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => setActiveTab("article")}
          >
            Articolo & Anteprima
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "image"}
            className={[
              "editorial-item-modal__tab",
              activeTab === "image" ? "editorial-item-modal__tab--active" : "",
              itemHasImage ? "editorial-item-modal__tab--has-content" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => setActiveTab("image")}
          >
            Immagine
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "publishing"}
            className={[
              "editorial-item-modal__tab",
              activeTab === "publishing" ? "editorial-item-modal__tab--active" : "",
              itemHasArticle ? "editorial-item-modal__tab--has-content" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => setActiveTab("publishing")}
          >
            Pubblicazione
          </button>
        </div>

        {activeTab === "detail" && (
          <section className="editorial-item-modal__section">
            <label className="gcr-field">
              <span className="gcr-field__label">Titolo</span>
              <input
                className="gcr-input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </label>

            <AppDatePicker
              label="Data pianificata"
              value={plannedDate}
              onChange={setPlannedDate}
            />

            {showCascadeOption && (
              <AppCheckbox
                variant="card"
                checked={cascadeReschedule}
                onChange={setCascadeReschedule}
                label="Riprogramma anche i contenuti successivi mantenendo la frequenza del piano"
                description="Se attivo, tutti i contenuti successivi verranno spostati dello stesso numero di giorni."
              />
            )}

            <AppSelect
              label="Stato"
              value={status}
              options={statusOptions}
              onChange={(v) => setStatus(v as ContentSeoEditorialStatus)}
            />

            <AppSelect
              label="Obiettivo"
              value={objective}
              options={objectiveOptions}
              onChange={(v) => setObjective(v as ContentSeoEditorialObjective | "")}
            />

            <label className="gcr-field">
              <span className="gcr-field__label">Keyword principale</span>
              <input
                className="gcr-input"
                value={primaryKeyword}
                onChange={(e) => setPrimaryKeyword(e.target.value)}
              />
            </label>

            <label className="gcr-field">
              <span className="gcr-field__label">Keyword secondarie (separate da virgola)</span>
              <input
                className="gcr-input"
                value={secondaryKeywords}
                onChange={(e) => setSecondaryKeywords(e.target.value)}
              />
            </label>

            <AutoResizeTextarea
              label="Note"
              value={notes}
              onChange={setNotes}
              minRows={2}
              maxRows={12}
            />

            {item.linkedShopifyProductTitle && (
              <p className="editorial-item-modal__linked">
                Prodotto collegato: <strong>{item.linkedShopifyProductTitle}</strong>
              </p>
            )}
          </section>
        )}

        {activeTab === "brief" && (
          <section className="editorial-item-modal__section editorial-item-modal__brief-tab">
            <div className="editorial-item-modal__brief-status">
              <span className="gcr-field__label">Stato brief</span>
              <EditorialStatusBadge status={status} />
            </div>

            {hasBrief ? (
              <>
                <EditorialBriefEditor value={brief!} onChange={setBrief} />
                <EditorialAiGenerationAccordion
                  projectId={projectId}
                  item={item}
                  variant="brief"
                />
              </>
            ) : (
              <div className="editorial-item-modal__brief-empty gcr-card">
                <p className="gcr-card__description">
                  Brief SEO non ancora generato. Genera il brief usando Brand Intelligence,
                  prodotto collegato e Safe Claims.
                </p>
              </div>
            )}
          </section>
        )}

        {activeTab === "article" && (
          <section className="editorial-item-modal__section editorial-item-modal__article-tab">
            <div className="editorial-item-modal__brief-status">
              <span className="gcr-field__label">Stato articolo</span>
              <EditorialStatusBadge status={status} />
            </div>

            {!briefApproved && (
              <div className="editorial-item-modal__brief-empty gcr-card">
                <p className="gcr-card__description">
                  Approva prima il brief SEO per generare l&apos;articolo.
                </p>
              </div>
            )}

            {briefApproved && !hasArticle && (
              <div className="editorial-item-modal__brief-empty gcr-card">
                <p className="gcr-card__description">
                  Genera una bozza articolo usando il brief approvato e la Brand Intelligence.
                </p>
              </div>
            )}

            {hasArticle && (
              <>
                <div className="editorial-article-subtabs" role="tablist">
                  <button
                    type="button"
                    role="tab"
                    aria-selected={articleView === "editor"}
                    className={[
                      "editorial-article-subtabs__tab",
                      articleView === "editor" ? "editorial-article-subtabs__tab--active" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    onClick={() => setArticleView("editor")}
                  >
                    Editor
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={articleView === "preview"}
                    className={[
                      "editorial-article-subtabs__tab",
                      articleView === "preview" ? "editorial-article-subtabs__tab--active" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    onClick={() => setArticleView("preview")}
                  >
                    Anteprima
                  </button>
                </div>

                {articleView === "editor" ? (
                  <EditorialArticleEditor
                    value={article!}
                    onChange={setArticle}
                    bodyMode={articleBodyMode}
                    onBodyModeChange={setArticleBodyMode}
                  />
                ) : (
                  <EditorialArticlePreview value={article!} />
                )}
                <EditorialAiGenerationAccordion
                  projectId={projectId}
                  item={item}
                  variant="article"
                />
              </>
            )}
          </section>
        )}

        {activeTab === "image" && item && (
          <section className="editorial-item-modal__section editorial-image-tab-wrap">
            <EditorialImageTab
              projectId={projectId}
              itemId={item.id}
              hasArticle={hasArticle}
              article={article}
              image={image}
              imageIsStale={imageIsStale}
              revisionNote={imageRevisionNote}
              onRevisionNoteChange={setImageRevisionNote}
              onGenerate={() => void handleGenerateImage()}
              onRegenerate={() => void handleGenerateImage()}
              onApplyEdit={() => void handleEditImage()}
              onApprove={() => void handleApproveImage()}
              onRemove={() => void handleRemoveImage()}
              onSyncFromTitle={() => void handleSyncImageFromTitle()}
              generateLoading={generateImageMutation.isPending}
              editLoading={editImageMutation.isPending}
              approveLoading={approveImageMutation.isPending}
              removeLoading={removeImageMutation.isPending}
              syncLoading={syncImageFromTitleMutation.isPending}
            />
          </section>
        )}

        {activeTab === "publishing" && publishing && (
          <section className="editorial-item-modal__section editorial-publishing-tab-wrap">
            <EditorialPublishingTab
              item={item}
              status={status}
              hasArticle={hasArticle}
              publishingStale={publishingStale}
              staleDismissed={staleDismissed}
              publishBlockedByStale={publishingStale}
              publishBlockedBySeo={publishSeoIncomplete}
              publishError={error}
              plannedDate={item.plannedDate}
              timezone={shopifyStatus?.timezone}
              publishing={publishing}
              onChange={setPublishing}
              onSyncFromArticle={() => void handleSyncPublishingFromArticle()}
              onDismissStale={() => setStaleDismissed(true)}
              onDisconnectShopify={() => void handleDisconnectShopify()}
              onRestorePedDate={handleRestorePedDate}
              syncLoading={syncPublishingMutation.isPending}
              disconnectLoading={disconnectShopifyMutation.isPending}
              blogs={blogsData?.blogs ?? []}
              blogsLoading={blogsLoading}
              blogsSyncRequired={blogsData?.syncRequired ?? false}
              canWriteContent={canWriteContent}
              scopesLoading={scopesLoading}
            />
          </section>
        )}
      </div>
    </AppModal>
  );
}
