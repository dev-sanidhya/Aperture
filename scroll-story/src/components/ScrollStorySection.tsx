import { useRef } from "react";
import {
  motion,
  useScroll,
  useTransform,
  useSpring,
  MotionValue,
} from "framer-motion";

/* ─── Aperture iris SVG (inline, flat gold) ─────────────────── */
function ApertureIcon({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 36 36" fill="none">
      <g fill="#d1a26a">
        <path d="M23.5,18 L32,18 A14,14 0 0,1 28.7,27 L22.6,21.9 A5.5,5.5 0 0,0 23.5,18 Z" />
        <path d="M21,23.2 L25,30.1 A14,14 0 0,1 15.6,31.8 L16.95,23.9 A5.5,5.5 0 0,0 21,23.2 Z" />
        <path d="M15,23.2 L11,30.1 A14,14 0 0,1 4.84,22.8 L12.36,20.05 A5.5,5.5 0 0,0 15,23.2 Z" />
        <path d="M12.5,18 L4,18 A14,14 0 0,1 7.3,9 L13.4,14.1 A5.5,5.5 0 0,0 12.5,18 Z" />
        <path d="M15,12.8 L11,5.9 A14,14 0 0,1 20.4,4.2 L19.04,12.1 A5.5,5.5 0 0,0 15,12.8 Z" />
        <path d="M21,12.8 L25,5.9 A14,14 0 0,1 31.16,13.2 L23.64,15.95 A5.5,5.5 0 0,0 21,12.8 Z" />
      </g>
      <circle cx="18" cy="18" r="5.5" fill="#0d1117" stroke="rgba(209,162,106,0.45)" strokeWidth="0.8" />
      <circle cx="18" cy="18" r="2" fill="#d1a26a" />
    </svg>
  );
}

/* ─── Smooth spring wrapper ─────────────────────────────────── */
function useSmooth(v: MotionValue<number>, stiffness = 80, damping = 20) {
  return useSpring(v, { stiffness, damping, restDelta: 0.001 });
}

/* ─── Card shell ────────────────────────────────────────────── */
function GlassCard({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-2xl border border-white/[0.08] shadow-[0_24px_56px_rgba(0,0,0,0.55)] ${className}`}
      style={{
        background: "rgba(255,255,255,0.04)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
      }}
    >
      {children}
    </div>
  );
}

/* ─── Pill tag ──────────────────────────────────────────────── */
function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span
      className="text-[10px] font-semibold px-2.5 py-1 rounded-full border border-white/[0.08] text-white/40"
      style={{ background: "rgba(255,255,255,0.03)" }}
    >
      {children}
    </span>
  );
}

/* ─── Progress bar ──────────────────────────────────────────── */
function ProgressBar({ progress }: { progress: MotionValue<number> }) {
  const width = useTransform(progress, [0, 1], ["0%", "100%"]);
  return (
    <div className="absolute top-0 left-0 right-0 h-[2px] z-50 bg-white/5">
      <motion.div
        style={{ width }}
        className="h-full"
        style={{
          width,
          background: "linear-gradient(90deg, #d1a26a, #8fd3c4, #d1a26a)",
          backgroundSize: "200% 100%",
        }}
      />
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   MAIN COMPONENT
════════════════════════════════════════════════════════════ */
export default function ScrollStorySection() {
  const ref = useRef<HTMLDivElement>(null);

  /* Raw scroll progress 0 → 1 over the 400vh section */
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end end"],
  });

  /* ── Background parallax blobs ─────────────────────────── */
  const bgY     = useSmooth(useTransform(scrollYProgress, [0, 1], [0, -140]), 60, 18);
  const blob1X  = useSmooth(useTransform(scrollYProgress, [0, 1], [0,  -80]), 50, 15);
  const blob1Y  = useSmooth(useTransform(scrollYProgress, [0, 1], [0, -120]), 50, 15);
  const blob2X  = useSmooth(useTransform(scrollYProgress, [0, 1], [0,   80]), 45, 16);
  const blob2Y  = useSmooth(useTransform(scrollYProgress, [0, 1], [0,  -90]), 45, 16);
  const blob3Y  = useSmooth(useTransform(scrollYProgress, [0, 1], [0,  -60]), 40, 18);

  /* ── Typography ─────────────────────────────────────────── */
  const headingOpacity  = useTransform(scrollYProgress, [0, 0.18], [0, 1]);
  const headingY        = useSmooth(useTransform(scrollYProgress, [0, 0.25], [36, 0]), 90, 22);
  const subtitleOpacity = useTransform(scrollYProgress, [0.06, 0.26], [0, 1]);
  const subtitleY       = useSmooth(useTransform(scrollYProgress, [0.06, 0.28], [24, 0]), 90, 22);
  const ctaOpacity      = useTransform(scrollYProgress, [0.12, 0.32], [0, 1]);
  const ctaScale        = useSmooth(useTransform(scrollYProgress, [0.12, 0.32], [0.82, 1]), 100, 24);

  /* ── Center panel ───────────────────────────────────────── */
  const centerOpacity = useTransform(scrollYProgress, [0, 0.14], [0, 1]);
  const centerScale   = useSmooth(useTransform(scrollYProgress, [0, 0.5, 1], [0.88, 1, 1.04]), 90, 22);
  const centerY       = useSmooth(useTransform(scrollYProgress, [0, 1], [60, -60]), 70, 20);

  /* ── TL card ────────────────────────────────────────────── */
  const tlOpacity = useTransform(scrollYProgress, [0.04, 0.28], [0, 1]);
  const tlY       = useSmooth(useTransform(scrollYProgress, [0, 1], [160, -110]), 65, 18);
  const tlX       = useSmooth(useTransform(scrollYProgress, [0, 0.7], [-50, 0]), 65, 18);
  const tlRotate  = useSmooth(useTransform(scrollYProgress, [0, 0.65], [-10, 0]), 70, 20);

  /* ── TR card ────────────────────────────────────────────── */
  const trOpacity = useTransform(scrollYProgress, [0.08, 0.32], [0, 1]);
  const trY       = useSmooth(useTransform(scrollYProgress, [0, 1], [120, -130]), 60, 17);
  const trX       = useSmooth(useTransform(scrollYProgress, [0, 0.7], [50, 0]), 60, 17);
  const trRotate  = useSmooth(useTransform(scrollYProgress, [0, 0.65], [10, 0]), 70, 20);

  /* ── BL card ────────────────────────────────────────────── */
  const blOpacity = useTransform(scrollYProgress, [0.14, 0.38], [0, 1]);
  const blY       = useSmooth(useTransform(scrollYProgress, [0, 1], [200, -80]), 55, 16);
  const blRotate  = useSmooth(useTransform(scrollYProgress, [0, 0.7], [-7, 0]), 65, 20);

  /* ── BR card ────────────────────────────────────────────── */
  const brOpacity = useTransform(scrollYProgress, [0.18, 0.42], [0, 1]);
  const brY       = useSmooth(useTransform(scrollYProgress, [0, 1], [180, -95]), 55, 16);
  const brRotate  = useSmooth(useTransform(scrollYProgress, [0, 0.7], [7, 0]), 65, 20);

  /* ── Floating label (bottom center) ────────────────────── */
  const labelOpacity = useTransform(scrollYProgress, [0.5, 0.7], [0, 1]);
  const labelY       = useSmooth(useTransform(scrollYProgress, [0.5, 0.75], [20, 0]), 80, 22);

  return (
    <section ref={ref} className="relative" style={{ height: "400vh", background: "#0a0d12" }}>

      {/* ════ STICKY VIEWPORT ════════════════════════════════ */}
      <div className="sticky top-0 h-screen overflow-hidden">

        {/* Progress bar */}
        <ProgressBar progress={scrollYProgress} />

        {/* ── Background layer ───────────────────────────── */}
        <motion.div style={{ y: bgY }} className="absolute inset-0 pointer-events-none">
          {/* Gold blob top-left */}
          <motion.div
            style={{ x: blob1X, y: blob1Y }}
            className="absolute -top-32 -left-32 w-[640px] h-[640px] rounded-full"
            style={{
              x: blob1X, y: blob1Y,
              background: "radial-gradient(circle, rgba(209,162,106,0.12) 0%, transparent 70%)",
              filter: "blur(80px)",
            }}
          />
          {/* Teal blob bottom-right */}
          <motion.div
            style={{ x: blob2X, y: blob2Y }}
            className="absolute -bottom-32 -right-32 w-[580px] h-[580px] rounded-full"
            style={{
              x: blob2X, y: blob2Y,
              background: "radial-gradient(circle, rgba(143,211,196,0.09) 0%, transparent 70%)",
              filter: "blur(80px)",
            }}
          />
          {/* Gold blob center */}
          <motion.div
            style={{ y: blob3Y }}
            className="absolute top-[30%] left-[35%] w-[400px] h-[400px] rounded-full"
            style={{
              y: blob3Y,
              background: "radial-gradient(circle, rgba(209,162,106,0.06) 0%, transparent 70%)",
              filter: "blur(60px)",
            }}
          />
        </motion.div>

        {/* Subtle grid */}
        <div
          className="absolute inset-0 pointer-events-none opacity-[0.025]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.12) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.12) 1px, transparent 1px)",
            backgroundSize: "72px 72px",
          }}
        />

        {/* ── Heading ────────────────────────────────────── */}
        <motion.div
          style={{ opacity: headingOpacity, y: headingY }}
          className="absolute top-12 left-1/2 -translate-x-1/2 text-center z-20 pointer-events-none"
        >
          <span
            className="block text-xs font-bold tracking-[0.28em] uppercase mb-3"
            style={{ color: "#d1a26a" }}
          >
            Aperture Studio
          </span>
          <h2
            className="text-5xl font-bold leading-[1.1] text-white"
            style={{ fontFamily: "'Cormorant Garamond', serif", fontWeight: 700 }}
          >
            Every angle.<br />One partner.
          </h2>
        </motion.div>

        {/* ── Subtitle ───────────────────────────────────── */}
        <motion.p
          style={{ opacity: subtitleOpacity, y: subtitleY }}
          className="absolute bottom-28 left-1/2 -translate-x-1/2 text-center text-sm max-w-xs z-20 pointer-events-none leading-relaxed"
          style={{
            opacity: subtitleOpacity,
            y: subtitleY,
            color: "rgba(181,176,166,0.8)",
          }}
        >
          Websites, apps, AI systems, automation, and branding — built end to end.
        </motion.p>

        {/* ── CTA ────────────────────────────────────────── */}
        <motion.div
          style={{ opacity: ctaOpacity, scale: ctaScale }}
          className="absolute bottom-10 left-1/2 -translate-x-1/2 z-20"
        >
          <button
            className="px-8 py-3 rounded-full text-sm font-semibold tracking-wide cursor-pointer transition-opacity hover:opacity-90"
            style={{
              background: "#d1a26a",
              color: "#0a0d12",
              fontFamily: "Manrope, sans-serif",
            }}
          >
            Start a project
          </button>
        </motion.div>

        {/* ═══════ CENTER PANEL ══════════════════════════════ */}
        <motion.div
          style={{ scale: centerScale, y: centerY, opacity: centerOpacity }}
          className="absolute left-1/2 top-1/2 z-10"
          style={{
            scale: centerScale,
            y: centerY,
            opacity: centerOpacity,
            x: "-50%",
            translateY: "-50%",
            left: "50%",
            top: "50%",
            position: "absolute",
            width: "420px",
          }}
        >
          <GlassCard>
            {/* Header strip */}
            <div
              className="px-7 pt-7 pb-5"
              style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
            >
              <div className="flex items-center gap-3 mb-4">
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center"
                  style={{
                    background: "rgba(209,162,106,0.08)",
                    border: "1px solid rgba(209,162,106,0.18)",
                  }}
                >
                  <ApertureIcon size={18} />
                </div>
                <span className="text-sm font-medium" style={{ color: "rgba(255,255,255,0.5)" }}>
                  Aperture Studio
                </span>
                <span
                  className="ml-auto text-[10px] font-bold px-2.5 py-1 rounded-full"
                  style={{
                    color: "#d1a26a",
                    background: "rgba(209,162,106,0.1)",
                    border: "1px solid rgba(209,162,106,0.2)",
                  }}
                >
                  Active
                </span>
              </div>
              <h3
                className="text-2xl font-bold text-white"
                style={{ fontFamily: "'Cormorant Garamond', serif" }}
              >
                Clean Digital Systems
              </h3>
              <p className="text-xs mt-1" style={{ color: "rgba(255,255,255,0.38)" }}>
                Full-stack digital partner
              </p>
            </div>

            {/* Metrics */}
            <div className="px-7 py-6 space-y-4">
              {[
                { label: "Websites & Apps", pct: 92, color: "#d1a26a" },
                { label: "AI Systems",      pct: 78, color: "#8fd3c4" },
                { label: "Automation",      pct: 85, color: "#d1a26a" },
              ].map((item) => (
                <div key={item.label}>
                  <div className="flex justify-between text-xs mb-1.5" style={{ color: "rgba(255,255,255,0.42)" }}>
                    <span>{item.label}</span>
                    <span style={{ color: item.color, fontWeight: 600 }}>{item.pct}%</span>
                  </div>
                  <div className="h-[3px] rounded-full" style={{ background: "rgba(255,255,255,0.05)" }}>
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${item.pct}%`, background: item.color, opacity: 0.8 }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Footer strip */}
            <div
              className="px-7 py-4 flex items-center gap-2"
              style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}
            >
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="text-[11px]" style={{ color: "rgba(255,255,255,0.3)" }}>
                Available for new projects
              </span>
            </div>
          </GlassCard>
        </motion.div>

        {/* ═══════ TL CARD — Presence ════════════════════════ */}
        <motion.div
          style={{ opacity: tlOpacity, y: tlY, x: tlX, rotate: tlRotate }}
          className="absolute z-10"
          style={{
            opacity: tlOpacity, y: tlY, x: tlX, rotate: tlRotate,
            left: "7%", top: "24%", width: "240px",
          }}
        >
          <GlassCard className="p-6">
            <div
              className="w-8 h-8 rounded-xl flex items-center justify-center mb-4 text-xs font-bold"
              style={{
                background: "rgba(209,162,106,0.08)",
                border: "1px solid rgba(209,162,106,0.16)",
                color: "#d1a26a",
              }}
            >
              01
            </div>
            <h4 className="text-white text-sm font-semibold mb-1">Presence</h4>
            <p className="text-xs leading-relaxed mb-4" style={{ color: "rgba(255,255,255,0.36)" }}>
              Brand identity, websites, redesigns, landing pages, ecommerce.
            </p>
            <div className="flex flex-wrap gap-1.5">
              <Tag>Branding</Tag>
              <Tag>UI/UX</Tag>
            </div>
          </GlassCard>
        </motion.div>

        {/* ═══════ TR CARD — Products ════════════════════════ */}
        <motion.div
          style={{
            opacity: trOpacity, y: trY, x: trX, rotate: trRotate,
            right: "7%", top: "18%", width: "240px", position: "absolute", zIndex: 10,
          }}
        >
          <GlassCard className="p-6">
            <div
              className="w-8 h-8 rounded-xl flex items-center justify-center mb-4 text-xs font-bold"
              style={{
                background: "rgba(143,211,196,0.08)",
                border: "1px solid rgba(143,211,196,0.16)",
                color: "#8fd3c4",
              }}
            >
              02
            </div>
            <h4 className="text-white text-sm font-semibold mb-1">Products</h4>
            <p className="text-xs leading-relaxed mb-4" style={{ color: "rgba(255,255,255,0.36)" }}>
              Web apps, SaaS MVPs, dashboards, portals, internal tools.
            </p>
            <div className="flex flex-wrap gap-1.5">
              <Tag>Web Apps</Tag>
              <Tag>MVPs</Tag>
            </div>
          </GlassCard>
        </motion.div>

        {/* ═══════ BL CARD — Systems ═════════════════════════ */}
        <motion.div
          style={{
            opacity: blOpacity, y: blY, rotate: blRotate,
            left: "9%", bottom: "16%", width: "220px", position: "absolute", zIndex: 10,
          }}
        >
          <GlassCard className="p-5">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center mb-3 text-[10px] font-bold"
              style={{
                background: "rgba(209,162,106,0.08)",
                border: "1px solid rgba(209,162,106,0.14)",
                color: "#d1a26a",
              }}
            >
              03
            </div>
            <h4 className="text-white text-sm font-semibold mb-1">Systems</h4>
            <p className="text-xs leading-relaxed" style={{ color: "rgba(255,255,255,0.34)" }}>
              APIs, CRM pipelines, intake flows, lead routing, integrations.
            </p>
          </GlassCard>
        </motion.div>

        {/* ═══════ BR CARD — Intelligence ════════════════════ */}
        <motion.div
          style={{
            opacity: brOpacity, y: brY, rotate: brRotate,
            right: "9%", bottom: "18%", width: "220px", position: "absolute", zIndex: 10,
          }}
        >
          <GlassCard className="p-5">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center mb-3 text-[10px] font-bold"
              style={{
                background: "rgba(143,211,196,0.08)",
                border: "1px solid rgba(143,211,196,0.14)",
                color: "#8fd3c4",
              }}
            >
              04
            </div>
            <h4 className="text-white text-sm font-semibold mb-1">Intelligence</h4>
            <p className="text-xs leading-relaxed" style={{ color: "rgba(255,255,255,0.34)" }}>
              AI agents, agentic workflows, copilots, content generation.
            </p>
          </GlassCard>
        </motion.div>

        {/* ── Floating label ─────────────────────────────── */}
        <motion.div
          style={{
            opacity: labelOpacity, y: labelY,
            position: "absolute", bottom: "48px", left: "50%",
            transform: "translateX(-50%)", zIndex: 20,
            pointerEvents: "none",
          }}
          className="flex items-center gap-2"
        >
          <div className="w-px h-6" style={{ background: "linear-gradient(to bottom, transparent, rgba(209,162,106,0.4))" }} />
          <span className="text-[11px] font-semibold tracking-[0.2em] uppercase" style={{ color: "rgba(209,162,106,0.5)" }}>
            Scroll to explore
          </span>
          <div className="w-px h-6" style={{ background: "linear-gradient(to bottom, rgba(209,162,106,0.4), transparent)" }} />
        </motion.div>

      </div>
    </section>
  );
}
