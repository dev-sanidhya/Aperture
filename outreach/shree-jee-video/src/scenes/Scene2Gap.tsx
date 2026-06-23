import React from 'react';
import {AbsoluteFill, interpolate, Sequence} from 'remotion';
import {Background, FadeUp, Chip, C, FONT, D, useSceneFade, useEntrance} from '../lib';

const WAMessage: React.FC<{text: string; delay: number; out?: boolean}> = ({text, delay, out}) => {
  const e = useEntrance(delay, {stiffness: 200});
  return (
    <div
      style={{
        opacity: e,
        transform: `translateY(${interpolate(e, [0, 1], [16, 0])}px)`,
        alignSelf: out ? 'flex-end' : 'flex-start',
        background: out ? C.whatsappOut : C.whatsappBubble,
        color: C.text,
        fontFamily: FONT,
        fontSize: 26,
        fontWeight: 500,
        padding: '14px 20px',
        borderRadius: 18,
        borderBottomLeftRadius: out ? 18 : 4,
        borderBottomRightRadius: out ? 4 : 18,
        maxWidth: '78%',
        lineHeight: 1.3,
      }}
    >
      {text}
    </div>
  );
};

export const Scene2Gap: React.FC = () => {
  const fade = useSceneFade(D.gap);
  const phoneE = useEntrance(150, {stiffness: 80});
  return (
    <AbsoluteFill style={{opacity: fade}}>
      <Background accentGlow={C.blue} />
      <AbsoluteFill style={{padding: '70px 70px', justifyContent: 'flex-start', alignItems: 'center'}}>
        {/* Part 1: the strength */}
        <FadeUp delay={0}>
          <div
            style={{
              fontFamily: FONT,
              fontWeight: 800,
              fontSize: 54,
              color: C.text,
              textAlign: 'center',
              lineHeight: 1.15,
            }}
          >
            You already supply
          </div>
        </FadeUp>
        <FadeUp delay={16} style={{marginTop: 16}}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 14,
              padding: '14px 28px',
              borderRadius: 16,
              background: '#FFFFFF',
              boxShadow: `0 16px 50px ${C.blue}40`,
            }}
          >
            <span style={{fontFamily: FONT, fontWeight: 800, fontSize: 42, color: '#0F1111'}}>amazon</span>
            <span style={{fontFamily: FONT, fontWeight: 800, fontSize: 42, color: '#FF9900'}}>basics</span>
            <span style={{fontSize: 36, marginLeft: 6}}>✓</span>
          </div>
        </FadeUp>

        {/* Part 2: the gap */}
        <Sequence from={90} layout="none">
          <FadeUp delay={0} style={{marginTop: 38, textAlign: 'center'}}>
            <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 38, color: C.muted, lineHeight: 1.3}}>
              But here's how that runs today
            </div>
          </FadeUp>
        </Sequence>

        {/* Phone with WhatsApp quote chaos */}
        <div
          style={{
            opacity: phoneE,
            transform: `translateY(${interpolate(phoneE, [0, 1], [40, 0])}px)`,
            marginTop: 30,
            width: 560,
            background: C.whatsapp,
            borderRadius: 32,
            border: `2px solid ${C.line}`,
            overflow: 'hidden',
            boxShadow: '0 30px 80px rgba(0,0,0,0.5)',
          }}
        >
          <div
            style={{
              background: '#1F2C34',
              padding: '16px 24px',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              borderBottom: `1px solid #000000`,
            }}
          >
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: '50%',
                background: C.green,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: FONT,
                fontWeight: 800,
                fontSize: 22,
                color: '#08130E',
              }}
            >
              B
            </div>
            <div>
              <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 25, color: C.text}}>New buyer</div>
              <div style={{fontFamily: FONT, fontSize: 18, color: C.green}}>online</div>
            </div>
          </div>
          <div
            style={{
              padding: '18px 20px 22px',
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
            }}
          >
            <WAMessage delay={210} text="Hi, do you do laminated pouches? Price?" />
            <WAMessage delay={250} text="sir send size + qty, will share rate" out />
            <WAMessage delay={300} text="also, any website / catalog to see?" />
            <WAMessage delay={345} text="no website, I'll WhatsApp photos 📷" out />
          </div>
        </div>

        {/* pain chips - in normal flow, below the phone */}
        <div
          style={{
            marginTop: 34,
            display: 'flex',
            gap: 14,
            flexWrap: 'wrap',
            justifyContent: 'center',
            maxWidth: 940,
          }}
        >
          <Chip delay={400} color={C.muted} icon="✕">No real website</Chip>
          <Chip delay={418} color={C.muted} icon="✕">Quotes by hand</Chip>
          <Chip delay={436} color={C.muted} icon="✕">Catalog = phone photos</Chip>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
