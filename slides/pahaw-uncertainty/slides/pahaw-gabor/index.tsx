import type { ReactNode } from 'react';
import type { DesignSystem, Page, SlideMeta, SlideTransition } from '@open-slide/core';
import { useSlidePageNumber } from '@open-slide/core';

import effHc from './assets/spiral_effort_hc_hi.png';
import effPd from './assets/spiral_effort_pd_hi.png';
import velHc from './assets/spiral_velocity_hc_hi.png';
import velPd from './assets/spiral_velocity_pd_hi.png';
import rgbHc from './assets/spiral_rgb_vpe_hc_hi.png';
import rgbPd from './assets/spiral_rgb_vpe_pd_hi.png';

// ─── Academic tokens ──────────────────────────────────────────────────────────
export const design: DesignSystem = {
  palette: { bg: '#fbfaf7', text: '#161616', accent: '#1f4e9b' },
  fonts: { display: 'Georgia, "Times New Roman", serif', body: '"Inter", "SF Pro Text", system-ui, sans-serif' },
  typeScale: { hero: 96, body: 27 },
  radius: 6,
};
const INK = '#161616', TXT = '#242428', MUTED = '#6f747c';
const BLUE = '#1f4e9b', GREEN = '#2e7d32', ORANGE = '#c9791f', RED = '#b3261e', PAPER = '#fbfaf7';
const RULE = '#1a1a1a', HAIR = '#e4e1da';
const SERIF = 'Georgia, "Times New Roman", serif';
const MONO = 'ui-monospace, "SF Mono", Menlo, monospace';
const num = { fontFamily: MONO, fontVariantNumeric: 'tabular-nums' as const };
const fill = { width: '100%', height: '100%', fontFamily: 'var(--osd-font-body)', boxSizing: 'border-box' } as const;

// ─── Chrome ────────────────────────────────────────────────────────────────────
const Foot = () => {
  const { current, total } = useSlidePageNumber();
  return (
    <div style={{ position: 'absolute', left: 96, right: 96, bottom: 38, display: 'flex', justifyContent: 'space-between', fontSize: 17, color: MUTED, ...num }}>
      <span>Porcelli · 99% Sure? Gabor Begs to Differ</span>
      <span>{String(current).padStart(2, '0')} / {String(total).padStart(2, '0')}</span>
    </div>
  );
};
const Cite = ({ children }: { children: ReactNode }) => <sup style={{ color: BLUE, fontSize: '0.62em', fontWeight: 600, ...num }}>[{children}]</sup>;
const K = ({ children, c = INK }: { children: ReactNode; c?: string }) => <span style={{ ...num, color: c, fontWeight: 600 }}>{children}</span>;

const Frame = ({ kicker, title, children }: { kicker?: string; title: ReactNode; children: ReactNode }) => (
  <div style={{ ...fill, background: PAPER, color: INK, position: 'relative', display: 'flex', flexDirection: 'column', padding: '58px 96px 84px' }}>
    {kicker && <div style={{ fontSize: 18, letterSpacing: '0.2em', color: BLUE, ...num, textTransform: 'uppercase', fontWeight: 600 }}>{kicker}</div>}
    <h2 style={{ fontFamily: SERIF, fontSize: 40, fontWeight: 700, margin: '8px 0 0', lineHeight: 1.12, letterSpacing: '-0.01em' }}>{title}</h2>
    <div style={{ height: 3, background: RULE, width: '100%', margin: '18px 0 0' }} />
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', width: '100%' }}>{children}</div>
    <Foot />
  </div>
);
const P = ({ children, size = 27, mt = 0 }: { children: ReactNode; size?: number; mt?: number }) => (
  <p style={{ fontSize: size, lineHeight: 1.5, color: TXT, margin: `${mt}px 0 0`, textAlign: 'justify', maxWidth: 1560 }}>{children}</p>
);
const Eq = ({ children }: { children: ReactNode }) => (
  <div style={{ textAlign: 'center', fontFamily: MONO, fontSize: 30, color: INK, margin: '26px 0', letterSpacing: '0.01em' }}>{children}</div>
);

// ═══ 01 — Title ══════════════════════════════════════════════════════════════════
const Title: Page = () => (
  <div style={{ ...fill, background: PAPER, color: INK, position: 'relative', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '0 130px' }}>
    <div style={{ fontSize: 19, letterSpacing: '0.22em', color: BLUE, ...num, textTransform: 'uppercase', fontWeight: 600 }}>Time-frequency analysis · PaHaW benchmark</div>
    <h1 style={{ fontFamily: SERIF, fontSize: 82, fontWeight: 700, margin: '26px 0 0', lineHeight: 1.06, maxWidth: 1520 }}>
      99% Sure? <span style={{ color: BLUE }}>Gabor</span> Begs to Differ
    </h1>
    <p style={{ fontFamily: SERIF, fontSize: 34, fontStyle: 'italic', color: TXT, margin: '22px 0 0', maxWidth: 1420, lineHeight: 1.35 }}>
      A time-frequency look at Parkinson's handwriting and a structure-preserving image encoding
    </p>
    <div style={{ height: 3, background: RULE, width: 560, margin: '42px 0 26px' }} />
    <div style={{ fontSize: 26, ...num, color: INK }}>Andrea Porcelli</div>
    <div style={{ fontSize: 22, ...num, color: MUTED, marginTop: 8 }}>Department of Computer Science · University of Bari Aldo Moro</div>
    <Foot />
  </div>
);

// ═══ 02 — Clinical motivation ════════════════════════════════════════════════════
const Motivation: Page = () => {
  // two velocity traces: healthy (smooth) vs PD (tremor + arrests)
  const W = 1180;
  const healthy = () => { let d = 'M40 70 '; for (let x = 40; x <= W; x += 4) { const t = (x - 40) / 60; d += 'L' + x + ' ' + (70 + Math.sin(t) * 8).toFixed(1) + ' '; } return d; };
  const AR = [[430, 486], [760, 806]];
  const pd = () => { let d = 'M40 70 '; for (let x = 40; x <= W; x += 3) { const inA = AR.some((a) => x >= a[0] && x <= a[1]); const tr = inA ? 0 : Math.sin((x - 40) * 0.16) * 30 * (0.6 + 0.4 * Math.sin((x - 40) * 0.02)); d += 'L' + x + ' ' + (inA ? 70 : 70 + tr).toFixed(1) + ' '; } return d; };
  return (
    <Frame kicker="The problem" title="Handwriting is a window into the Parkinsonian brain">
      <P mt={2}>
        A graphics tablet records the pen while a patient draws. The trace carries the motor signature of the disease:
        a <K c={BLUE}>4–6 Hz tremor</K>, slower and more variable velocity, and brief akinetic <K c={ORANGE}>arrests</K> —
        a cheap, non-invasive biomarker.
      </P>
      <svg viewBox="0 0 1200 320" style={{ width: '100%', maxWidth: 1420, alignSelf: 'center', marginTop: 20 }}>
        <text x={40} y={30} fontFamily={SERIF} fontSize={22} fontWeight={700} fill={GREEN}>Healthy control</text>
        <g transform="translate(0,10)"><path d={healthy()} fill="none" stroke={GREEN} strokeWidth={2.6} /></g>
        <line x1={40} y1={170} x2={W} y2={170} stroke={HAIR} strokeWidth={1.5} />
        <text x={40} y={210} fontFamily={SERIF} fontSize={22} fontWeight={700} fill={ORANGE}>Parkinson's disease</text>
        <g transform="translate(0,150)">
          {AR.map((a, i) => <rect key={i} x={a[0]} y={35} width={a[1] - a[0]} height={70} fill={ORANGE} opacity={0.12} />)}
          <path d={pd()} fill="none" stroke={ORANGE} strokeWidth={2.6} />
          {AR.map((a, i) => <text key={i} x={(a[0] + a[1]) / 2} y={128} textAnchor="middle" fontFamily={MONO} fontSize={16} fill={ORANGE}>arrest</text>)}
        </g>
        <text x={W} y={300} textAnchor="end" fontFamily={MONO} fontSize={17} fill={MUTED}>pen velocity · time →</text>
      </svg>
    </Frame>
  );
};

// ═══ 03 — The paradox ════════════════════════════════════════════════════════════
const Paradox: Page = () => (
  <Frame kicker="The problem" title="Reported accuracy on PaHaW is near-perfect. Is it real?">
    <P mt={2}>
      PaHaW<Cite>1</Cite> is the standard public benchmark: <K>72</K> subjects (<K>37</K> PD, <K>35</K> HC) on a Wacom
      tablet. Reported accuracies routinely exceed <K>90%</K> — and sometimes reach <K>100%</K>.
    </P>
    <div style={{ display: 'flex', alignItems: 'stretch', gap: 40, marginTop: 40, alignSelf: 'center' }}>
      <div style={{ textAlign: 'center', padding: '30px 48px', border: `2px solid ${RED}`, borderRadius: 10, background: '#fbe9e7' }}>
        <div style={{ fontSize: 20, color: RED, ...num, textTransform: 'uppercase', letterSpacing: '0.1em' }}>Headline literature</div>
        <div style={{ fontFamily: SERIF, fontSize: 108, fontWeight: 700, color: RED, lineHeight: 1 }}>0.99</div>
        <div style={{ fontSize: 22, color: MUTED, marginTop: 6 }}>single splits · no variance</div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', fontFamily: SERIF, fontSize: 60, color: MUTED }}>→</div>
      <div style={{ textAlign: 'center', padding: '30px 48px', border: `2px solid ${GREEN}`, borderRadius: 10, background: '#e3f5e9' }}>
        <div style={{ fontSize: 20, color: GREEN, ...num, textTransform: 'uppercase', letterSpacing: '0.1em' }}>Careful evaluation</div>
        <div style={{ fontFamily: SERIF, fontSize: 108, fontWeight: 700, color: GREEN, lineHeight: 1 }}>0.75</div>
        <div style={{ fontSize: 22, color: MUTED, marginTop: 6 }}>nested CV · corrected test</div>
      </div>
    </div>
    <P mt={36} size={25}>We ask two questions — <b>statistical</b>: how much survives an honest protocol? and <b>physical</b>: is the signal even resolvable?</P>
  </Frame>
);

// ═══ 04 — Table 1: literature ════════════════════════════════════════════════════
const TabLit: Page = () => {
  const GT = '2.0fr 1.45fr 0.6fr 0.6fr 0.4fr 0.4fr 0.4fr 0.4fr';
  const Yes = () => <span style={{ color: GREEN, fontWeight: 700 }}>✓</span>;
  const No = () => <span style={{ color: RED, fontWeight: 700 }}>✗</span>;
  const Mb = () => <span style={{ color: MUTED }}>∼</span>;
  const Row = ({ m, v, a, f, n1, n2, n3, n4, hi }: any) => (
    <div style={{ display: 'grid', gridTemplateColumns: GT, alignItems: 'center', fontSize: 24, padding: '11px 6px', background: hi ? '#eaf1fc' : 'transparent', borderRadius: hi ? 6 : 0 }}>
      <span>{m}</span><span style={{ color: MUTED, fontSize: 21 }}>{v}</span>
      <span style={{ textAlign: 'right', ...num }}>{a}</span><span style={{ textAlign: 'right', ...num }}>{f}</span>
      <span style={{ textAlign: 'center' }}>{n1}</span><span style={{ textAlign: 'center' }}>{n2}</span><span style={{ textAlign: 'center' }}>{n3}</span><span style={{ textAlign: 'center' }}>{n4}</span>
    </div>
  );
  return (
    <Frame kicker="Related work" title="The literature nests rarely and reports no variance">
      <div style={{ fontSize: 21, color: MUTED, fontStyle: 'italic', fontFamily: SERIF, marginBottom: 14 }}>
        Table 1. Representative results on PaHaW. Audit: nested selection (Nest), freedom from feature-selection bias (FS), subject-disjoint splits (Subj), reported variability (Var).
      </div>
      <div style={{ borderTop: `2.5px solid ${RULE}` }} />
      <div style={{ display: 'grid', gridTemplateColumns: GT, fontSize: 20, color: MUTED, padding: '10px 6px' }}>
        <span>Method</span><span>Validation</span><span style={{ textAlign: 'right' }}>Acc</span><span style={{ textAlign: 'right' }}>F1</span>
        <span style={{ textAlign: 'center' }}>Nest</span><span style={{ textAlign: 'center' }}>FS</span><span style={{ textAlign: 'center' }}>Subj</span><span style={{ textAlign: 'center' }}>Var</span>
      </div>
      <div style={{ borderTop: `1.5px solid ${RULE}` }} />
      <Row m={<>Drotár et al. 2016<Cite>1</Cite></>} v="10-fold (tasks 2–8)" a="0.813" f="0.840" n1={<No />} n2={<No />} n3={<Yes />} n4={<No />} />
      <Row m={<>Impedovo 2019<Cite>2</Cite></>} v="10-fold" a="0.984" f="n/r" n1={<No />} n2={<No />} n3={<Yes />} n4={<No />} />
      <Row m={<>Diaz et al. 2021<Cite>3</Cite></>} v="10-fold" a="0.938" f="n/r" n1={<No />} n2={<No />} n3={<Yes />} n4={<No />} />
      <Row m={<>Wang et al. 2024<Cite>4</Cite></>} v="5-fold (augmented)" a="0.847" f="0.857" n1={<No />} n2={<No />} n3={<Mb />} n4={<No />} />
      <Row m={<>Kumar &amp; Ghosh 2024<Cite>5</Cite></>} v="3:1 hold-out" a="1.000" f="n/r" n1={<No />} n2={<No />} n3={<Mb />} n4={<No />} />
      <Row m={<>Shin et al. 2025<Cite>6</Cite></>} v="LOOCV (task-level)" a="0.986" f="0.986" n1={<No />} n2={<No />} n3={<No />} n4={<No />} />
      <Row m={<>Valla et al. 2022 — non-nested<Cite>7</Cite></>} v="10-fold" a="0.849" f="0.849" n1={<No />} n2={<No />} n3={<Yes />} n4={<No />} />
      <Row m={<>Valla et al. 2022 — nested<Cite>7</Cite></>} v="nested 10-fold" a="0.737" f="0.730" n1={<Yes />} n2={<Yes />} n3={<Yes />} n4={<No />} />
      <div style={{ borderTop: `1px solid ${HAIR}` }} />
      <Row m={<b>Ours — effort · ViT · RF</b>} v="nested 3×10-fold" a="0.752" f="0.746" n1={<Yes />} n2={<Yes />} n3={<Yes />} n4={<Yes />} hi />
      <div style={{ borderTop: `2.5px solid ${RULE}` }} />
      <div style={{ fontSize: 20, color: MUTED, marginTop: 12 }}>The two studies that <b>nest</b> their selection (Valla-nested and ours) both land near <K c={GREEN}>0.74</K>; the headlines cluster near <K c={RED}>0.99</K>.</div>
    </Frame>
  );
};

// ═══ 05 — Evaluation pitfalls ════════════════════════════════════════════════════
const Pitfalls: Page = () => {
  const Item = ({ n, t, children }: { n: number; t: string; children: ReactNode }) => (
    <div style={{ display: 'flex', gap: 20, marginBottom: 22, alignItems: 'baseline' }}>
      <span style={{ fontFamily: SERIF, fontSize: 34, fontWeight: 700, color: BLUE, minWidth: 40 }}>{n}</span>
      <div>
        <span style={{ fontFamily: SERIF, fontSize: 27, fontWeight: 700, color: INK }}>{t}. </span>
        <span style={{ fontSize: 25, lineHeight: 1.42, color: TXT }}>{children}</span>
      </div>
    </div>
  );
  return (
    <Frame kicker="Related work" title="Four practices inflate PaHaW scores">
      <Item n={1} t="Subject leakage">A writer's other tasks stay in training — Shin et al.<Cite>6</Cite> report <K c={RED}>99.98%</K> under leave-one-recording-out. Group-aware splitting is the fix<Cite>9</Cite>.</Item>
      <Item n={2} t="Feature-selection bias">Choosing features on the full set before splitting: Valla et al.<Cite>7</Cite> measure <K c={RED}>84.9%</K> non-nested vs. <K c={GREEN}>73.7%</K> nested — an <K>11-point</K> gap.</Item>
      <Item n={3} t="Feature explosion">Shin et al.<Cite>6</Cite> derive <K c={RED}>944</K> features for <K>~75</K> subjects; enough degrees of freedom to fit the cohort almost perfectly.</Item>
      <Item n={4} t="No uncertainty, no valid test">None report a standard deviation; our fold-to-fold F1 std reaches <K c={RED}>0.21</K>, and naive paired <i>t</i>-tests across correlated folds are anti-conservative.</Item>
    </Frame>
  );
};

// ═══ 06 — The signal ═════════════════════════════════════════════════════════════
const Signal: Page = () => {
  const A1 = [430, 490], A2 = [770, 815];
  const trace = () => { let d = 'M60 90 '; for (let x = 60; x <= 1180; x += 3) { const inA = (x >= A1[0] && x <= A1[1]) || (x >= A2[0] && x <= A2[1]); const tr = inA ? 0 : Math.sin((x - 60) * 0.14) * 34 * (0.6 + 0.4 * Math.sin((x - 60) * 0.02)); d += 'L' + x + ' ' + (inA ? 124 : 90 + tr).toFixed(1) + ' '; } return d; };
  return (
    <Frame kicker="A time-frequency limit" title="The signal: two events at incommensurate scales">
      <P mt={2}>
        The PD signature superimposes a <K c={BLUE}>4–6 Hz tremor</K> — a <i>narrow-band</i> event best localized in
        frequency — with aperiodic akinetic <K c={ORANGE}>arrests of tens of ms</K> — <i>broadband</i> events best
        localized in time. On a few-second spiral at <K>f<sub>s</sub> = 150 Hz</K> the tremor gives only a handful of cycles.
      </P>
      <svg viewBox="0 0 1200 210" style={{ width: '100%', maxWidth: 1400, marginTop: 20, alignSelf: 'center' }}>
        <rect x={210} y={40} width={140} height={100} fill={BLUE} opacity={0.07} />
        <text x={280} y={28} textAnchor="middle" fontFamily={MONO} fontSize={19} fill={BLUE}>4–6 Hz tremor</text>
        {[A1, A2].map((a, i) => (<g key={i}><rect x={a[0]} y={104} width={a[1] - a[0]} height={40} fill={ORANGE} opacity={0.14} /><line x1={(a[0] + a[1]) / 2} y1={30} x2={(a[0] + a[1]) / 2} y2={150} stroke={ORANGE} strokeWidth={2} strokeDasharray="5 5" /><text x={(a[0] + a[1]) / 2} y={22} textAnchor="middle" fontFamily={MONO} fontSize={18} fill={ORANGE}>arrest</text></g>))}
        <path d={trace()} fill="none" stroke={BLUE} strokeWidth={2.6} />
        <text x={1180} y={196} textAnchor="end" fontFamily={MONO} fontSize={18} fill={MUTED}>pen velocity · time →</text>
      </svg>
    </Frame>
  );
};

// ═══ 07 — STFT window dilemma ════════════════════════════════════════════════════
const STFT: Page = () => (
  <Frame kicker="A time-frequency limit" title="The window dilemma (short-time Fourier transform)">
    <P mt={2}>The STFT reads <K>x[n]</K> through a window <K>w</K> of length <K>L</K> that fixes the time <i>and</i> frequency resolutions <i>at once</i>, with product <K>Δt·Δf ≈ 1</K> constant:</P>
    <Eq>X[m,k] = Σ<sub>n</sub> x[n] · w[n − mH] · e<sup>−j2πkn/L</sup>&nbsp;&nbsp;&nbsp; Δt ≈ L/f<sub>s</sub>,&nbsp; Δf ≈ f<sub>s</sub>/L</Eq>
    <div style={{ display: 'flex', gap: 40, justifyContent: 'center', margin: '10px 0 18px' }}>
      <div style={{ textAlign: 'center', padding: '14px 30px', border: `1.5px solid ${BLUE}`, borderRadius: 8 }}>
        <div style={{ fontFamily: SERIF, fontSize: 24, fontWeight: 700, color: BLUE }}>Long window</div>
        <div style={{ fontSize: 21, color: TXT }}>resolves the tremor · smears the arrests</div>
      </div>
      <div style={{ textAlign: 'center', padding: '14px 30px', border: `1.5px solid ${ORANGE}`, borderRadius: 8 }}>
        <div style={{ fontFamily: SERIF, fontSize: 24, fontWeight: 700, color: ORANGE }}>Short window</div>
        <div style={{ fontSize: 21, color: TXT }}>times the arrests · blurs the tremor</div>
      </div>
    </div>
    <P>Resolving <K>4</K> from <K>6 Hz</K> needs <K c={BLUE}>Δf ≤ 2 Hz</K>, hence <K c={BLUE}>L ≥ 150/2 = 75 samples ≈ 0.5 s</K> — over which any sub-decisecond arrest is washed out. <b>No single L serves both.</b></P>
  </Frame>
);

// ═══ 08 — Wavelet + tiling ═══════════════════════════════════════════════════════
const Wavelet: Page = () => {
  const pw = 360, ph = 300, pyT = 66, lx = 40, rx = 470;
  const stft = []; for (let r = 0; r < 5; r++) for (let c = 0; c < 6; c++) stft.push(<rect key={r + '-' + c} x={lx + c * pw / 6} y={pyT + r * ph / 5} width={pw / 6} height={ph / 5} fill={BLUE} fillOpacity={0.09} stroke={BLUE} strokeWidth={1.5} strokeOpacity={0.7} />);
  const bands = [{ c: 8, f: 8 }, { c: 4, f: 4 }, { c: 2, f: 2 }, { c: 1, f: 1 }]; const wav = []; let yy = pyT;
  for (let b = 0; b < bands.length; b++) { const h = ph * bands[b].f / 15, cw = pw / bands[b].c; for (let c = 0; c < bands[b].c; c++) wav.push(<rect key={b + '-' + c} x={rx + c * cw} y={yy} width={cw} height={h} fill={ORANGE} fillOpacity={0.11} stroke={ORANGE} strokeWidth={1.5} strokeOpacity={0.75} />); yy += h; }
  return (
    <Frame kicker="A time-frequency limit" title="The wavelet dilemma (continuous wavelet transform)">
      <div style={{ display: 'flex', gap: 40, alignItems: 'center' }}>
        <div style={{ flex: '0 0 680px' }}>
          <P size={26}>The CWT swaps the fixed window for dilations of a mother wavelet <K>ψ</K>, holding <K>Q = f/Δf</K> constant so the tiling adapts to scale:</P>
          <Eq>W[a,b] = (1/√a) Σ<sub>n</sub> x[n] · ψ*((n−b)/a)</Eq>
          <P size={26}>But <K>Q</K> and the shape of <K>ψ</K> are fixed <i>before</i> training. The wavelet <b>relocates</b> the commitment along the bound — it does not remove it.</P>
        </div>
        <svg viewBox="0 0 860 420" style={{ flex: 1 }}>
          <defs><marker id="ar" markerWidth="9" markerHeight="9" refX="6" refY="4" orient="auto"><path d="M0 0 L7 4 L0 8 z" fill={INK} /></marker><marker id="arv" markerWidth="9" markerHeight="9" refX="4" refY="6" orient="auto"><path d="M0 7 L4 0 L7 7 z" fill={INK} /></marker></defs>
          {stft}{wav}
          {[lx, rx].map((x) => (<g key={x}><line x1={x} y1={pyT + ph} x2={x + pw + 12} y2={pyT + ph} stroke={INK} strokeWidth={1.8} markerEnd="url(#ar)" /><line x1={x} y1={pyT + ph} x2={x} y2={pyT - 12} stroke={INK} strokeWidth={1.8} markerEnd="url(#arv)" /><text x={x + pw + 2} y={pyT + ph + 26} fontFamily={MONO} fontSize={17} fill={MUTED}>t</text><text x={x - 20} y={pyT - 2} fontFamily={MONO} fontSize={17} fill={MUTED}>f</text></g>))}
          <text x={lx + pw / 2} y={40} textAnchor="middle" fontFamily={SERIF} fontSize={24} fontWeight={700} fill={BLUE}>STFT</text>
          <text x={rx + pw / 2} y={40} textAnchor="middle" fontFamily={SERIF} fontSize={24} fontWeight={700} fill={ORANGE}>Wavelet</text>
        </svg>
      </div>
    </Frame>
  );
};

// ═══ 09 — Gabor bound ════════════════════════════════════════════════════════════
const Gabor: Page = () => {
  const px = 120, pw = 900, cy = 150, amp = 105, sig = 0.13, om = 2 * Math.PI * 6;
  const atom = () => { let d = 'M'; const N = 300; for (let i = 0; i <= N; i++) { const t = i / N, x = px + t * pw, u = t - 0.5, e = Math.exp(-(u * u) / (2 * sig * sig)); d += x.toFixed(1) + ' ' + (cy - amp * e * Math.cos(om * u)).toFixed(1) + (i < N ? ' L' : ''); } return d; };
  const env = (s: number) => { let d = 'M'; const N = 120; for (let i = 0; i <= N; i++) { const t = i / N, x = px + t * pw, u = t - 0.5, e = Math.exp(-(u * u) / (2 * sig * sig)); d += x.toFixed(1) + ' ' + (cy - s * amp * e).toFixed(1) + (i < N ? ' L' : ''); } return d; };
  return (
    <Frame kicker="A time-frequency limit" title="The Heisenberg–Gabor bound">
      <P mt={2}>Both transforms obey the uncertainty inequality, with equality only for the <b>Gabor atom</b> — a Gaussian-modulated sinusoid:</P>
      <Eq><span style={{ color: BLUE, fontSize: 40 }}>σ<sub>t</sub> · σ<sub>f</sub> ≥ 1/4π</span></Eq>
      <svg viewBox="0 0 1140 320" style={{ width: '100%', maxWidth: 1360, alignSelf: 'center' }}>
        <path d={env(1)} fill="none" stroke={ORANGE} strokeWidth={2.2} strokeDasharray="6 5" />
        <path d={env(-1)} fill="none" stroke={ORANGE} strokeWidth={2.2} strokeDasharray="6 5" />
        <path d={atom()} fill="none" stroke={BLUE} strokeWidth={3} />
        <text x={px + pw} y={cy - amp - 10} textAnchor="end" fontFamily={MONO} fontSize={19} fill={ORANGE}>Gaussian envelope</text>
      </svg>
      <P mt={6}>Pinning the tremor to <K>±1 Hz</K> demands <K c={BLUE}>σ<sub>t</sub> ≥ 0.08 s</K> (longer than an arrest); timing an arrest to <K>±10 ms</K> demands <K c={ORANGE}>σ<sub>f</sub> ≥ 8 Hz</K> (wider than the tremor band). <b>Direct conflict.</b></P>
    </Frame>
  );
};

// ═══ 10 — Upstream of the model ══════════════════════════════════════════════════
const Upstream: Page = () => {
  const Box = ({ x, w, label, sub, filled }: any) => (<g>
    <rect x={x} y={40} width={w} height={104} rx={8} fill={filled ? INK : '#eef2f9'} stroke={INK} strokeWidth={2} />
    <text x={x + w / 2} y={88} textAnchor="middle" fontFamily={SERIF} fontSize={26} fontWeight={700} fill={filled ? '#fff' : INK}>{label}</text>
    <text x={x + w / 2} y={118} textAnchor="middle" fontFamily={MONO} fontSize={17} fill={filled ? '#cfd4dc' : MUTED}>{sub}</text>
  </g>);
  return (
    <Frame kicker="A time-frequency limit" title="The limit is upstream of the classifier">
      <P mt={2}>The inequality constrains the <b>input</b>, not the model. Whatever fills the black box, it receives a short 150 Hz recording whose joint time-frequency content is <i>already</i> limited — no downstream computation recovers information the measurement never contained.</P>
      <svg viewBox="0 0 1240 240" style={{ width: '100%', maxWidth: 1400, alignSelf: 'center', marginTop: 8 }}>
        <defs><marker id="ah" markerWidth="10" markerHeight="10" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 z" fill={INK} /></marker></defs>
        <Box x={80} w={280} label="pen input" sub="x, y, p @ 150 Hz" />
        <Box x={480} w={280} label="any model" sub="RNN · CNN · ViT · SVM" filled />
        <Box x={880} w={280} label="PD / HC" sub="decision" />
        <line x1={360} y1={92} x2={480} y2={92} stroke={INK} strokeWidth={2.5} markerEnd="url(#ah)" />
        <line x1={760} y1={92} x2={880} y2={92} stroke={INK} strokeWidth={2.5} markerEnd="url(#ah)" />
        <line x1={80} y1={186} x2={1160} y2={186} stroke={RED} strokeWidth={2.5} strokeDasharray="9 7" />
        <text x={620} y={222} textAnchor="middle" fontFamily={MONO} fontSize={21} fill={RED}>σ_t·σ_f ≥ 1/4π — bounded before the box</text>
      </svg>
      <P mt={10} size={24}>A reported <K c={RED}>99%</K> therefore need not mean the signal is resolved — only that the evaluation was permissive.</P>
    </Frame>
  );
};

// ═══ 11 — Reframe ════════════════════════════════════════════════════════════════
const Reframe: Page = () => {
  const Card = ({ c, bg, tag, title, body, mark }: any) => (
    <div style={{ flex: 1, padding: '30px 34px', border: `2px solid ${c}`, borderRadius: 12, background: bg }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <span style={{ fontSize: 40, fontWeight: 800, color: c }}>{mark}</span>
        <span style={{ fontSize: 19, ...num, textTransform: 'uppercase', letterSpacing: '0.1em', color: c }}>{tag}</span>
      </div>
      <div style={{ fontFamily: SERIF, fontSize: 32, fontWeight: 700, margin: '14px 0 10px', color: INK }}>{title}</div>
      <div style={{ fontSize: 24, lineHeight: 1.45, color: TXT }}>{body}</div>
    </div>
  );
  return (
    <Frame kicker="Method — the idea" title="Change the question: preserve, don't separate">
      <P mt={2}>Learning a filter that <i>separates</i> the PD signal from the healthy one is an ill-posed inverse problem at this resolution. So we stop trying to separate — and instead preserve the structure the bound lets us keep.</P>
      <div style={{ display: 'flex', gap: 40, marginTop: 34 }}>
        <Card c={RED} bg="#fbe9e7" mark="✗" tag="The old question" title="Separate the two signals"
          body={<>Recover the tremor from the arrests — an inverse problem the uncertainty bound forbids on a short 150 Hz signal.</>} />
        <Card c={GREEN} bg="#e3f5e9" mark="✓" tag="Our question" title="Preserve the structure"
          body={<>Draw the trajectory, colour each point by <i>how fast, how hard, where</i> — discard only the phase we could never recover anyway.</>} />
      </div>
    </Frame>
  );
};

// ═══ 12 — Dataset + spirals ══════════════════════════════════════════════════════
const Dataset: Page = () => {
  const Cell = ({ src, cap, c }: { src: string; cap: string; c: string }) => (
    <div style={{ textAlign: 'center' }}>
      <div style={{ padding: 6, borderRadius: 14, background: '#000', boxShadow: `0 8px 24px rgba(0,0,0,0.22), 0 0 0 2px ${c}`, display: 'inline-block' }}>
        <img src={src} style={{ width: 214, height: 214, borderRadius: 9, display: 'block', imageRendering: 'auto' }} />
      </div>
      <div style={{ fontSize: 18, ...num, color: c, marginTop: 10, fontWeight: 600 }}>{cap}</div>
    </div>
  );
  return (
    <Frame kicker="Method — dataset" title="PaHaW: one spiral per subject">
      <div style={{ display: 'flex', gap: 48, alignItems: 'center' }}>
        <div style={{ flex: '0 0 760px' }}>
          <P size={26}>PaHaW<Cite>1</Cite> — <K>72</K> subjects on a Wacom tablet at <K>f<sub>s</sub> = 150 Hz</K>; each sample is a 7-tuple</P>
          <Eq><span style={{ fontSize: 24 }}>s<sub>n</sub> = (x<sub>n</sub>, y<sub>n</sub>, t<sub>n</sub>, b<sub>n</sub>, p<sub>n</sub>, θ<sup>az</sup>, θ<sup>al</sup>)</span></Eq>
          <P size={26}>We use only <b>Task 1</b> (the Archimedean spiral): one recording per subject, so the subject decision <i>is</i> the recording decision — removing the cross-task leakage that inflates other studies.</P>
        </div>
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, auto)', gap: 24 }}>
            <Cell src={effHc} cap="HC · effort" c={GREEN} />
            <Cell src={effPd} cap="PD · effort" c={ORANGE} />
            <Cell src={velHc} cap="HC · velocity" c={GREEN} />
            <Cell src={velPd} cap="PD · velocity" c={ORANGE} />
          </div>
          <div style={{ fontSize: 18, color: MUTED, fontStyle: 'italic', fontFamily: SERIF, marginTop: 12, maxWidth: 480, textAlign: 'center' }}>Fig. 1. Real colour-encoded PaHaW spirals (Task 1).</div>
        </div>
      </div>
    </Frame>
  );
};

// ═══ 13 — Encoding: HC vs PD ═════════════════════════════════════════════════════
const Encoding: Page = () => {
  const Col = ({ label, c, imgs }: { label: string; c: string; imgs: [string, string][] }) => (
    <div style={{ textAlign: 'center' }}>
      <div style={{ fontFamily: SERIF, fontSize: 26, fontWeight: 700, color: c, marginBottom: 14 }}>{label}</div>
      <div style={{ display: 'flex', gap: 22 }}>
        {imgs.map(([src, cap]) => (
          <div key={cap} style={{ textAlign: 'center' }}>
            <div style={{ padding: 5, borderRadius: 13, background: '#000', boxShadow: `0 8px 22px rgba(0,0,0,0.2), 0 0 0 2px ${c}`, display: 'inline-block' }}>
              <img src={src} style={{ width: 202, height: 202, borderRadius: 9, display: 'block' }} />
            </div>
            <div style={{ fontSize: 17, ...num, color: MUTED, marginTop: 9 }}>{cap}</div>
          </div>
        ))}
      </div>
    </div>
  );
  return (
    <Frame kicker="Method — encoding" title="A structure-preserving colour encoding">
      <P mt={2}>We draw the spiral on a <K>224×224</K> canvas and colour each pen sample by a kinematic channel with a perceptually-uniform map. The PD spiral reads slower, tighter and lower-effort — visible <i>as a picture</i>.</P>
      <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: 28, alignItems: 'flex-start' }}>
        <Col label="Healthy control" c={GREEN} imgs={[[velHc, 'velocity'], [effHc, 'effort'], [rgbHc, 'rgb v·p·e']]} />
        <div style={{ width: 2, alignSelf: 'stretch', background: HAIR }} />
        <Col label="Parkinson's disease" c={ORANGE} imgs={[[velPd, 'velocity'], [effPd, 'effort'], [rgbPd, 'rgb v·p·e']]} />
      </div>
    </Frame>
  );
};

// ═══ 14 — Pipeline ═══════════════════════════════════════════════════════════════
const Pipeline: Page = () => {
  const Box = ({ x, w, fill: bg, label, sub }: any) => (<g>
    <rect x={x} y={70} width={w} height={100} rx={8} fill={bg} stroke={INK} strokeWidth={1.6} />
    <text x={x + w / 2} y={112} textAnchor="middle" fontFamily={SERIF} fontSize={23} fontWeight={700} fill={INK}>{label}</text>
    <text x={x + w / 2} y={140} textAnchor="middle" fontFamily={MONO} fontSize={15} fill={MUTED}>{sub}</text>
  </g>);
  const xs = [60, 320, 600, 890, 1170]; const ws = [230, 250, 260, 250, 200];
  const labels = [['raw signal', 'v, p, e @ 150 Hz'], ['colour image', '224×224'], ['frozen encoder', 'ViT / Swin / EffNet'], ['z-score + head', '7 tuned heads'], ['decision', 'PD / HC']];
  const cols = ['#e8eefb', '#dbe6f8', '#e0f0e4', '#f6e9d8', '#eeeeee'];
  return (
    <Frame kicker="Method — pipeline" title="Re-encode → frozen backbone → tuned head">
      <P mt={2}>The kinematics become a colour image, embedded by a <b>frozen</b> ImageNet backbone (no training on 72 subjects), then classified by a per-fold-tuned head. The handcrafted clinical vector <i>(dashed)</i> bypasses the encoder as a baseline.</P>
      <svg viewBox="0 0 1400 300" style={{ width: '100%', maxWidth: 1500, alignSelf: 'center', marginTop: 12 }}>
        <defs><marker id="ap" markerWidth="10" markerHeight="10" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 z" fill={INK} /></marker></defs>
        {xs.map((x, i) => <Box key={i} x={x} w={ws[i]} fill={cols[i]} label={labels[i][0]} sub={labels[i][1]} />)}
        {xs.slice(0, -1).map((x, i) => <line key={i} x1={x + ws[i]} y1={120} x2={xs[i + 1]} y2={120} stroke={INK} strokeWidth={2.2} markerEnd="url(#ap)" />)}
        <rect x={320} y={220} width={250} height={64} rx={8} fill="#e0f0e4" stroke={INK} strokeWidth={1.4} strokeDasharray="6 5" />
        <text x={445} y={248} textAnchor="middle" fontFamily={SERIF} fontSize={20} fontWeight={700} fill={INK}>handcrafted 33-d</text>
        <text x={445} y={270} textAnchor="middle" fontFamily={MONO} fontSize={14} fill={MUTED}>clinical baseline</text>
        <path d="M570 252 L1015 252 L1015 172" fill="none" stroke={INK} strokeWidth={1.8} strokeDasharray="6 5" markerEnd="url(#ap)" />
      </svg>
    </Frame>
  );
};

// ═══ 15 — The grid ═══════════════════════════════════════════════════════════════
const Grid: Page = () => (
  <Frame kicker="Method — search space" title="Ten encodings × three backbones × seven heads">
    <P mt={2}>We render <K>ten</K> image modalities — six single-channel maps (velocity, acceleration, pressure, azimuth, altitude, effort), three RGB triplets, one geometry-only control — embed each with three frozen backbones, and tune seven heads (logistic regression, three SVMs, a random forest, two MLPs).</P>
    <div style={{ display: 'flex', justifyContent: 'center', gap: 70, marginTop: 44 }}>
      {[['10 × 3 + 1', 'inputs = 31'], ['× 7', 'tuned heads'], ['= 217', 'input–head cells']].map(([a, b]) => (
        <div key={a} style={{ textAlign: 'center' }}>
          <div style={{ fontFamily: MONO, fontSize: 58, fontWeight: 700, color: BLUE }}>{a}</div>
          <div style={{ fontSize: 23, color: MUTED, marginTop: 10 }}>{b}</div>
        </div>
      ))}
    </div>
    <P mt={44} size={24}>Every cell is evaluated under the <i>same</i> honest protocol — so the comparison is fair and the winner is earned, not selected.</P>
  </Frame>
);

// ═══ 16 — Protocol ═══════════════════════════════════════════════════════════════
const Protocol: Page = () => (
  <Frame kicker="Evaluation — protocol" title="Repeated nested CV with a corrected test">
    <P mt={2}>We run <K>R = 3</K> repeats (seeds 42, 43, 44) of 10-fold <K>StratifiedGroupKFold</K> (subject = group<Cite>9</Cite>) → <K>N = 30</K> test folds per cell; an inner 3-fold grid search tunes each head on the training portion only. Models are compared with the Nadeau–Bengio corrected paired <i>t</i>-test<Cite>8</Cite>:</P>
    <Eq><span style={{ fontSize: 34 }}>t<sub>NB</sub> = d̄ / √[ (1/N + n<sub>test</sub>/n<sub>train</sub>) · s² ]</span>,&nbsp;&nbsp; df = N − 1 = 29</Eq>
    <P>For 10-fold CV this multiplies the naive variance by <K>0.144/0.033 ≈ 4.3</K>, so <K>t<sub>NB</sub></K> is <K c={RED}>≈ 2.1× smaller</K> than its naive twin — repairing the optimism from train/test overlap.</P>
  </Frame>
);

// ═══ 17 — Table 2: significance ══════════════════════════════════════════════════
const TabSig: Page = () => {
  const GT = '2.4fr 0.7fr 0.75fr 0.9fr 0.75fr 0.9fr';
  const Row = ({ m, f, tn, pn, tc, pc, sig, hi }: any) => (
    <div style={{ display: 'grid', gridTemplateColumns: GT, alignItems: 'center', fontSize: 24, padding: '10px 6px', background: hi ? '#eaf6ec' : 'transparent', borderRadius: hi ? 6 : 0 }}>
      <span>{m}</span><span style={{ textAlign: 'right', ...num }}>{f}</span><span style={{ textAlign: 'right', ...num }}>{tn}</span>
      <span style={{ textAlign: 'right', ...num, color: sig ? RED : INK }}>{pn}</span><span style={{ textAlign: 'right', ...num }}>{tc}</span>
      <span style={{ textAlign: 'right', ...num, color: hi ? GREEN : INK }}>{pc}</span>
    </div>
  );
  return (
    <Frame kicker="Evaluation — results" title="The correction erases the fine-grained ranking">
      <div style={{ fontSize: 21, color: MUTED, fontStyle: 'italic', fontFamily: SERIF, marginBottom: 12 }}>
        Table 2. Champion (effort · ViT · random forest; F1 = 0.7457) vs. rivals; naive and Nadeau–Bengio corrected paired <i>t</i>-tests (df = 29). Red: naive-significant · Green: survives correction.
      </div>
      <div style={{ borderTop: `2.5px solid ${RULE}` }} />
      <div style={{ display: 'grid', gridTemplateColumns: GT, fontSize: 20, color: MUTED, padding: '10px 6px' }}>
        <span>Comparison (rival's own F1)</span><span style={{ textAlign: 'right' }}>F1</span><span style={{ textAlign: 'right' }}>t naive</span><span style={{ textAlign: 'right' }}>p naive</span><span style={{ textAlign: 'right' }}>t NB</span><span style={{ textAlign: 'right' }}>p NB</span>
      </div>
      <div style={{ borderTop: `1.5px solid ${RULE}` }} />
      <Row m="velocity · ViT · RF" f="0.7090" tn="1.36" pn="0.1850" tc="0.65" pc="0.5194" />
      <Row m="raw · Swin · RF" f="0.6473" tn="2.43" pn="0.0215" tc="1.17" pc="0.2527" sig />
      <Row m="acceleration · ViT · MLP-s" f="0.6372" tn="3.53" pn="0.0014" tc="1.69" pc="0.1010" sig />
      <Row m="rgb_vpz · ViT · RF" f="0.6226" tn="4.02" pn="0.0004" tc="1.93" pc="0.0631" sig />
      <Row m="pressure · Swin · MLP-f" f="0.6157" tn="3.32" pn="0.0025" tc="1.59" pc="0.1221" sig />
      <div style={{ borderTop: `1px solid ${HAIR}`, margin: '4px 0' }} />
      <Row m="champion F1 vs. chance" f="0.7457" tn="—" pn="<.0001" tc="3.64" pc="0.0011" hi />
      <Row m="champion vs. clinical baseline" f="0.5080" tn="—" pn="<.0001" tc="2.49" pc="0.0187" hi />
      <div style={{ borderTop: `2.5px solid ${RULE}` }} />
      <div style={{ fontSize: 20, color: MUTED, marginTop: 12 }}>Naive test: <K c={RED}>7/7</K> “significant”. After correction: <K c={GREEN}>0</K>. Over all 30 rivals, <K>29 → 10</K>; none of the 9 nearest survive.</div>
    </Frame>
  );
};

// ═══ 18 — Discussion ═════════════════════════════════════════════════════════════
const Discussion: Page = () => {
  const Col = ({ c, bg, tag, children }: any) => (
    <div style={{ flex: 1, padding: '26px 30px', borderTop: `4px solid ${c}`, background: bg, borderRadius: '0 0 10px 10px' }}>
      <div style={{ fontFamily: SERIF, fontSize: 28, fontWeight: 700, color: c, marginBottom: 12 }}>{tag}</div>
      <div style={{ fontSize: 24, lineHeight: 1.45, color: TXT }}>{children}</div>
    </div>
  );
  return (
    <Frame kicker="Evaluation — discussion" title="A real but coarse signal">
      <div style={{ display: 'flex', gap: 36, marginTop: 8 }}>
        <Col c={GREEN} bg="#f1f8f2" tag="What survives">
          The champion (effort · ViT · RF) beats chance on every metric (<K c={GREEN}>p ≤ 0.0011</K>) and the 33-d clinical baseline (F1 <K c={GREEN}>0.746</K> vs. <K>0.508</K>, <K c={GREEN}>p = 0.019</K>). <b>Effort and velocity</b> — the tremor and its pressure modulation — are the channels that help.
        </Col>
        <Col c={RED} bg="#fcf2f1" tag="What does not">
          Nothing finer. The winner beats <K>29</K> of 30 rivals naively but only <K>10</K> after correction — and <b>none</b> of its nine nearest. Subject-level F1 takes just <K>nine</K> values over ≈7 held-out subjects; the best head even flips RF↔MLP with the metric.
        </Col>
      </div>
      <P mt={30} size={25}>The ranking below effort/velocity is <b>flat</b> down to the baseline: PaHaW is <i>not</i> yet a solved task.</P>
    </Frame>
  );
};

// ═══ 19 — Conclusion ═════════════════════════════════════════════════════════════
const Conclusion: Page = () => (
  <Frame kicker="Conclusion" title="On 72 subjects, the honest number is a modest one">
    <P mt={4} size={30}>The PD signature is a <b>time-frequency object</b> no fixed representation can resolve, by the Heisenberg–Gabor principle. PaHaW's high reported figures therefore partly reflect leakage and optimistic testing — not a fully solved task.</P>
    <P mt={22} size={30}>Rather than separate the two signals, we <b>re-encode</b> them into a structure-preserving colour image a frozen vision model can attack. Evaluated honestly it clears chance and a clinical baseline — <i>but nothing finer</i>.</P>
    <div style={{ marginTop: 34, fontSize: 21, ...num, color: MUTED }}>Reproducibility — seeds {'{42, 43, 44}'} · <span style={{ color: BLUE }}>run_repeated.py · nadeau_bengio.py · full_pairwise.py</span></div>
  </Frame>
);

// ═══ 20 — References ═════════════════════════════════════════════════════════════
const Refs: Page = () => {
  const refs = [
    'P. Drotár et al. Evaluation of handwriting kinematics and pressure for PD diagnosis. Artif. Intell. Med., 2016.',
    'D. Impedovo, G. Pirlo. Dynamic handwriting analysis for neurodegenerative disease assessment. IEEE Rev. Biomed. Eng., 2019.',
    'M. Diaz et al. Sequence-based dynamic handwriting analysis for PD. Pattern Recognit. Lett., 2021.',
    'X. Wang et al. Handwriting-based PD detection. Biomed. Signal Process. Control, 2024.',
    'A. Kumar, S. Ghosh. Handwriting-based PD classification. 2024.',
    'J. Shin et al. PD detection based on in-air dynamics features. 2025.',
    'E. Valla et al. Tremor-related feature engineering for ML-based PD detection. 2022.',
    'C. Nadeau, Y. Bengio. Inference for the generalization error. Mach. Learn., 2003.',
    'S. Varma, R. Simon. Bias in error estimation when using CV for model selection. BMC Bioinf., 2006.',
    'A. Dosovitskiy et al. An image is worth 16×16 words (ViT). ICLR, 2021.',
    'Z. Liu et al. Swin Transformer. ICCV, 2021.',
    'M. Tan, Q. Le. EfficientNet. ICML, 2019.',
  ];
  return (
    <Frame kicker="References" title="References">
      <div style={{ columns: 2, columnGap: 64, marginTop: 6 }}>
        {refs.map((r, i) => (
          <div key={i} style={{ breakInside: 'avoid', display: 'flex', gap: 12, marginBottom: 14, fontSize: 20, lineHeight: 1.35, color: TXT }}>
            <span style={{ ...num, color: BLUE, fontWeight: 600, minWidth: 30 }}>[{i + 1}]</span><span>{r}</span>
          </div>
        ))}
      </div>
    </Frame>
  );
};

// ─── Transition ─────────────────────────────────────────────────────────────────
const EO = 'cubic-bezier(0, 0, 0.2, 1)', EI = 'cubic-bezier(0.4, 0, 1, 1)';
export const transition: SlideTransition = {
  duration: 190,
  exit: { duration: 130, easing: EI, keyframes: [{ opacity: 1 }, { opacity: 0 }] },
  enter: { duration: 190, delay: 50, easing: EO, keyframes: [{ opacity: 0, transform: 'translateY(5px)' }, { opacity: 1, transform: 'translateY(0)' }] },
};
export const meta: SlideMeta = { title: '99% Sure? Gabor Begs to Differ', createdAt: '2026-07-01T08:22:38.690Z' };
export default [
  Title, Motivation, Paradox, TabLit, Pitfalls,
  Signal, STFT, Wavelet, Gabor, Upstream,
  Reframe, Dataset, Encoding, Pipeline, Grid,
  Protocol, TabSig, Discussion, Conclusion, Refs,
] satisfies Page[];
