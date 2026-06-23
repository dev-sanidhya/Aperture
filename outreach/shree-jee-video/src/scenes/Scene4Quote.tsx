import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, Sequence} from 'remotion';
import {Background, FadeUp, C, FONT, D, useSceneFade, useEntrance} from '../lib';

const Field: React.FC<{label: string; value: string; delay: number}> = ({label, value, delay}) => {
  const e = useEntrance(delay, {stiffness: 160});
  return (
    <div style={{opacity: e, transform: `translateX(${interpolate(e, [0, 1], [-20, 0])}px)`}}>
      <div style={{fontFamily: FONT, fontSize: 20, color: C.muted, marginBottom: 8}}>{label}</div>
      <div
        style={{
          background: C.surface2,
          border: `1px solid ${C.line}`,
          borderRadius: 12,
          padding: '16px 20px',
          fontFamily: FONT,
          fontSize: 26,
          fontWeight: 600,
          color: C.text,
        }}
      >
        {value}
      </div>
    </div>
  );
};

export const Scene4Quote: React.FC = () => {
  const fade = useSceneFade(D.quote);
  const frame = useCurrentFrame();
  const panel = useEntrance(40, {stiffness: 80});

  // button press pulse around frame 200
  const press = interpolate(frame, [195, 205, 215], [1, 0.94, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{opacity: fade}}>
      <Background />
      <AbsoluteFill style={{padding: 70, justifyContent: 'flex-start', alignItems: 'center'}}>
        <FadeUp delay={0} style={{textAlign: 'center'}}>
          <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 30, color: C.accent, letterSpacing: 2}}>
            FIX #2
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
            Instant quotes, zero manual work
          </div>
        </FadeUp>

        {/* tool panel */}
        <div
          style={{
            opacity: panel,
            transform: `translateY(${interpolate(panel, [0, 1], [50, 0])}px)`,
            marginTop: 44,
            width: 880,
            background: C.surface,
            borderRadius: 22,
            border: `1px solid ${C.line}`,
            padding: 38,
            boxShadow: '0 40px 90px rgba(0,0,0,0.55)',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 12, marginBottom: 26}}>
            <div style={{fontSize: 30}}>⚡</div>
            <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 30, color: C.text}}>
              Get a Quote
            </div>
            <div
              style={{
                marginLeft: 'auto',
                fontFamily: FONT,
                fontSize: 19,
                color: C.green,
                background: `${C.green}1A`,
                padding: '6px 14px',
                borderRadius: 999,
                fontWeight: 600,
              }}
            >
              AI-powered
            </div>
          </div>

          <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 22}}>
            <Field label="Product" value="Laminated pouch" delay={70} />
            <Field label="Material" value="BOPP · matte" delay={86} />
            <Field label="Size" value='8" × 11"' delay={102} />
            <Field label="Print" value="4-color" delay={118} />
            <Field label="Quantity" value="50,000 units" delay={134} />
            <Field label="Delivery" value="Pan-India" delay={150} />
          </div>

          {/* button */}
          <div
            style={{
              transform: `scale(${press})`,
              marginTop: 30,
              background: C.accent,
              borderRadius: 14,
              padding: '20px 0',
              textAlign: 'center',
              fontFamily: FONT,
              fontWeight: 800,
              fontSize: 30,
              color: '#1A0B03',
            }}
          >
            Generate Quote →
          </div>
        </div>

        {/* result card slides in after button press */}
        <Sequence from={215}>
          <ResultCard />
        </Sequence>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const ResultCard: React.FC = () => {
  const e = useEntrance(0, {stiffness: 120});
  const frame = useCurrentFrame();
  const toInbox = useEntrance(120, {stiffness: 110});
  return (
    <div
      style={{
        position: 'absolute',
        bottom: 64,
        left: '50%',
        transform: `translateX(-50%) translateY(${interpolate(e, [0, 1], [40, 0])}px)`,
        opacity: e,
        width: 820,
        background: `linear-gradient(135deg, ${C.surface2}, ${C.surface})`,
        border: `1.5px solid ${C.green}55`,
        borderRadius: 20,
        padding: 30,
        display: 'flex',
        alignItems: 'center',
        gap: 28,
        boxShadow: `0 30px 70px ${C.green}25`,
      }}
    >
      <div style={{flex: 1}}>
        <div style={{fontFamily: FONT, fontSize: 22, color: C.muted}}>Estimated quote</div>
        <div style={{fontFamily: FONT, fontWeight: 800, fontSize: 50, color: C.text, marginTop: 4}}>
          ₹2.40 <span style={{fontSize: 28, color: C.muted}}>/ unit</span>
        </div>
        <div style={{fontFamily: FONT, fontSize: 22, color: C.green, marginTop: 8, fontWeight: 600}}>
          Generated in 3 seconds · no staff time
        </div>
      </div>
      <div
        style={{
          opacity: toInbox,
          transform: `scale(${interpolate(toInbox, [0, 1], [0.8, 1])})`,
          textAlign: 'center',
          padding: '18px 24px',
          background: `${C.blue}1A`,
          border: `1px solid ${C.blue}55`,
          borderRadius: 14,
        }}
      >
        <div style={{fontSize: 34}}>📥</div>
        <div style={{fontFamily: FONT, fontSize: 20, color: C.text, marginTop: 6, fontWeight: 600}}>
          Lands with
          <br />
          your team
        </div>
      </div>
    </div>
  );
};
