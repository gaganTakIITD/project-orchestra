import { memo } from 'react';

/**
 * Static ASCII decoration pattern - memoized to prevent unnecessary re-renders
 * Displayed on desktop only, hidden on mobile to save bandwidth
 */
const AsciiPattern = memo(() => (
  <div className="text-muted-foreground font-mono text-xs leading-tight select-none" aria-hidden="true">
    <div>{"> > > > > > > >".split(" ").map((c, i) => <span key={i}>{c} </span>)}</div>
    <div className="mt-2">{"> > > > > >".split(" ").map((c, i) => <span key={i}>{c} </span>)}</div>
    <div className="mt-2">{"> > > > > > > > >".split(" ").map((c, i) => <span key={i}>{c} </span>)}</div>
    <div className="mt-4">{"> > > >".split(" ").map((c, i) => <span key={i}>{c} </span>)}</div>
    <div className="mt-2">{"> > > > > > > >".split(" ").map((c, i) => <span key={i}>{c} </span>)}</div>
  </div>
));

AsciiPattern.displayName = 'AsciiPattern';

export default AsciiPattern;
