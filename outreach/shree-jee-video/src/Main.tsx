import React from 'react';
import {AbsoluteFill, Series} from 'remotion';
import {C, D} from './lib';
import {Scene1Open} from './scenes/Scene1Open';
import {Scene2Gap} from './scenes/Scene2Gap';
import {Scene3Catalog} from './scenes/Scene3Catalog';
import {Scene4Quote} from './scenes/Scene4Quote';
import {Scene5Close} from './scenes/Scene5Close';

export const Main: React.FC = () => {
  return (
    <AbsoluteFill style={{background: C.bg0}}>
      <Series>
        <Series.Sequence durationInFrames={D.open}>
          <Scene1Open />
        </Series.Sequence>
        <Series.Sequence durationInFrames={D.gap}>
          <Scene2Gap />
        </Series.Sequence>
        <Series.Sequence durationInFrames={D.catalog}>
          <Scene3Catalog />
        </Series.Sequence>
        <Series.Sequence durationInFrames={D.quote}>
          <Scene4Quote />
        </Series.Sequence>
        <Series.Sequence durationInFrames={D.close}>
          <Scene5Close />
        </Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};
