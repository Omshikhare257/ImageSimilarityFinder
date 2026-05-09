import { useState, useRef } from "react";

if (!document.getElementById("isf-font")) {
  const l = document.createElement("link");
  l.id = "isf-font"; l.rel = "stylesheet";
  l.href = "https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&display=swap";
  document.head.appendChild(l);
}

const RAW_CSS = `
  @keyframes fadeUp  { from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)} }
  @keyframes fadeIn  { from{opacity:0}to{opacity:1} }
  @keyframes pulse   { 0%,100%{opacity:1}50%{opacity:.35} }
  @keyframes spin    { to{transform:rotate(360deg)} }
  @keyframes scanline{ 0%{top:-60px}100%{top:110%} }

  .isf*{box-sizing:border-box;margin:0;padding:0}
  .isf{
    font-family:'DM Sans',sans-serif;
    background:#08080F;
    color:#EEEEF5;
    min-height:100vh;
  }

  .isf-hdr{
    display:flex;align-items:center;justify-content:space-between;
    padding:22px 48px;
    border-bottom:1px solid #1C1C28;
    animation:fadeIn .5s ease both;
  }
  .isf-logo{display:flex;align-items:center;gap:12px}
  .isf-logo-gem{
    width:38px;height:38px;border-radius:10px;
    background:linear-gradient(135deg,#6C63FF,#A78BFA);
    display:flex;align-items:center;justify-content:center;
    font-size:17px;
    box-shadow:0 0 24px #6C63FF55;
  }
  .isf-logo-name{font-family:'Syne',sans-serif;font-size:15px;font-weight:700;letter-spacing:.04em}
  .isf-logo-tagline{font-size:10px;color:#66668A;letter-spacing:.07em;margin-top:1px}
  .isf-hdr-badge{
    font-size:10px;font-weight:700;letter-spacing:.12em;
    background:#6C63FF18;color:#A78BFA;
    border:1px solid #6C63FF44;border-radius:99px;padding:5px 14px;
  }

  .isf-main{max-width:1080px;margin:0 auto;padding:52px 48px 100px}

  .isf-hero{text-align:center;margin-bottom:52px;animation:fadeUp .6s .1s ease both}
  .isf-hero h1{
    font-family:'Syne',sans-serif;
    font-size:clamp(26px,4vw,50px);font-weight:800;
    letter-spacing:-.025em;line-height:1.08;
    margin-bottom:16px;
    background:linear-gradient(130deg,#EEEEF5 0%,#6C63FF 55%,#A78BFA 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  }
  .isf-hero p{font-size:14px;color:#7070A0;max-width:460px;margin:0 auto;line-height:1.75}

  .isf-urow{
    display:grid;grid-template-columns:1fr 60px 1fr;
    gap:0;margin-bottom:28px;
    animation:fadeUp .6s .2s ease both;
  }
  .isf-dz-label{
    font-family:'Syne',sans-serif;font-size:10px;font-weight:700;
    letter-spacing:.13em;color:#44445A;text-transform:uppercase;
    margin-bottom:10px;display:flex;align-items:center;gap:8px;
  }
  .isf-dz-label em{
    width:18px;height:18px;border-radius:50%;
    background:#161622;border:1px solid #2A2A3A;
    display:inline-flex;align-items:center;justify-content:center;
    font-style:normal;font-size:10px;color:#8080A8;
  }
  .isf-dz{
    border:1px dashed #2A2A3A;border-radius:16px;
    background:#0E0E1A;height:230px;
    display:flex;flex-direction:column;align-items:center;justify-content:center;
    cursor:pointer;transition:border-color .2s,background .2s,box-shadow .2s;
    overflow:hidden;position:relative;
  }
  .isf-dz:hover,.isf-dz.drag{
    border-color:#6C63FF;background:#11111E;
    box-shadow:0 0 36px #6C63FF1A;
  }
  .isf-dz-ico{
    width:50px;height:50px;border-radius:14px;
    background:#161622;border:1px solid #2A2A3A;
    display:flex;align-items:center;justify-content:center;
    font-size:20px;margin-bottom:14px;
    transition:transform .2s;
  }
  .isf-dz:hover .isf-dz-ico{transform:scale(1.1) rotate(-4deg)}
  .isf-dz-txt{font-size:13px;color:#7070A0;margin-bottom:4px}
  .isf-dz-hint{font-size:11px;color:#44445A}
  .isf-dz img{width:100%;height:100%;object-fit:cover;position:absolute;inset:0}
  .isf-dz-ov{
    position:absolute;inset:0;
    background:linear-gradient(to top,rgba(8,8,15,.92) 0%,transparent 55%);
    display:flex;align-items:flex-end;padding:14px;
    opacity:0;transition:opacity .2s;
  }
  .isf-dz:hover .isf-dz-ov{opacity:1}
  .isf-rm{
    background:rgba(239,68,68,.15);border:1px solid rgba(239,68,68,.4);
    color:#FCA5A5;border-radius:8px;font-size:11px;font-weight:500;
    padding:5px 12px;cursor:pointer;transition:background .15s;
  }
  .isf-rm:hover{background:rgba(239,68,68,.3)}

  .isf-dz:hover .isf-scan{
    position:absolute;left:0;right:0;height:60px;pointer-events:none;
    background:linear-gradient(to bottom,transparent,#6C63FF18,transparent);
    animation:scanline 1.4s ease-in-out infinite;
  }

  .isf-fname{
    position:absolute;bottom:0;left:0;right:0;
    background:rgba(8,8,15,.85);
    font-size:10px;color:#7070A0;
    padding:6px 10px;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
  }

  .isf-vs{display:flex;align-items:center;justify-content:center;padding-top:32px}
  .isf-vs-c{
    width:42px;height:42px;border-radius:50%;
    background:#0E0E1A;border:1px solid #2A2A3A;
    display:flex;align-items:center;justify-content:center;
    font-family:'Syne',sans-serif;font-size:11px;font-weight:700;color:#66668A;
  }

  .isf-btn{
    width:100%;padding:16px;
    font-family:'Syne',sans-serif;font-size:13px;font-weight:700;
    letter-spacing:.1em;text-transform:uppercase;
    border-radius:14px;border:none;cursor:pointer;
    transition:all .2s;margin-bottom:28px;
    animation:fadeUp .6s .3s ease both;
  }
  .isf-btn-on{
    background:linear-gradient(135deg,#6C63FF,#8B83FF);
    color:#fff;box-shadow:0 4px 28px #6C63FF44;
  }
  .isf-btn-on:hover{box-shadow:0 6px 40px #6C63FF77;transform:translateY(-2px)}
  .isf-btn-off{background:#0E0E1A;color:#44445A;border:1px solid #1C1C28;cursor:not-allowed}
  .isf-btn-load{background:#111120;color:#6C63FF;border:1px solid #6C63FF44;cursor:wait}
  .isf-spin{
    display:inline-block;width:13px;height:13px;
    border:2px solid #6C63FF44;border-top-color:#6C63FF;
    border-radius:50%;animation:spin .7s linear infinite;
    margin-right:10px;vertical-align:middle;
  }

  .isf-err{
    background:#180F0F;border:1px solid rgba(239,68,68,.3);
    border-radius:12px;padding:14px 18px;
    font-size:13px;color:#FCA5A5;margin-bottom:24px;
    animation:fadeUp .3s ease both;
  }
  .isf-err small{display:block;margin-top:6px;font-size:11px;opacity:.6;color:#FCA5A5}
  .isf-err code{
    font-family:monospace;font-size:11px;
    background:#2A0A0A;padding:1px 5px;border-radius:4px;
  }

  .isf-res{animation:fadeUp .5s ease both}

  .isf-shero{
    background:#0E0E1A;border:1px solid #1C1C28;
    border-radius:20px;padding:40px 44px;
    display:grid;grid-template-columns:auto 1fr auto;
    gap:44px;align-items:center;
    margin-bottom:20px;position:relative;overflow:hidden;
  }
  .isf-shero::before{
    content:'';position:absolute;inset:0;
    background:radial-gradient(ellipse at 15% 50%,var(--glow,#6C63FF18) 0%,transparent 65%);
    pointer-events:none;
  }
  .isf-shero::after{
    content:'';position:absolute;top:0;left:0;right:0;height:1px;
    background:linear-gradient(90deg,transparent,var(--lc,#6C63FF),transparent);
    opacity:.5;
  }

  .isf-ring-wrap{position:relative;width:136px;height:136px}
  .isf-ring-svg{width:136px;height:136px;transform:rotate(-90deg)}
  .isf-ring-bg{fill:none;stroke:#1C1C28;stroke-width:7}
  .isf-ring-fg{
    fill:none;stroke-width:7;stroke-linecap:round;
    stroke-dasharray:339;stroke-dashoffset:var(--dash,339);
    transition:stroke-dashoffset 1.3s cubic-bezier(.23,1,.32,1);
  }
  .isf-ring-inner{
    position:absolute;inset:0;
    display:flex;flex-direction:column;align-items:center;justify-content:center;
  }
  .isf-ring-num{font-family:'Syne',sans-serif;font-size:32px;font-weight:800;line-height:1}
  .isf-ring-sub{font-size:11px;color:#66668A;margin-top:2px}

  .isf-vchip{
    display:inline-block;
    font-family:'Syne',sans-serif;font-size:10px;font-weight:700;letter-spacing:.14em;
    padding:4px 13px;border-radius:99px;border:1px solid;
    margin-bottom:12px;
  }
  .isf-vtitle{
    font-family:'Syne',sans-serif;
    font-size:clamp(18px,2.5vw,28px);font-weight:800;
    letter-spacing:-.015em;margin-bottom:8px;
  }
  .isf-vsub{font-size:13px;color:#7070A0;line-height:1.7}

  .isf-analysis{
    margin-top:10px;font-size:11px;color:#7070A0;line-height:1.7;
    max-width:340px;background:#161622;border-radius:8px;
    padding:8px 12px;border:1px solid #2A2A3A;
  }

  .isf-mbars{display:flex;flex-direction:column;gap:10px;min-width:175px}
  .isf-mrow{}
  .isf-mtop{display:flex;justify-content:space-between;font-size:10px;color:#66668A;margin-bottom:4px}
  .isf-mtop b{color:var(--c);font-weight:600}
  .isf-mtrack{height:3px;border-radius:99px;background:#1C1C28;overflow:hidden}
  .isf-mfill{height:100%;border-radius:99px;background:var(--c);width:var(--w);transition:width 1s cubic-bezier(.23,1,.32,1)}

  .isf-stitle{
    font-family:'Syne',sans-serif;font-size:10px;font-weight:700;
    letter-spacing:.14em;text-transform:uppercase;color:#44445A;
    margin-bottom:14px;display:flex;align-items:center;gap:10px;
  }
  .isf-stitle::after{content:'';flex:1;height:1px;background:#1C1C28}

  .isf-cgrid{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
    gap:12px;margin-bottom:20px;
  }
  .isf-mc{
    background:#0E0E1A;border:1px solid #1C1C28;
    border-radius:14px;padding:20px;
    transition:border-color .2s,transform .2s,box-shadow .2s;
    position:relative;overflow:hidden;
  }
  .isf-mc::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--mc);opacity:.7}
  .isf-mc:hover{border-color:var(--mc);transform:translateY(-3px);box-shadow:0 14px 36px rgba(0,0,0,.5)}
  .isf-mc-top2{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:14px}
  .isf-mc-icon2{
    width:36px;height:36px;border-radius:9px;
    display:flex;align-items:center;justify-content:center;
    font-size:15px;background:var(--mclo);
    border:1px solid var(--mc);color:var(--mc);flex-shrink:0;
  }
  .isf-mc-score2{
    font-family:'Syne',sans-serif;font-size:22px;font-weight:800;
    color:var(--mc);line-height:1;
  }
  .isf-mc-score2 span{font-size:12px;font-weight:500}
  .isf-mc-name2{font-size:12px;font-weight:500;color:#CCCCE0;margin-bottom:6px}
  .isf-mc-bar-t{height:2px;border-radius:99px;background:#1C1C28;overflow:hidden;margin-bottom:10px}
  .isf-mc-bar-f{height:100%;border-radius:99px;background:var(--mc);width:var(--w);transition:width 1.2s cubic-bezier(.23,1,.32,1)}
  .isf-mc-desc2{font-size:11px;color:#66668A;line-height:1.65;margin-bottom:10px}
  .isf-pill2{
    display:inline-block;font-size:10px;
    background:#161622;border:1px solid #2A2A3A;
    color:#66668A;border-radius:99px;padding:2px 8px;
    margin-right:4px;margin-top:2px;
  }

  .isf-theory{
    background:#0E0E1A;border:1px solid #1C1C28;
    border-radius:16px;padding:26px 30px;
  }
  .isf-theory-ttl{
    font-family:'Syne',sans-serif;font-size:12px;font-weight:700;
    letter-spacing:.08em;color:#66668A;margin-bottom:20px;
    display:flex;align-items:center;gap:8px;
  }
  .isf-tgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:18px}
  .isf-ti h4{
    font-family:'Syne',sans-serif;font-size:12px;font-weight:700;
    color:#EEEEF5;margin-bottom:5px;display:flex;align-items:center;gap:6px;
  }
  .isf-ti h4 s2{color:var(--tc);font-style:normal}
  .isf-ti p{font-size:11px;color:#66668A;line-height:1.7}
  .isf-formula{
    font-family:'Courier New',monospace;font-size:10px;
    background:#161622;border:1px solid #2A2A3A;
    border-radius:6px;padding:5px 10px;color:#6C63FF;
    margin-top:8px;display:inline-block;
  }

  @media(max-width:740px){
    .isf-main{padding:28px 18px 70px}
    .isf-hdr{padding:16px 18px}
    .isf-urow{grid-template-columns:1fr}
    .isf-vs{padding:8px 0}
    .isf-shero{grid-template-columns:1fr;gap:22px;padding:24px}
    .isf-mbars{min-width:unset}
  }
`;

if (!document.getElementById("isf-styles")) {
  const s = document.createElement("style");
  s.id = "isf-styles";
  s.textContent = RAW_CSS;
  document.head.appendChild(s);
}

const METHOD_META = {
  histogram:   { label: "Color Histogram",         icon: "◈", color: "#3B82F6", short: "HIST"  },
  ssim:        { label: "SSIM",                    icon: "◉", color: "#22D3A5", short: "SSIM"  },
  phash:       { label: "Perceptual Hash",          icon: "◆", color: "#F59E0B", short: "pHASH" },
  ahash:       { label: "Average Hash",             icon: "◇", color: "#FB923C", short: "aHASH" },
  dhash:       { label: "Difference Hash",          icon: "▣", color: "#F43F5E", short: "dHASH" },
  whash:       { label: "Wavelet Hash",             icon: "≋", color: "#8B5CF6", short: "wHASH" },
  edge:        { label: "Edge Similarity",          icon: "⊡", color: "#06B6D4", short: "EDGE"  },
  pixel:       { label: "Pixel PSNR",               icon: "⊞", color: "#84CC16", short: "PSNR"  },
  texture:     { label: "Texture LBP",              icon: "⊠", color: "#EAB308", short: "LBP"   },
  frequency:   { label: "Frequency FFT",            icon: "∿", color: "#EC4899", short: "FFT"   },
  spatial:     { label: "Spatial Layout",           icon: "▦", color: "#14B8A6", short: "SPAT"  },
  moment:      { label: "Hu Moments",               icon: "⊗", color: "#A78BFA", short: "HU"    },
  perspective: { label: "Perspective & Structure",  icon: "⊹", color: "#F97316", short: "PERSP" },
  keypoint:    { label: "Keypoint Matching",        icon: "⊕", color: "#38BDF8", short: "KPT"   },
  deep:        { label: "Deep CNN",                 icon: "◍", color: "#C084FC", short: "CNN"   },
};

const VERDICT_META = {
  "Near Identical":     { color: "#22D3A5", glow: "#22D3A522", label: "NEAR IDENTICAL"    },
  "Very Similar":       { color: "#5EEAD4", glow: "#5EEAD418", label: "VERY SIMILAR"      },
  "Moderately Similar": { color: "#F59E0B", glow: "#F59E0B22", label: "MODERATELY SIMILAR" },
  "Slightly Similar":   { color: "#FB923C", glow: "#FB923C22", label: "SLIGHTLY SIMILAR"  },
  "Very Different":     { color: "#EF4444", glow: "#EF444422", label: "VERY DIFFERENT"    },
};

const THEORY = [
  { id:"histogram",   label:"Color Histogram",         color:"#3B82F6", icon:"◈", body:"RGB + HSV + 2D joint histogram compared via Bhattacharyya coefficient.", formula:"BC = Σ √(h₁[i] × h₂[i])" },
  { id:"ssim",        label:"SSIM",                    color:"#22D3A5", icon:"◉", body:"Multi-scale Gaussian-windowed luminance, contrast & structure comparison.", formula:"SSIM = l(x,y) · c(x,y) · s(x,y)" },
  { id:"phash",       label:"pHash",                   color:"#F59E0B", icon:"◆", body:"256-bit DCT fingerprint with DC skipped for brightness robustness.", formula:"sim = 1 − (hamming / 256)" },
  { id:"ahash",       label:"aHash",                   color:"#FB923C", icon:"◇", body:"Pixels vs. image mean — fast brightness-normalised fingerprint.", formula:"bits = px > mean(img)" },
  { id:"dhash",       label:"dHash",                   color:"#F43F5E", icon:"▣", body:"Horizontal gradient direction hash — robust to brightness/contrast.", formula:"bits = px[i] > px[i+1]" },
  { id:"whash",       label:"wHash",                   color:"#8B5CF6", icon:"≋", body:"Haar wavelet LL band preserves multi-freq spatial information.", formula:"LL = Haar2D(img)[:8,:8]" },
  { id:"edge",        label:"Edge Similarity",         color:"#06B6D4", icon:"⊡", body:"Sobel magnitude IoU + cosine correlation + gradient direction agreement.", formula:"IoU = |E₁∩E₂| / |E₁∪E₂|" },
  { id:"pixel",       label:"Pixel PSNR",              color:"#84CC16", icon:"⊞", body:"Peak Signal-to-Noise Ratio — sensitive to exact pixel differences.", formula:"PSNR = 10·log₁₀(255²/MSE)" },
  { id:"texture",     label:"Texture LBP",             color:"#EAB308", icon:"⊠", body:"Local Binary Pattern histogram — captures micro-texture patterns.", formula:"LBP(p) = Σ s(gₙ−g_c)·2ⁿ" },
  { id:"frequency",   label:"Frequency FFT",           color:"#EC4899", icon:"∿", body:"Log-magnitude FFT spectrum cosine + histogram + radial energy profile.", formula:"F = FFT2(img), sim = cos(F₁,F₂)" },
  { id:"spatial",     label:"Spatial Layout",          color:"#14B8A6", icon:"▦", body:"8×8 grid mean colour and texture richness — captures composition.", formula:"score = Σ(1 − |μ₁−μ₂|/255√3)" },
  { id:"moment",      label:"Hu Moments",              color:"#A78BFA", icon:"⊗", body:"7 log-transformed Hu invariant moments — rotation/scale invariant.", formula:"hᵢ = f(μₚq) — 7 invariants" },
  { id:"perspective", label:"Perspective & Structure", color:"#F97316", icon:"⊹", body:"Angle histogram + rule-of-thirds grid + symmetry + vanishing point proxy.", formula:"sim = angle·quad·sym·vp·density" },
  { id:"keypoint",    label:"Keypoint Matching",       color:"#38BDF8", icon:"⊕", body:"Harris corners + normalised patch descriptors + Lowe's ratio test.", formula:"R = det(M) − k·trace(M)²" },
  { id:"deep",        label:"Deep CNN (MobileNetV2)",  color:"#C084FC", icon:"◍", body:"Cosine similarity of MobileNetV2 semantic feature embeddings.", formula:"cos(A,B) = A·B / (‖A‖×‖B‖)" },
];

/* ── DropZone ── */
function DropZone({ label, num, image, onImage }) {
  const ref = useRef();
  const [drag, setDrag] = useState(false);

  const pick = (file) => {
    if (!file || !file.type.startsWith("image/")) return;
    onImage({ file, url: URL.createObjectURL(file), name: file.name });
  };

  return (
    <div>
      <div className="isf-dz-label">
        <em>{num}</em>{label}
      </div>
      <div
        className={`isf-dz${drag ? " drag" : ""}`}
        onClick={() => !image && ref.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files[0]); }}
      >
        <div className="isf-scan" />
        {image ? (
          <>
            <img src={image.url} alt={label} />
            <div className="isf-fname">{image.name}</div>
            <div className="isf-dz-ov">
              <button
                className="isf-rm"
                onClick={(e) => { e.stopPropagation(); onImage(null); }}
              >
                ✕ Remove
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="isf-dz-ico">🖼</div>
            <div className="isf-dz-txt">Drop image or click to browse</div>
            <div className="isf-dz-hint">JPG · PNG · WEBP · GIF · BMP · TIFF</div>
          </>
        )}
      </div>
      <input
        ref={ref}
        type="file"
        accept="image/*"
        style={{ display: "none" }}
        onChange={(e) => pick(e.target.files[0])}
      />
    </div>
  );
}

/* ── ScoreRing ── */
function ScoreRing({ score, color }) {
  const r = 54;
  const circ = 2 * Math.PI * r;
  const dash = circ - (circ * score) / 100;
  return (
    <div className="isf-ring-wrap">
      <svg className="isf-ring-svg" viewBox="0 0 136 136">
        <circle className="isf-ring-bg" cx="68" cy="68" r={r} />
        <circle
          className="isf-ring-fg"
          cx="68" cy="68" r={r}
          stroke={color}
          style={{ "--dash": dash }}
        />
      </svg>
      <div className="isf-ring-inner">
        <div className="isf-ring-num" style={{ color }}>{Math.round(score)}</div>
        <div className="isf-ring-sub">/ 100</div>
      </div>
    </div>
  );
}

/* ── MethodCard ── */
function MethodCard({ id, method }) {
  const m = METHOD_META[id] || { label: id, icon: "●", color: "#888", short: id };
  return (
    <div className="isf-mc" style={{ "--mc": m.color, "--mclo": m.color + "18" }}>
      <div className="isf-mc-top2">
        <div className="isf-mc-icon2">{m.icon}</div>
        <div className="isf-mc-score2">{method.score.toFixed(1)}<span>%</span></div>
      </div>
      <div className="isf-mc-name2">{method.name}</div>
      <div className="isf-mc-bar-t">
        <div className="isf-mc-bar-f" style={{ "--w": `${method.score}%` }} />
      </div>
      <div className="isf-mc-desc2">{method.description}</div>
      <span className="isf-pill2">⏱ {method.complexity}</span>
      <span className="isf-pill2">💡 {method.use_case}</span>
    </div>
  );
}

/* ── Confidence color helper ── */
function confColor(c) {
  if (c === "High")   return "#22D3A5";
  if (c === "Medium") return "#F59E0B";
  return "#EF4444";
}

/* ── Main App ── */
export default function ImageSimilarityFinder() {
  const [img1, setImg1] = useState(null);
  const [img2, setImg2] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // ✅ NOW USES VERCEL SERVERLESS ROUTE — no localhost needed
  const API_URL = "/api/compare";
  const canCompare = img1 && img2 && !loading;

  const compare = async () => {
    if (!canCompare) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const form = new FormData();
      form.append("image1", img1.file);
      form.append("image2", img2.file);
      const res = await fetch(API_URL, { method: "POST", body: form });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        throw new Error(e.error || `Server error ${res.status}`);
      }
      setResult(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const verdict = result?.verdict;
  const vm = verdict ? (VERDICT_META[verdict] || VERDICT_META["Very Different"]) : null;

  const btnCls = loading
    ? "isf-btn isf-btn-load"
    : canCompare
    ? "isf-btn isf-btn-on"
    : "isf-btn isf-btn-off";

  return (
    <div className="isf">

      {/* ── Header ── */}
      <header className="isf-hdr">
        <div className="isf-logo">
          <div className="isf-logo-gem">⬡</div>
          <div>
            <div className="isf-logo-name">VisionMatch</div>
            <div className="isf-logo-tagline">IMAGE SIMILARITY ANALYZER</div>
          </div>
        </div>
        <div className="isf-hdr-badge">14 ALGORITHMS</div>
      </header>

      <main className="isf-main">

        {/* ── Hero ── */}
        <div className="isf-hero">
          <h1>Analyze Image Similarity</h1>
          <p>
            Upload two images and compare them across 14 algorithms — from color
            histograms and perceptual hashing to perspective detection and keypoint matching.
          </p>
        </div>

        {/* ── Upload Row ── */}
        <div className="isf-urow">
          <DropZone label="First Image"  num="01" image={img1} onImage={setImg1} />
          <div className="isf-vs">
            <div className="isf-vs-c">VS</div>
          </div>
          <DropZone label="Second Image" num="02" image={img2} onImage={setImg2} />
        </div>

        {/* ── Compare Button ── */}
        <button className={btnCls} onClick={compare} disabled={!canCompare || loading}>
          {loading
            ? <><span className="isf-spin" />Analyzing Images…</>
            : "→  Analyze Similarity"}
        </button>

        {/* ── Error ── */}
        {error && (
          <div className="isf-err">
            ⚠ {error}
          </div>
        )}

        {/* ── Results ── */}
        {result && vm && (
          <div className="isf-res">

            {/* Score Hero Card */}
            <div className="isf-shero" style={{ "--glow": vm.glow, "--lc": vm.color }}>

              <ScoreRing score={result.overall_score} color={vm.color} />

              <div>
                <div
                  className="isf-vchip"
                  style={{
                    color: vm.color,
                    borderColor: vm.color + "55",
                    background: vm.color + "14",
                  }}
                >
                  {vm.label}
                </div>
                <div className="isf-vtitle">{result.overall_score.toFixed(1)}% Similar</div>
                <div className="isf-vsub">
                  {result.methods_used} algorithms · Confidence:{" "}
                  <b style={{ color: confColor(result.confidence) }}>{result.confidence}</b>
                  {result.time_seconds && (
                    <span style={{ opacity: 0.5 }}> · {result.time_seconds}s</span>
                  )}
                </div>
                {result.analysis && (
                  <div className="isf-analysis">💡 {result.analysis}</div>
                )}
              </div>

              {/* Mini Bars */}
              <div className="isf-mbars">
                {Object.entries(result.results).map(([id, m]) => {
                  const meta = METHOD_META[id] || { short: id.toUpperCase().slice(0, 5), color: "#888" };
                  return (
                    <div className="isf-mrow" key={id}>
                      <div className="isf-mtop">
                        <span>{meta.short}</span>
                        <b style={{ "--c": meta.color }}>{m.score.toFixed(1)}%</b>
                      </div>
                      <div className="isf-mtrack">
                        <div
                          className="isf-mfill"
                          style={{ "--c": meta.color, "--w": `${m.score}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Method Cards */}
            <div className="isf-stitle">
              Algorithm Breakdown ({result.methods_used} methods)
            </div>
            <div className="isf-cgrid">
              {Object.entries(result.results).map(([id, method]) => (
                <MethodCard key={id} id={id} method={method} />
              ))}
            </div>

            {/* Theory Section */}
            <div className="isf-theory">
              <div className="isf-theory-ttl">📚  Theory Reference — for your report & viva</div>
              <div className="isf-tgrid">
                {THEORY.map((t) => (
                  <div className="isf-ti" key={t.id} style={{ "--tc": t.color }}>
                    <h4><s2>{t.icon}</s2>{t.label}</h4>
                    <p>{t.body}</p>
                    <div className="isf-formula">{t.formula}</div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}
      </main>
    </div>
  );
}