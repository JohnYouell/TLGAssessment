import { useEffect, useRef } from "react";
import Player from "@vimeo/player";
import { Lock, PlayCircle } from "lucide-react";

const vimeoId = (url) => (url || "").match(/vimeo\.com\/(?:video\/)?(\d+)/)?.[1];

export const VideoEmbed = ({ url, label, onEnded, locked, onUnlock, testId = "video-embed" }) => {
  const ref = useRef(null);
  const id = vimeoId(url);

  useEffect(() => {
    if (!id || !onEnded || !ref.current) {
      return undefined;
    }
    const player = new Player(ref.current);
    player.on("ended", onEnded);
    return () => player.off("ended");
  }, [id, onEnded]);

  const frame = "relative mx-auto aspect-video w-full max-w-3xl overflow-hidden rounded-sm border-2 border-gold/60 bg-surface";
  if (locked) {
    return (
      <div className={`${frame} flex flex-col items-center justify-center gap-4 text-center`} data-testid={`${testId}-locked`}>
        <Lock className="h-10 w-10 text-gold" />
        <p className="px-6 font-heading uppercase tracking-widest text-white">Video included with Full Access</p>
        <button type="button" onClick={onUnlock} className="btn-gold" data-testid={`${testId}-unlock-button`}>Unlock the Full Training Program</button>
      </div>
    );
  }
  if (!id) {
    return (
      <div className={`${frame} flex flex-col items-center justify-center gap-3 border-dashed text-center`} data-testid={`${testId}-placeholder`}>
        <PlayCircle className="h-14 w-14 text-gold/70" />
        <span className="px-6 text-xs uppercase tracking-widest text-zinc-400">[{label || "Video placeholder"}]</span>
      </div>
    );
  }
  return (
    <div className={frame} data-testid={testId}>
      <iframe ref={ref} src={`https://player.vimeo.com/video/${id}?title=0&byline=0&portrait=0`} title={label || "Video"}
        className="absolute inset-0 h-full w-full" allow="autoplay; fullscreen; picture-in-picture" allowFullScreen />
    </div>
  );
};
