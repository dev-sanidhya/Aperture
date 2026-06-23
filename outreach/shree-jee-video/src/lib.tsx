import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  random,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Inter';

const {fontFamily} = loadFont();

export const FPS = 30;

// Scene durations (frames @ 30fps)
export const D = {
  open: 180, // 0-6s
  gap: 480, // 6-22s
  catalog: 510, // 22-39s
  quote: 510, // 39-56s
  close: 420, // 56-70s
};
export const TOTAL_FRAMES = D.open + D.gap + D.catalog + D.quote + D.close; // 2100 = 70s

export const C = {
  bg0: '#070A12',
  bg1: '#0C1120',
  surface: '#141B2E',
  surface2: '#1B2540',
  line: '#26304A',
  text: '#FFFFFF',
  muted: '#93A1BC',
  accent: '#FF7A3D', // warm packaging orange
  accentSoft: '#FFB082',
  green: '#3DDC84',
  blue: '#5B8DEF',
  whatsapp: '#1F2C34',
  whatsappBubble: '#2A3942',
  whatsappOut: '#005C4B',
};

export const FONT = fontFamily;

// Easing-friendly entrance: returns 0..1 progress with spring
export const useEntrance = (delay = 0, config?: Partial<{damping: number; mass: number; stiffness: number}>) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({
    frame: frame - delay,
    fps,
    config: {damping: 200, mass: 0.8, stiffness: 120, ...config},
  });
};

export const FadeUp: React.FC<{
  delay?: number;
  y?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({delay = 0, y = 28, children, style}) => {
  const e = useEntrance(delay);
  return (
    <div
      style={{
        opacity: e,
        transform: `translateY(${interpolate(e, [0, 1], [y, 0])}px)`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

// Fade an element out near the end of its scene for clean transitions
export const useSceneFade = (sceneDuration: number, fadeFrames = 14) => {
  const frame = useCurrentFrame();
  const inFade = interpolate(frame, [0, fadeFrames], [0, 1], {extrapolateRight: 'clamp'});
  const outFade = interpolate(
    frame,
    [sceneDuration - fadeFrames, sceneDuration],
    [1, 0],
    {extrapolateLeft: 'clamp'}
  );
  return Math.min(inFade, outFade);
};

export const Background: React.FC<{accentGlow?: string}> = ({accentGlow = C.accent}) => {
  const frame = useCurrentFrame();
  const drift = Math.sin(frame / 90) * 30;
  return (
    <AbsoluteFill>
      <AbsoluteFill
        style={{
          background: `radial-gradient(120% 90% at 50% -10%, ${C.bg1} 0%, ${C.bg0} 60%)`,
        }}
      />
      {/* soft accent glow */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(40% 30% at ${50 + drift / 8}% 18%, ${accentGlow}22 0%, transparent 70%)`,
        }}
      />
      {/* subtle grid */}
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(${C.line}1A 1px, transparent 1px), linear-gradient(90deg, ${C.line}1A 1px, transparent 1px)`,
          backgroundSize: '60px 60px',
          maskImage: 'radial-gradient(80% 80% at 50% 40%, black 30%, transparent 85%)',
          WebkitMaskImage: 'radial-gradient(80% 80% at 50% 40%, black 30%, transparent 85%)',
          transform: `translateY(${drift}px)`,
        }}
      />
      {/* floating dots */}
      {new Array(14).fill(0).map((_, i) => {
        const x = random(`x${i}`) * 1080;
        const baseY = random(`y${i}`) * 1080;
        const y = (baseY + frame * (0.3 + random(`s${i}`) * 0.5)) % 1080;
        const size = 2 + random(`r${i}`) * 4;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: size,
              height: size,
              borderRadius: '50%',
              background: i % 3 === 0 ? accentGlow : C.muted,
              opacity: 0.18,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

export const ApertureMark: React.FC<{size?: number; style?: React.CSSProperties}> = ({
  size = 34,
  style,
}) => {
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: size * 0.34, ...style}}>
      <svg width={size} height={size} viewBox="0 0 100 100" fill="none">
        <circle cx="50" cy="50" r="44" stroke={C.accent} strokeWidth="7" />
        <circle cx="50" cy="50" r="14" fill={C.accent} />
        <path d="M50 6 L50 28" stroke={C.accent} strokeWidth="7" strokeLinecap="round" />
        <path d="M50 72 L50 94" stroke={C.accent} strokeWidth="7" strokeLinecap="round" />
      </svg>
      <span
        style={{
          fontFamily: FONT,
          fontWeight: 700,
          fontSize: size * 0.82,
          color: C.text,
          letterSpacing: size * 0.02,
        }}
      >
        Aperture
      </span>
    </div>
  );
};

export const Chip: React.FC<{
  children: React.ReactNode;
  color?: string;
  delay?: number;
  icon?: string;
}> = ({children, color = C.accent, delay = 0, icon}) => {
  const e = useEntrance(delay, {stiffness: 160});
  return (
    <div
      style={{
        opacity: e,
        transform: `scale(${interpolate(e, [0, 1], [0.85, 1])})`,
        display: 'inline-flex',
        alignItems: 'center',
        gap: 12,
        padding: '14px 24px',
        borderRadius: 999,
        background: `${color}1A`,
        border: `1.5px solid ${color}55`,
        color: C.text,
        fontFamily: FONT,
        fontWeight: 600,
        fontSize: 30,
      }}
    >
      {icon ? <span style={{fontSize: 30}}>{icon}</span> : null}
      {children}
    </div>
  );
};
