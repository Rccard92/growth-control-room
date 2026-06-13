const LOGO_SRC = {
  full: "/brand/gcr-logo-full.png",
  mark: "/brand/gcr-favicon-512.png",
} as const;

interface BrandLogoProps {
  variant?: keyof typeof LOGO_SRC;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function BrandLogo({
  variant = "full",
  size = "md",
  className,
}: BrandLogoProps) {
  const classes = ["brand-logo", `brand-logo--${size}`, className]
    .filter(Boolean)
    .join(" ");

  return (
    <span className={classes}>
      <img
        className="brand-logo__image"
        src={LOGO_SRC[variant]}
        alt="Growth Control Room"
        decoding="async"
      />
    </span>
  );
}
