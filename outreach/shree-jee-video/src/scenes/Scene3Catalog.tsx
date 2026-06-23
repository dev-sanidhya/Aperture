import React from 'react';
import {AbsoluteFill, interpolate} from 'remotion';
import {Background, FadeUp, C, FONT, D, useSceneFade, useEntrance} from '../lib';

const Dot: React.FC<{color: string}> = ({color}) => (
  <div style={{width: 14, height: 14, borderRadius: '50%', background: color}} />
);

const ProductCard: React.FC<{title: string; sub: string; emoji: string; delay: number}> = ({
  title,
  sub,
  emoji,
  delay,
}) => {
  const e = useEntrance(delay, {stiffness: 150});
  return (
    <div
      style={{
        opacity: e,
        transform: `translateY(${interpolate(e, [0, 1], [30, 0])}px)`,
        background: C.surface2,
        borderRadius: 18,
        border: `1px solid ${C.line}`,
        padding: 22,
        flex: 1,
      }}
    >
      <div
        style={{
          height: 110,
          borderRadius: 12,
          background: `linear-gradient(135deg, ${C.accent}33, ${C.accent}0D)`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 56,
          marginBottom: 16,
        }}
      >
        {emoji}
      </div>
      <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 26, color: C.text}}>{title}</div>
      <div style={{fontFamily: FONT, fontSize: 20, color: C.muted, marginTop: 6}}>{sub}</div>
    </div>
  );
};

export const Scene3Catalog: React.FC = () => {
  const fade = useSceneFade(D.catalog);
  const browser = useEntrance(40, {stiffness: 80});
  return (
    <AbsoluteFill style={{opacity: fade}}>
      <Background />
      <AbsoluteFill style={{padding: 70, justifyContent: 'flex-start', alignItems: 'center'}}>
        <FadeUp delay={0} style={{textAlign: 'center'}}>
          <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 30, color: C.accent, letterSpacing: 2}}>
            FIX #1
          </div>
          <div
            style={{
              fontFamily: FONT,
              fontWeight: 800,
              fontSize: 52,
              color: C.text,
              marginTop: 10,
              lineHeight: 1.15,
            }}
          >
            A site that matches your scale
          </div>
        </FadeUp>

        {/* Browser mockup */}
        <div
          style={{
            opacity: browser,
            transform: `translateY(${interpolate(browser, [0, 1], [50, 0])}px) scale(${interpolate(
              browser,
              [0, 1],
              [0.94, 1]
            )})`,
            marginTop: 44,
            width: 920,
            background: C.surface,
            borderRadius: 22,
            border: `1px solid ${C.line}`,
            overflow: 'hidden',
            boxShadow: '0 40px 90px rgba(0,0,0,0.55)',
          }}
        >
          {/* browser bar */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '18px 24px',
              background: C.bg1,
              borderBottom: `1px solid ${C.line}`,
            }}
          >
            <Dot color="#FF5F57" />
            <Dot color="#FEBC2E" />
            <Dot color="#28C840" />
            <div
              style={{
                marginLeft: 18,
                flex: 1,
                background: C.surface2,
                borderRadius: 10,
                padding: '10px 20px',
                fontFamily: FONT,
                fontSize: 22,
                color: C.muted,
              }}
            >
              🔒 shreejeepackaging.com
            </div>
          </div>

          {/* hero */}
          <div style={{padding: '40px 40px 34px'}}>
            <div style={{fontFamily: FONT, fontWeight: 800, fontSize: 44, color: C.text, lineHeight: 1.1}}>
              Flexible & Laminated
              <br />
              Packaging, Built to Spec
            </div>
            <div style={{fontFamily: FONT, fontSize: 24, color: C.muted, marginTop: 14}}>
              Printed pouches · Lamination films · Custom runs
            </div>

            {/* trust strip */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                marginTop: 22,
                padding: '12px 18px',
                background: `${C.green}14`,
                border: `1px solid ${C.green}40`,
                borderRadius: 12,
                width: 'fit-content',
                fontFamily: FONT,
                fontSize: 22,
                color: C.text,
                fontWeight: 600,
              }}
            >
              <span style={{color: C.green}}>★</span> Trusted by Amazon Basics & growing D2C brands
            </div>

            {/* product cards */}
            <div style={{display: 'flex', gap: 18, marginTop: 30}}>
              <ProductCard delay={70} emoji="📦" title="Printed Pouches" sub="4-color, food-grade" />
              <ProductCard delay={86} emoji="🎞️" title="Lamination Films" sub="BOPP · PET · matte" />
              <ProductCard delay={102} emoji="✨" title="Custom Packaging" sub="Made to your spec" />
            </div>
          </div>
        </div>

        <FadeUp delay={170} style={{marginTop: 38}}>
          <div style={{fontFamily: FONT, fontWeight: 600, fontSize: 30, color: C.accentSoft, textAlign: 'center'}}>
            Looks as serious as the brands you supply.
          </div>
        </FadeUp>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
