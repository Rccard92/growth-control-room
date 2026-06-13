import { useCallback, useRef, useState } from "react";

const MAX_FILES = 10;
const MAX_BYTES = 15 * 1024 * 1024;
const ACCEPT = ".pdf,.docx,.txt,.md";

interface BrandFileDropzoneProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
}

function validateFiles(files: File[]): string | null {
  if (files.length > MAX_FILES) {
    return `Massimo ${MAX_FILES} file per batch.`;
  }
  for (const file of files) {
    if (file.size > MAX_BYTES) {
      return `${file.name} supera il limite di 15MB.`;
    }
    const lower = file.name.toLowerCase();
    if (![".pdf", ".docx", ".txt", ".md"].some((ext) => lower.endsWith(ext))) {
      return `${file.name}: formato non supportato. Usa PDF, DOCX, TXT o MD.`;
    }
  }
  return null;
}

export function BrandFileDropzone({ onFilesSelected, disabled }: BrandFileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFiles = useCallback(
    (fileList: FileList | null) => {
      if (!fileList?.length) return;
      const files = Array.from(fileList);
      const err = validateFiles(files);
      if (err) {
        setError(err);
        return;
      }
      setError(null);
      onFilesSelected(files);
    },
    [onFilesSelected],
  );

  return (
    <div className="bi-dropzone-wrap">
      <div
        className={`bi-dropzone ${dragOver ? "bi-dropzone--active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          if (!disabled) handleFiles(e.dataTransfer.files);
        }}
        onClick={() => !disabled && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
      >
        <p className="bi-dropzone__title">Trascina i file qui</p>
        <p className="bi-dropzone__hint">PDF, DOCX, TXT, MD — max 10 file, 15MB ciascuno</p>
        <button
          type="button"
          className="gcr-btn gcr-btn--ghost gcr-btn--sm"
          disabled={disabled}
          onClick={(e) => {
            e.stopPropagation();
            inputRef.current?.click();
          }}
        >
          Seleziona file
        </button>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          multiple
          hidden
          disabled={disabled}
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>
      {error && <div className="gcr-alert gcr-alert--error" style={{ marginTop: "0.75rem" }}>{error}</div>}
    </div>
  );
}
