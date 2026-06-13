import { useCallback, useRef, useState } from "react";
import type { SeoProposalGenerateFieldResponse } from "@gcr/shared";
import type { FieldSource } from "../components/content/optimizer/seoFieldState";

export interface SeoAiQueueItem {
  id: string;
  fieldKey: string;
  valueAtEnqueue: string;
  sourceAtEnqueue: FieldSource;
  run: () => Promise<SeoProposalGenerateFieldResponse>;
}

export interface SeoAiQueueHandlers {
  onStartGenerating: (fieldKey: string) => void;
  onClearGenerating: (fieldKey: string) => void;
  onApplyResult: (fieldKey: string, response: SeoProposalGenerateFieldResponse) => void;
  onSkipped: (fieldKey: string, message: string) => void;
  onError: (fieldKey: string, message: string) => void;
  getFieldState: (fieldKey: string) => { value: string; source: FieldSource } | undefined;
}

export function useSeoAiQueue(handlers: SeoAiQueueHandlers) {
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;

  const queueRef = useRef<SeoAiQueueItem[]>([]);
  const processingRef = useRef(false);
  const activeFieldRef = useRef<string | null>(null);
  const [pendingQueueCount, setPendingQueueCount] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [generatingFields, setGeneratingFields] = useState<Set<string>>(new Set());

  const syncCounts = useCallback(() => {
    const waiting = queueRef.current.length;
    const active = processingRef.current ? 1 : 0;
    setPendingQueueCount(waiting + active);
    setIsProcessing(processingRef.current || waiting > 0);
  }, []);

  const finishField = useCallback((fieldKey: string) => {
    const stillQueued = queueRef.current.some((q) => q.fieldKey === fieldKey);
    const stillActive = activeFieldRef.current === fieldKey && processingRef.current;
    if (!stillQueued && !stillActive) {
      setGeneratingFields((prev) => {
        if (!prev.has(fieldKey)) return prev;
        const next = new Set(prev);
        next.delete(fieldKey);
        return next;
      });
      handlersRef.current.onClearGenerating(fieldKey);
    }
  }, []);

  const processNext = useCallback(async () => {
    if (processingRef.current) return;
    const item = queueRef.current.shift();
    if (!item) {
      syncCounts();
      return;
    }

    processingRef.current = true;
    activeFieldRef.current = item.fieldKey;
    syncCounts();
    handlersRef.current.onStartGenerating(item.fieldKey);

    try {
      const response = await item.run();
      const current = handlersRef.current.getFieldState(item.fieldKey);
      if (
        current &&
        current.source === "manual" &&
        current.value !== item.valueAtEnqueue
      ) {
        handlersRef.current.onSkipped(
          item.fieldKey,
          "Modificato manualmente durante la generazione AI.",
        );
      } else {
        handlersRef.current.onApplyResult(item.fieldKey, response);
      }
    } catch {
      handlersRef.current.onError(item.fieldKey, "Generazione AI non riuscita.");
    } finally {
      processingRef.current = false;
      activeFieldRef.current = null;
      finishField(item.fieldKey);
      syncCounts();
      void processNext();
    }
  }, [finishField, syncCounts]);

  const enqueue = useCallback(
    (item: Omit<SeoAiQueueItem, "id"> & { id?: string }) => {
      const full: SeoAiQueueItem = {
        ...item,
        id: item.id ?? crypto.randomUUID(),
      };
      queueRef.current.push(full);
      setGeneratingFields((prev) => new Set(prev).add(full.fieldKey));
      handlersRef.current.onStartGenerating(full.fieldKey);
      syncCounts();
      void processNext();
    },
    [processNext, syncCounts],
  );

  const clear = useCallback(() => {
    queueRef.current = [];
    processingRef.current = false;
    activeFieldRef.current = null;
    setGeneratingFields(new Set());
    setPendingQueueCount(0);
    setIsProcessing(false);
  }, []);

  const isGeneratingField = useCallback(
    (fieldKey: string) => generatingFields.has(fieldKey),
    [generatingFields],
  );

  return {
    enqueue,
    clear,
    pendingQueueCount,
    isProcessing,
    isGeneratingField,
  };
}
