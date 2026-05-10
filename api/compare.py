"""
VisionMatch — Vercel Serverless Function  v4.0
POST /api/compare  →  multipart form with image1 + image2
"""

from http.server import BaseHTTPRequestHandler
import json, io, time, traceback, cgi
import numpy as np
from PIL import Image

# ─── Constants ────────────────────────────────────────────
COMPARE_SIZE = (256, 256)


# ─── Image Loading ────────────────────────────────────────
def load_image(data: bytes, size=COMPARE_SIZE) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    try:
        img.seek(0)
    except (AttributeError, EOFError):
        pass
    mode = img.mode
    if mode in ("RGBA", "LA", "PA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[3])
        img = bg
    elif mode == "P":
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    elif mode != "RGB":
        img = img.convert("RGB")
    return img.resize(size, Image.LANCZOS)


def to_gray(img):
    return np.array(img.convert("L"), dtype=np.float64)

def to_rgb(img):
    return np.array(img, dtype=np.float64)


# ─── Math Utils ───────────────────────────────────────────
def norm_hist(h):
    s = h.sum()
    return h.astype(np.float64) / (s + 1e-10)

def bhattacharyya(h1, h2):
    return float(np.clip(np.sum(np.sqrt(norm_hist(h1) * norm_hist(h2))), 0, 1))

def cosine_sim(a, b):
    a, b = a.flatten(), b.flatten()
    return float(np.clip(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10), -1, 1))

def clamp(v):
    return round(float(np.clip(v, 0, 100)), 2)

def gaussian_kernel_2d(size=11, sigma=1.5):
    k = np.arange(size) - size // 2
    g = np.exp(-k**2 / (2 * sigma**2))
    g /= g.sum()
    return np.outer(g, g)

def convolve2d(img, kernel):
    try:
        from scipy.ndimage import convolve
        return convolve(img.astype(np.float64), kernel, mode='reflect')
    except ImportError:
        kh, kw = kernel.shape
        ph, pw = kh // 2, kw // 2
        padded = np.pad(img, ((ph, ph), (pw, pw)), mode='reflect')
        out = np.zeros_like(img, dtype=np.float64)
        h, w = img.shape
        for i in range(kh):
            for j in range(kw):
                out += kernel[i, j] * padded[i:i+h, j:j+w]
        return out

def dct2(block):
    try:
        from scipy.fft import dct
        return dct(dct(block.T, norm='ortho').T, norm='ortho')
    except ImportError:
        try:
            from scipy.fftpack import dct
            return dct(dct(block.T, norm='ortho').T, norm='ortho')
        except ImportError:
            N, M = block.shape
            result = np.zeros_like(block, dtype=np.float64)
            ni = np.arange(N).reshape(-1, 1)
            mi = np.arange(M).reshape(1, -1)
            for u in range(N):
                for v in range(M):
                    result[u, v] = np.sum(
                        block
                        * np.cos(np.pi * u * (2*ni+1) / (2*N))
                        * np.cos(np.pi * v * (2*mi+1) / (2*M))
                    )
            return result


# ─── Method 1: Color Histogram ────────────────────────────
def color_histogram_similarity(img1, img2):
    a1, a2 = to_rgb(img1), to_rgb(img2)
    BINS = 128
    rgb_weights = [0.299, 0.587, 0.114]
    rgb_scores = []
    for ch in range(3):
        h1, _ = np.histogram(a1[:,:,ch], bins=BINS, range=(0,256))
        h2, _ = np.histogram(a2[:,:,ch], bins=BINS, range=(0,256))
        rgb_scores.append(bhattacharyya(h1, h2))
    rgb_score = sum(w*s for w,s in zip(rgb_weights, rgb_scores))
    hue_score = rgb_score
    try:
        hsv1 = np.array(img1.convert("HSV"), dtype=np.float64)
        hsv2 = np.array(img2.convert("HSV"), dtype=np.float64)
        h1h, _ = np.histogram(hsv1[:,:,0], bins=64, range=(0,256))
        h2h, _ = np.histogram(hsv2[:,:,0], bins=64, range=(0,256))
        h1s, _ = np.histogram(hsv1[:,:,1], bins=64, range=(0,256))
        h2s, _ = np.histogram(hsv2[:,:,1], bins=64, range=(0,256))
        hue_score = 0.7*bhattacharyya(h1h,h2h) + 0.3*bhattacharyya(h1s,h2s)
    except Exception:
        pass
    try:
        rg1,_,_ = np.histogram2d(a1[:,:,0].flatten(), a1[:,:,1].flatten(), bins=32, range=[[0,256],[0,256]])
        rg2,_,_ = np.histogram2d(a2[:,:,0].flatten(), a2[:,:,1].flatten(), bins=32, range=[[0,256],[0,256]])
        joint_score = bhattacharyya(rg1.flatten(), rg2.flatten())
    except Exception:
        joint_score = rgb_score
    try:
        def dominant(arr, n=8):
            px = arr.reshape(-1,3)
            q = np.linspace(0,100,n+1)
            cs = []
            for i in range(n):
                lo,hi = np.percentile(px[:,0],q[i]), np.percentile(px[:,0],q[i+1])
                m = (px[:,0]>=lo)&(px[:,0]<hi)
                if m.sum()>0: cs.append(px[m].mean(axis=0))
            return np.array(cs) if cs else np.zeros((1,3))
        dc1,dc2 = dominant(a1),dominant(a2)
        n = min(len(dc1),len(dc2))
        diffs = np.linalg.norm(dc1[:n]-dc2[:n], axis=1)
        dom_score = float(np.clip(1.0 - diffs.mean()/(255*np.sqrt(3)), 0, 1))
    except Exception:
        dom_score = rgb_score
    final = 0.30*rgb_score + 0.25*hue_score + 0.25*joint_score + 0.20*dom_score
    return clamp(final*100)


# ─── Method 2: SSIM ───────────────────────────────────────
def ssim_similarity(img1, img2):
    C1 = (0.01*255)**2; C2 = (0.03*255)**2
    kernel = gaussian_kernel_2d(11, 1.5)
    def ssim_ch(x, y):
        mu1=convolve2d(x,kernel); mu2=convolve2d(y,kernel)
        mu1sq,mu2sq,mu12 = mu1**2, mu2**2, mu1*mu2
        s1=np.maximum(convolve2d(x**2,kernel)-mu1sq,0)
        s2=np.maximum(convolve2d(y**2,kernel)-mu2sq,0)
        s12=convolve2d(x*y,kernel)-mu12
        num=(2*mu12+C1)*(2*s12+C2); den=(mu1sq+mu2sq+C1)*(s1+s2+C2)
        return float(np.mean(num/(den+1e-10)))
    g1,g2 = to_gray(img1), to_gray(img2)
    sf = ssim_ch(g1,g2)
    sh = sf
    try:
        g1h = np.array(img1.convert("L").resize((img1.width//2,img1.height//2),Image.LANCZOS),dtype=np.float64)
        g2h = np.array(img2.convert("L").resize((img2.width//2,img2.height//2),Image.LANCZOS),dtype=np.float64)
        sh = ssim_ch(g1h,g2h)
    except Exception:
        pass
    return clamp((0.6*sf+0.4*sh+1)/2*100)


# ─── Method 3: pHash ──────────────────────────────────────
def phash_similarity(img1, img2):
    HASH_SIZE=16; IMG_SIZE=64
    def compute(img):
        gray = img.convert("L").resize((IMG_SIZE,IMG_SIZE),Image.LANCZOS)
        block = np.array(gray,dtype=np.float32)
        d = dct2(block)
        low = d[:HASH_SIZE,:HASH_SIZE].flatten()
        return low > np.median(low[1:])
    return clamp(np.mean(compute(img1)==compute(img2))*100)


# ─── Method 4: aHash ──────────────────────────────────────
def ahash_similarity(img1, img2):
    SIZE=16
    def compute(img):
        a = np.array(img.convert("L").resize((SIZE,SIZE),Image.LANCZOS),dtype=np.float32)
        return a > a.mean()
    return clamp(np.mean(compute(img1)==compute(img2))*100)


# ─── Method 5: dHash ──────────────────────────────────────
def dhash_similarity(img1, img2):
    SIZE=16
    def compute(img):
        a = np.array(img.convert("L").resize((SIZE+1,SIZE),Image.LANCZOS),dtype=np.float32)
        return a[:,:-1] > a[:,1:]
    return clamp(np.mean(compute(img1)==compute(img2))*100)


# ─── Method 6: wHash ──────────────────────────────────────
def whash_similarity(img1, img2):
    SIZE=64; HASH_SIZE=8
    def haar_2d(arr):
        out = arr.copy().astype(np.float64)
        h,w = out.shape
        for i in range(h):
            row=out[i,:]; out[i,:w//2]=(row[0::2]+row[1::2])/2; out[i,w//2:]=(row[0::2]-row[1::2])/2
        for j in range(w):
            col=out[:,j]; out[:h//2,j]=(col[0::2]+col[1::2])/2; out[h//2:,j]=(col[0::2]-col[1::2])/2
        return out
    def compute(img):
        gray = np.array(img.convert("L").resize((SIZE,SIZE),Image.LANCZOS),dtype=np.float64)
        ll = haar_2d(gray)[:HASH_SIZE,:HASH_SIZE]
        return ll > np.median(ll)
    return clamp(np.mean(compute(img1)==compute(img2))*100)


# ─── Method 7: Edge Similarity ────────────────────────────
def edge_similarity(img1, img2):
    KX=np.array([[-1,0,1],[-2,0,2],[-1,0,1]],dtype=np.float64); KY=KX.T
    def edges(img):
        g=to_gray(img); gx=convolve2d(g,KX); gy=convolve2d(g,KY)
        mag=np.sqrt(gx**2+gy**2); mag/=(mag.max()+1e-10)
        return mag, np.arctan2(gy,gx+1e-10)
    e1,d1=edges(img1); e2,d2=edges(img2)
    b1,b2=e1>0.10, e2>0.10
    iou=float(np.sum(b1&b2)/(np.sum(b1|b2)+1e-10))
    mag_cos=(cosine_sim(e1,e2)+1)/2
    mask=b1&b2
    if mask.sum()>10:
        diff=np.abs(d1[mask]-d2[mask]); diff=np.minimum(diff,np.pi-diff)
        dir_score=float(1.0-diff.mean()/(np.pi/2))
    else:
        dir_score=0.5
    return clamp((0.40*iou+0.35*mag_cos+0.25*dir_score)*100)


# ─── Method 8: Pixel PSNR ─────────────────────────────────
def pixel_similarity(img1, img2):
    a1,a2=to_rgb(img1),to_rgb(img2)
    mse=np.mean((a1-a2)**2)
    if mse<1e-10: return 100.0
    psnr=10*np.log10(255.0**2/mse)
    return clamp(np.clip((psnr-10)/45.0,0,1)*100)


# ─── Method 9: Texture LBP ────────────────────────────────
def texture_similarity(img1, img2):
    def lbp(gray):
        h,w=gray.shape; offsets=[(-1,-1),(-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1)]
        center=gray[1:-1,1:-1]; code=np.zeros_like(center,dtype=np.uint8)
        for bit,(dy,dx) in enumerate(offsets):
            nb=gray[1+dy:h-1+dy,1+dx:w-1+dx]; code|=((nb>=center).astype(np.uint8)<<bit)
        out=np.zeros((h,w),dtype=np.uint8); out[1:-1,1:-1]=code; return out
    g1,g2=to_gray(img1).astype(np.uint8),to_gray(img2).astype(np.uint8)
    l1,l2=lbp(g1),lbp(g2)
    h1,_=np.histogram(l1,bins=256,range=(0,256)); h2,_=np.histogram(l2,bins=256,range=(0,256))
    return clamp(bhattacharyya(h1,h2)*100)


# ─── Method 10: Frequency FFT ─────────────────────────────
def frequency_similarity(img1, img2):
    def fft_feat(img):
        g=to_gray(img); fft=np.fft.fft2(g); mag=np.abs(np.fft.fftshift(fft))
        mag=np.log1p(mag); mag/=(mag.max()+1e-10); return mag
    f1,f2=fft_feat(img1),fft_feat(img2)
    cos=(cosine_sim(f1,f2)+1)/2
    h1,_=np.histogram(f1,bins=128,range=(0,1)); h2,_=np.histogram(f2,bins=128,range=(0,1))
    hist=bhattacharyya(h1,h2)
    def radial(mag):
        cy,cx=np.array(mag.shape)//2; y,x=np.ogrid[:mag.shape[0],:mag.shape[1]]
        r=np.sqrt((x-cx)**2+(y-cy)**2).astype(int); r_max=min(cy,cx)
        return np.array([mag[r==i].mean() if (r==i).any() else 0 for i in range(r_max)])
    rp1,rp2=radial(f1),radial(f2); mn=min(len(rp1),len(rp2))
    rad=(cosine_sim(rp1[:mn],rp2[:mn])+1)/2 if mn>0 else 0.5
    return clamp((0.40*cos+0.30*hist+0.30*rad)*100)


# ─── Method 11: Spatial Layout ────────────────────────────
def spatial_similarity(img1, img2):
    GRID=8; a1,a2=to_rgb(img1),to_rgb(img2); h,w,_=a1.shape; ch,cw=h//GRID,w//GRID
    mean_scores,std_scores=[],[]
    for i in range(GRID):
        for j in range(GRID):
            c1=a1[i*ch:(i+1)*ch,j*cw:(j+1)*cw]; c2=a2[i*ch:(i+1)*ch,j*cw:(j+1)*cw]
            d=np.linalg.norm(c1.mean(axis=(0,1))-c2.mean(axis=(0,1)))/(255*np.sqrt(3))
            mean_scores.append(1.0-d)
            s1,s2=c1.std(),c2.std()
            std_scores.append(1.0-abs(s1-s2)/(max(s1,s2,1e-5)))
    return clamp((0.70*np.mean(mean_scores)+0.30*np.mean(std_scores))*100)


# ─── Method 12: Hu Moments ────────────────────────────────
def moment_similarity(img1, img2):
    def hu(img):
        gray=to_gray(img); gray/=(gray.max()+1e-10)
        h,w=gray.shape; y,x=np.mgrid[0:h,0:w]; m00=gray.sum()+1e-10
        xb=(x*gray).sum()/m00; yb=(y*gray).sum()/m00; xc,yc=x-xb,y-yb
        def mu(p,q): return (xc**p*yc**q*gray).sum()/m00
        mu20=mu(2,0);mu02=mu(0,2);mu11=mu(1,1);mu30=mu(3,0);mu03=mu(0,3);mu21=mu(2,1);mu12=mu(1,2)
        h1=mu20+mu02; h2=(mu20-mu02)**2+4*mu11**2; h3=(mu30-3*mu12)**2+(3*mu21-mu03)**2
        h4=(mu30+mu12)**2+(mu21+mu03)**2
        h5=((mu30-3*mu12)*(mu30+mu12)*((mu30+mu12)**2-3*(mu21+mu03)**2)+(3*mu21-mu03)*(mu21+mu03)*(3*(mu30+mu12)**2-(mu21+mu03)**2))
        h6=((mu20-mu02)*((mu30+mu12)**2-(mu21+mu03)**2)+4*mu11*(mu30+mu12)*(mu21+mu03))
        h7=((3*mu21-mu03)*(mu30+mu12)*((mu30+mu12)**2-3*(mu21+mu03)**2)-(mu30-3*mu12)*(mu21+mu03)*(3*(mu30+mu12)**2-(mu21+mu03)**2))
        moments=np.array([h1,h2,h3,h4,h5,h6,h7])
        with np.errstate(divide='ignore',invalid='ignore'):
            return np.where(moments!=0,np.sign(moments)*np.log10(np.abs(moments)+1e-10),0)
    m1,m2=hu(img1),hu(img2)
    diff=np.abs(m1-m2); scale=np.abs(m1)+np.abs(m2)+1e-10
    return clamp((1.0-np.mean(np.clip(diff/scale,0,1)))*100)


# ─── Method 13: Perspective & Structure ───────────────────
def perspective_similarity(img1, img2):
    def sobel_edges(img):
        g=to_gray(img); KX=np.array([[-1,0,1],[-2,0,2],[-1,0,1]],dtype=np.float64); KY=KX.T
        gx=convolve2d(g,KX); gy=convolve2d(g,KY); mag=np.sqrt(gx**2+gy**2)
        mag/=(mag.max()+1e-10); dirn=np.arctan2(gy,gx+1e-10); return mag,dirn,gx,gy
    def angle_hist(mag,dirn,bins=18):
        mask=mag>0.08
        if mask.sum()<10: return np.ones(bins)/bins
        angles=((dirn[mask]+np.pi)/(2*np.pi)*bins).astype(int)%bins
        h=np.bincount(angles,minlength=bins).astype(np.float64); return h/(h.sum()+1e-10)
    mag1,dir1,gx1,gy1=sobel_edges(img1); mag2,dir2,gx2,gy2=sobel_edges(img2)
    ah1,ah2=angle_hist(mag1,dir1),angle_hist(mag2,dir2)
    shifts=[np.roll(ah1,k) for k in range(len(ah1))]
    angle_sim=float(max(np.dot(s,ah2)/(np.linalg.norm(s)*np.linalg.norm(ah2)+1e-10) for s in shifts))
    angle_sim=(angle_sim+1)/2
    def quadrant_profile(img,rows=3,cols=3):
        a=to_gray(img); h,w=a.shape; rh,cw=h//rows,w//cols; profile=[]
        for i in range(rows):
            for j in range(cols):
                cell=a[i*rh:(i+1)*rh,j*cw:(j+1)*cw]; profile.extend([cell.mean()/255,cell.std()/128])
        return np.array(profile)
    qp1,qp2=quadrant_profile(img1),quadrant_profile(img2); quad_sim=(cosine_sim(qp1,qp2)+1)/2
    def symmetry_score(img):
        g=to_gray(img); h,w=g.shape; lft=g[:,:w//2]; rgt=np.fliplr(g[:,w-w//2:])
        mn=min(lft.shape[1],rgt.shape[1]); hs=float(1.0-np.mean(np.abs(lft[:,:mn]-rgt[:,:mn]))/255)
        top=g[:h//2,:]; bot=np.flipud(g[h-h//2:,:]); mn2=min(top.shape[0],bot.shape[0])
        vs=float(1.0-np.mean(np.abs(top[:mn2]-bot[:mn2]))/255); return hs,vs
    hs1,vs1=symmetry_score(img1); hs2,vs2=symmetry_score(img2)
    sym_score=(1-abs(hs1-hs2)+1-abs(vs1-vs2))/2
    def vp_score(gx,gy,mag):
        mask=mag>0.08
        if mask.sum()<10: return 0.5
        return float(np.mean(np.abs(gx[mask])>np.abs(gy[mask])))
    vp_sim=1.0-abs(vp_score(gx1,gy1,mag1)-vp_score(gx2,gy2,mag2))
    def density_profile(img):
        g=to_gray(img); h,w=g.shape; cy,cx=h//2,w//2; d4,d4w=h//4,w//4
        zones=[g[:cy,:cx].mean(),g[:cy,cx:].mean(),g[cy:,:cx].mean(),g[cy:,cx:].mean(),g[d4:3*d4,d4w:3*d4w].mean()]
        return np.array(zones)/255
    dp1,dp2=density_profile(img1),density_profile(img2); dens_sim=(cosine_sim(dp1,dp2)+1)/2
    return clamp((0.25*angle_sim+0.25*quad_sim+0.20*sym_score+0.15*vp_sim+0.15*dens_sim)*100)


# ─── Method 14: Keypoint Matching ─────────────────────────
def keypoint_similarity(img1, img2):
    def harris_corners(gray, k=0.05, threshold=0.01, max_pts=150):
        KX=np.array([[-1,0,1],[-2,0,2],[-1,0,1]],dtype=np.float64); KY=KX.T
        Ix=convolve2d(gray/255.0,KX); Iy=convolve2d(gray/255.0,KY)
        w=gaussian_kernel_2d(5,1.0); Ixx=convolve2d(Ix**2,w); Iyy=convolve2d(Iy**2,w); Ixy=convolve2d(Ix*Iy,w)
        det=Ixx*Iyy-Ixy**2; trace=Ixx+Iyy; R=det-k*trace**2
        R_thresh=R*(R>threshold*R.max()); padded=np.pad(R_thresh,1,mode='constant')
        local_max=np.zeros_like(R_thresh,dtype=bool)
        for dy in range(-1,2):
            for dx in range(-1,2):
                if dy==0 and dx==0: continue
                local_max|=R_thresh<padded[1+dy:1+dy+R_thresh.shape[0],1+dx:1+dx+R_thresh.shape[1]]
        pts=np.argwhere((~local_max)&(R_thresh>0))
        responses=R_thresh[pts[:,0],pts[:,1]]; order=np.argsort(-responses)[:max_pts]
        return pts[order]
    def patch_descriptor(gray,pts,patch=9):
        half=patch//2; h,w=gray.shape; descs=[]; valid=[]
        for (y,x) in pts:
            if y-half<0 or y+half>=h or x-half<0 or x+half>=w: continue
            p=gray[y-half:y+half+1,x-half:x+half+1].flatten().astype(np.float64)
            p=(p-p.mean())/(p.std()+1e-10); descs.append(p); valid.append((y,x))
        return (np.array(descs) if descs else np.zeros((1,patch*patch))), valid
    g1,g2=to_gray(img1),to_gray(img2)
    pts1,pts2=harris_corners(g1),harris_corners(g2)
    if len(pts1)==0 or len(pts2)==0: return 50.0
    d1,v1=patch_descriptor(g1,pts1); d2,v2=patch_descriptor(g2,pts2)
    if len(d1)==0 or len(d2)==0: return 50.0
    matches=0; RATIO=0.80
    for desc in d1:
        sims=np.dot(d2,desc)/(np.linalg.norm(d2,axis=1)*np.linalg.norm(desc)+1e-10)
        sorted_sims=np.sort(sims)[::-1]; best=sorted_sims[0]
        second=sorted_sims[1] if len(sorted_sims)>1 else 0.0
        if best>0 and (second<1e-10 or best/(abs(second)+1e-10)>(1/RATIO)): matches+=1
    match_rate=matches/(max(len(d1),len(d2))+1e-10)
    count_sim=min(len(pts1),len(pts2))/(max(len(pts1),len(pts2))+1e-10)
    return clamp((0.75*match_rate+0.25*count_sim)*100)


# ─── Scoring & Verdict ────────────────────────────────────
BASE_WEIGHTS = {
    "histogram":0.08,"ssim":0.12,"phash":0.09,"ahash":0.05,"dhash":0.05,
    "whash":0.05,"edge":0.10,"pixel":0.10,"texture":0.08,"frequency":0.07,
    "spatial":0.07,"moment":0.04,"perspective":0.10,"keypoint":0.00,
}

def compute_weighted_score(results):
    weights=dict(BASE_WEIGHTS); total_w=total_s=0.0
    for key,method in results.items():
        w=weights.get(key,0.04); total_s+=method["score"]*w; total_w+=w
    return clamp(total_s/(total_w+1e-10))

def get_verdict(score):
    if score>=92: return "Near Identical"
    if score>=75: return "Very Similar"
    if score>=55: return "Moderately Similar"
    if score>=35: return "Slightly Similar"
    return "Very Different"

def get_confidence(results):
    std=np.std([v["score"] for v in results.values()])
    if std<8: return "High"
    if std<18: return "Medium"
    return "Low"

def get_analysis(results, overall):
    sc={k:v["score"] for k,v in results.items()}
    hi=max(sc,key=sc.get); lo=min(sc,key=sc.get); lines=[]
    if sc[hi]-sc[lo]>35: lines.append(f"Mixed signals: {hi} shows high similarity while {lo} is low.")
    if sc.get("ssim",0)>80 and sc.get("histogram",0)<50: lines.append("Structure matches but colors differ significantly.")
    if sc.get("histogram",0)>80 and sc.get("ssim",0)<50: lines.append("Similar colors but different layout or structure.")
    if sc.get("phash",0)>92: lines.append("Perceptual hash match: likely same source image.")
    if sc.get("pixel",0)>88: lines.append("Near pixel-perfect match detected.")
    if sc.get("perspective",0)>80 and sc.get("ssim",0)<55: lines.append("Similar perspective/composition but different content.")
    if sc.get("keypoint",0)>75: lines.append("Strong keypoint matches: images share key structural features.")
    if sc.get("texture",0)<40: lines.append("Textures are quite different.")
    if not lines: lines.append("All methods agree — result is reliable.")
    return " ".join(lines)


# ─── Vercel Handler ───────────────────────────────────────
def parse_multipart(body: bytes, content_type: str):
    environ = {
        'REQUEST_METHOD': 'POST',
        'CONTENT_TYPE': content_type,
        'CONTENT_LENGTH': str(len(body)),
    }
    fp = io.BytesIO(body)
    form = cgi.FieldStorage(fp=fp, environ=environ, keep_blank_values=True)
    return form


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        t_start = time.time()
        try:
            content_type = self.headers.get('Content-Type', '')
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)

            form = parse_multipart(body, content_type)

            if 'image1' not in form or 'image2' not in form:
                self._json(400, {"error": "Please upload both image1 and image2"})
                return

            b1 = form['image1'].file.read()
            b2 = form['image2'].file.read()

            if not b1 or not b2:
                self._json(400, {"error": "One or both files are empty."})
                return

            img1 = load_image(b1)
            img2 = load_image(b2)

            METHODS = [
                ("histogram","Color Histogram",lambda:color_histogram_similarity(img1,img2),
                 "Bhattacharyya coefficient over RGB+HSV+2D joint+dominant color.","O(n) — Very Fast","Color-based scene matching"),
                ("ssim","Structural Similarity (SSIM)",lambda:ssim_similarity(img1,img2),
                 "Multi-scale Gaussian-windowed SSIM measuring luminance, contrast, structure.","O(n) — Fast","Edit detection"),
                ("phash","Perceptual Hash (pHash)",lambda:phash_similarity(img1,img2),
                 "256-bit DCT fingerprint — brightness robust.","O(1) — Instant","Near-duplicate detection"),
                ("ahash","Average Hash (aHash)",lambda:ahash_similarity(img1,img2),
                 "Pixels vs. mean. Fast brightness-normalised fingerprint.","O(1) — Instant","Quick duplicate screening"),
                ("dhash","Difference Hash (dHash)",lambda:dhash_similarity(img1,img2),
                 "Horizontal gradient direction hash. Robust to brightness/contrast.","O(1) — Instant","Edge-aware duplicate"),
                ("whash","Wavelet Hash (wHash)",lambda:whash_similarity(img1,img2),
                 "Haar wavelet LL band preserves multi-frequency spatial info.","O(n log n) — Fast","Frequency-aware matching"),
                ("edge","Edge Similarity",lambda:edge_similarity(img1,img2),
                 "Sobel gradient IoU + cosine + direction alignment.","O(n) — Fast","Shape and structure"),
                ("pixel","Pixel PSNR",lambda:pixel_similarity(img1,img2),
                 "Peak Signal-to-Noise Ratio mapped 0–100.","O(n) — Very Fast","Exact image verification"),
                ("texture","Texture (LBP)",lambda:texture_similarity(img1,img2),
                 "Local Binary Pattern histogram — micro-texture patterns.","O(n) — Fast","Material texture matching"),
                ("frequency","Frequency Domain (FFT)",lambda:frequency_similarity(img1,img2),
                 "Log-magnitude FFT cosine + histogram + radial energy.","O(n log n) — Fast","Periodic patterns"),
                ("spatial","Spatial Layout",lambda:spatial_similarity(img1,img2),
                 "8×8 grid mean colour and texture richness comparison.","O(n) — Fast","Composition similarity"),
                ("moment","Hu Moments",lambda:moment_similarity(img1,img2),
                 "7 Hu invariant moments — rotation/scale invariant shape.","O(n) — Fast","Shape-based matching"),
                ("perspective","Perspective & Structure",lambda:perspective_similarity(img1,img2),
                 "Angle histogram + quadrant profile + symmetry + vanishing-point proxy.","O(n) — Fast","Geometric composition"),
                ("keypoint","Keypoint Matching",lambda:keypoint_similarity(img1,img2),
                 "Harris corners + patch descriptors + Lowe's ratio test.","O(n²) — Moderate","Local feature matching"),
            ]

            results = {}
            for key, name, fn, desc, complexity, use_case in METHODS:
                try:
                    results[key] = {
                        "name": name, "score": fn(),
                        "description": desc, "complexity": complexity, "use_case": use_case,
                    }
                except Exception as e:
                    print(f"[{key} ERROR] {e}")

            if not results:
                self._json(500, {"error": "All comparison methods failed."})
                return

            overall = compute_weighted_score(results)
            self._json(200, {
                "success": True,
                "results": results,
                "overall_score": overall,
                "verdict": get_verdict(overall),
                "confidence": get_confidence(results),
                "analysis": get_analysis(results, overall),
                "methods_used": len(results),
                "time_seconds": round(time.time() - t_start, 3),
            })

        except Exception as e:
            traceback.print_exc()
            self._json(500, {"error": f"Unexpected error: {str(e)}"})

    def _json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass
