import React from 'react';
import {AbsoluteFill, interpolate} from 'remotion';
import {Background, ApertureMark, FadeUp, C, FONT, D, useSceneFade, useEntrance} from '../lib';

const Proof: React.FC<{value: string; label: string; delay: number}> = ({value, label, delay}) => {
  const e = useEntrance(delay, {stiffness: 150});
  return (
    <div
      style={{
        opacity: e,
        transform: `translateY(${interpolate(e, [0, 1], [20, 0])}px)`,
        textAlign: 'center',
      }}
    >
      <div style={{fontFamily: FONT, fontWeight: 800, fontSize: 44, color: C.accent}}>{value}</div>
      <div style={{fontFamily: FONT, fontSize: 21, color: C.muted, marginTop: 4}}>{label}</div>
    </div>
  );
};

export const Scene5Close: React.FC = () => {
  const fade = useSceneFade(D.close, 18);
  return (
    <AbsoluteFill style={{opacity: fade}}>
      <Background />
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', padding: 80, textAlign: 'center'}}>
        <FadeUp delay={0}>
          <ApertureMark size={42} />
        </FadeUp>

        {/* proof row */}
        <div style={{display: 'flex', gap: 64, marginTop: 48}}>
          <Proof delay={20} value="10+" label="businesses shipped" />
          <Proof delay={34} value="Web3 + AI" label="specialist firm" />
          <Proof delay={48} value="End-to-end" label="web · AI · automation" />
        </div>

        <FadeUp delay={80} style={{marginTop: 64}}>
          <div
            style={{
              fontFamily: FONT,
              fontWeight: 800,
              fontSize: 58,
              color: C.text,
              lineHeight: 1.18,
              maxWidth: 860,
            }}
          >
            Want a real, quick demo
            <br />
            built around your product?
          </div>
        </FadeUp>

        <FadeUp delay={110} style={{marginTop: 30}}>
          <div style={{fontFamily: FONT, fontWeight: 500, fontSize: 36, color: C.muted}}>
            Let's grab <span style={{color: C.accentSoft, fontWeight: 700}}>10 minutes</span>.
          </div>
        </FadeUp>

        <FadeUp delay={140} style={{marginTop: 54}}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 16,
              padding: '22px 44px',
              background: C.accent,
              borderRadius: 16,
              fontFamily: FONT,
              fontWeight: 800,
              fontSize: 34,
              color: '#1A0B03',
              boxShadow: `0 20px 60px ${C.accent}45`,
            }}
          >
            📅 Reply and pick a time
          </div>
        </FadeUp>

        <FadeUp delay={170} style={{position: 'absolute', bottom: 64, alignItems: 'center'}}>
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8}}>
            <div
              style={{
                fontFamily: FONT,
                fontWeight: 700,
                fontSize: 30,
                color: C.accent,
                letterSpacing: 0.5,
              }}
            >
              aperturecm.in
            </div>
            <div style={{fontFamily: FONT, fontSize: 23, color: C.muted}}>Sanidhya · Aperture</div>
          </div>
        </FadeUp>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
