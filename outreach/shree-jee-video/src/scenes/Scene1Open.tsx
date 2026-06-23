import React from 'react';
import {AbsoluteFill, interpolate} from 'remotion';
import {Background, ApertureMark, FadeUp, C, FONT, D, useSceneFade, useEntrance} from '../lib';

export const Scene1Open: React.FC = () => {
  const fade = useSceneFade(D.open);
  const line = useEntrance(40, {stiffness: 90});
  return (
    <AbsoluteFill style={{opacity: fade}}>
      <Background />
      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          padding: 90,
          textAlign: 'center',
        }}
      >
        <FadeUp delay={0}>
          <ApertureMark size={46} />
        </FadeUp>

        <div
          style={{
            width: interpolate(line, [0, 1], [0, 180]),
            height: 3,
            background: C.accent,
            borderRadius: 2,
            margin: '46px 0',
          }}
        />

        <FadeUp delay={22}>
          <div
            style={{
              fontFamily: FONT,
              fontWeight: 800,
              fontSize: 72,
              color: C.text,
              lineHeight: 1.1,
            }}
          >
            Hey Divyansh
          </div>
        </FadeUp>

        <FadeUp delay={42} style={{marginTop: 28}}>
          <div
            style={{
              fontFamily: FONT,
              fontWeight: 500,
              fontSize: 40,
              color: C.muted,
              lineHeight: 1.35,
              maxWidth: 760,
            }}
          >
            I built you a 60-second look at what
            <br />
            <span style={{color: C.text, fontWeight: 700}}>Shree Jee Packaging</span> could be online.
          </div>
        </FadeUp>

        <FadeUp delay={78} style={{marginTop: 56}}>
          <div
            style={{
              fontFamily: FONT,
              fontWeight: 600,
              fontSize: 28,
              color: C.accentSoft,
              letterSpacing: 1,
            }}
          >
            No pitch. Just ideas. ↓
          </div>
        </FadeUp>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
