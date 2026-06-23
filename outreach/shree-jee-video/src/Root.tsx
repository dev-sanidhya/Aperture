import {Composition} from 'remotion';
import {Main} from './Main';
import {TOTAL_FRAMES, FPS} from './lib';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={Main}
      durationInFrames={TOTAL_FRAMES}
      fps={FPS}
      width={1080}
      height={1080}
    />
  );
};
