import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, Sequence} from 'remotion';
import {Background, FadeUp, Chip, C, FONT, D, useSceneFade, useEntrance} from '../lib';

const WAMessage: React.FC<{text: string; delay: number; out?: boolean}> = ({text, delay, out}) => {
  const e = useEntrance(delay, {stiffness: 170});
  return (
    <div
      style={{
        opacity: e,
        transform: `translateY(${interpolate(e, [0, 1], [16, 0])}px)`,
        alignSelf: out ? 'flex-end' : 'flex-start',
        background: out ? C.whatsappOut : C.whatsappBubble,
        color: C.text,
        fontFamily: FONT,
        fontSize: 27,
        fontWeight: 500,
        padding: '16px 22px',
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
  const frame = useCurrentFrame();
  const phoneE = useEntrance(150, {stiffness: 80});
  return (
    <AbsoluteFill style={{opacity: fade}}>
      <Background accentGlow={C.blue} />
      <AbsoluteFill style={{padding: 80, justifyContent: 'flex-start', alignItems: 'center'}}>
        {/* Part 1: the strength */}
        <FadeUp delay={0} style={{marginTop: 20}}>
          <div
            style={{
              fontFamily: FONT,
              fontWeight: 800,
              fontSize: 56,
              color: C.text,
              textAlign: 'center',
              lineHeight: 1.15,
            }}
          >
            You already supply
          </div>
        </FadeUp>
        <FadeUp delay={16} style={{marginTop: 18}}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 14,
              padding: '16px 30px',
              borderRadius: 16,
              background: '#FFFFFF',
              boxShadow: `0 16px 50px ${C.blue}40`,
            }}
          >
            <span style={{fontFamily: FONT, fontWeight: 800, fontSize: 44, color: '#0F1111'}}>
              amazon
            </span>
            <span style={{fontFamily: FONT, fontWeight: 800, fontSize: 44, color: '#FF9900'}}>
              basics
            </span>
            <span style={{fontSize: 38, marginLeft: 6}}>✓</span>
          </div>
        </FadeUp>

        {/* Part 2: the gap */}
        <Sequence from={90}>
          <FadeUp delay={0} style={{marginTop: 46, textAlign: 'center'}}>
            <div
              style={{
                fontFamily: FONT,
                fontWeight: 700,
                fontSize: 40,
                color: C.muted,
                lineHeight: 1.3,
              }}
            >
              But here's how that operation runs today
            </div>
          </FadeUp>
        </Sequence>

        {/* Phone with WhatsApp quote chaos */}
        <div
          style={{
            opacity: phoneE,
            transform: `translateY(${interpolate(phoneE, [0, 1], [40, 0])}px)`,
            marginTop: 40,
            width: 560,
            background: C.whatsapp,
            borderRadius: 36,
            border: `2px solid ${C.line}`,
            overflow: 'hidden',
            boxShadow: '0 30px 80px rgba(0,0,0,0.5)',
          }}
        >
          <div
            style={{
              background: '#1F2C34',
              padding: '20px 26px',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              borderBottom: `1px solid #000000`,
            }}
          >
            <div
              style={{
                width: 46,
                height: 46,
                borderRadius: '50%',
                background: C.green,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: FONT,
                fontWeight: 800,
                fontSize: 24,
                color: '#08130E',
              }}
            >
              R
            </div>
            <div>
              <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 26, color: C.text}}>
                New buyer
              </div>
              <div style={{fontFamily: FONT, fontSize: 19, color: C.green}}>online</div>
            </div>
          </div>
          <div
            style={{
              padding: '22px 22px 26px',
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
              minHeight: 360,
            }}
          >
            <WAMessage delay={210} text="Hi, do you do laminated pouches? Price?" />
            <WAMessage delay={250} text="sir send size + qty, will share rate" out />
            <WAMessage delay={300} text="also do you have a website / catalog?" />
            <WAMessage delay={345} text="no website, I'll WhatsApp photos 📷" out />
          </div>
        </div>

        {/* pain chips */}
        <div
          style={{
            position: 'absolute',
            bottom: 70,
            display: 'flex',
            gap: 16,
            flexWrap: 'wrap',
            justifyContent: 'center',
            maxWidth: 920,
          }}
        >
          <Chip delay={400} color={C.muted} icon="✕">No real website</Chip>
          <Chip delay={420} color={C.muted} icon="✕">Quotes by hand</Chip>
          <Chip delay={440} color={C.muted} icon="✕">Catalog = phone photos</Chip>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
