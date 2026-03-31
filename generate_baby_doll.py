#!/usr/bin/env python3
"""
Realistic baby doll in swaddled blanket — dollhouse 1:12 scale.

Technique: Marching cubes on a procedurally textured Signed Distance Field (SDF).
This is the same approach used for organic 3D models on Thingiverse/Printables:

  - Smooth-union / smooth-subtract blend ALL features (no hard CSG seams)
  - Gaussian random noise fields simulate fabric folds and skin micro-texture
  - Marching cubes extracts the iso-surface at high resolution
  - Result: organic, sculpted-looking geometry with realistic cloth detail

Dimensions: 1:12 dollhouse scale (~50 mm total length)
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from skimage import measure
import struct, os, time

t0 = time.time()

# ─────────────────────────────────────────────────────────────────────────────
# GRID SETUP
# ─────────────────────────────────────────────────────────────────────────────
VOXEL = 0.32          # mm per voxel — higher resolution than typical CAD export

xs = np.arange(-15.5, 15.5, VOXEL)
ys = np.arange(-27.0, 49.0, VOXEL)
zs = np.arange(-3.0,  28.0, VOXEL)
X, Y, Z = np.meshgrid(xs, ys, zs, indexing='ij')
print(f"Grid {X.shape}  ({X.size/1e6:.1f}M voxels)")


# ─────────────────────────────────────────────────────────────────────────────
# SDF PRIMITIVES  (all vectorised over the full grid)
# ─────────────────────────────────────────────────────────────────────────────

def sphere(cx, cy, cz, r):
    return np.sqrt((X-cx)**2 + (Y-cy)**2 + (Z-cz)**2) - r

def ellipsoid(cx, cy, cz, ax, ay, az):
    """
    Scaled-sphere ellipsoid.  Not unit-gradient, but stable and correct
    sign everywhere (negative inside, zero on surface, positive outside).
    Distances are scaled by the smallest half-axis so blend-radii k are
    roughly in mm units, which is all we need for organic smooth ops.
    """
    r = np.sqrt(((X-cx)/ax)**2 + ((Y-cy)/ay)**2 + ((Z-cz)/az)**2)
    scale = min(ax, ay, az)
    return (r - 1.0) * scale

def rounded_box(cx, cy, cz, hx, hy, hz, r):
    """Signed distance to rounded box (half-extents hx,hy,hz, corner radius r)."""
    qx = np.abs(X-cx) - hx + r
    qy = np.abs(Y-cy) - hy + r
    qz = np.abs(Z-cz) - hz + r
    return (np.sqrt(np.maximum(qx,0)**2 + np.maximum(qy,0)**2 + np.maximum(qz,0)**2)
            + np.minimum(np.maximum(qx, np.maximum(qy, qz)), 0) - r)

def capsule(ax, ay, az, bx, by, bz, r):
    """Capsule (thick line segment a→b, radius r)."""
    abx, aby, abz = bx-ax, by-ay, bz-az
    t = np.clip(((X-ax)*abx+(Y-ay)*aby+(Z-az)*abz) /
                (abx**2+aby**2+abz**2+1e-12), 0, 1)
    px = X-ax - t*abx;  py = Y-ay - t*aby;  pz = Z-az - t*abz
    return np.sqrt(px**2+py**2+pz**2) - r

def smin(a, b, k=2.5):
    """Smooth boolean union (k = blend radius in mm). Quilez 2013 formula."""
    h = np.clip(0.5 + 0.5*(b-a)/k, 0, 1)
    return b + h*(a-b) - k*h*(1-h)   # mix(b,a,h) — picks min, NOT mix(a,b,h)

def ssub(a, b, k=1.8):
    """Smooth boolean subtraction of b from a."""
    return -smin(-a, b, k)


# ─────────────────────────────────────────────────────────────────────────────
# PROCEDURAL TEXTURE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def gnoise(sigma_vox, amplitude, seed):
    """
    Gaussian-smoothed white noise — produces band-limited organic bumps.
    sigma_vox: smoothing kernel in voxels (controls bump wavelength).
    amplitude: peak-to-peak displacement in mm.
    """
    rng = np.random.default_rng(seed)
    raw = rng.standard_normal(X.shape).astype(np.float32)
    smoothed = gaussian_filter(raw, sigma=sigma_vox)
    # Normalise to [-1, 1] then scale
    mx = np.max(np.abs(smoothed)) + 1e-12
    return (smoothed / mx) * amplitude


# ─────────────────────────────────────────────────────────────────────────────
# 1. SWADDLED BODY
#    Rounded box: 17 W × 37 L × 12 H mm, sitting on z = 0.
#    Centre at (0, 0, 6).
# ─────────────────────────────────────────────────────────────────────────────

d_body = rounded_box(0, 0, 6.0,  hx=8.0, hy=18.0, hz=5.8,  r=2.5)

# ── Fabric texture ────────────────────────────────────────────────────────────
# Three scales of Gaussian noise simulate:
#   large   (~8 vox ≈ 2.6 mm)  = major cloth folds
#   medium  (~3 vox ≈ 1.0 mm)  = secondary wrinkles
#   fine    (~1.5 vox ≈ 0.5 mm) = weave micro-texture

n_large  = gnoise(sigma_vox=8,   amplitude=0.60, seed=1)
n_medium = gnoise(sigma_vox=3,   amplitude=0.22, seed=2)
n_fine   = gnoise(sigma_vox=1.5, amplitude=0.09, seed=3)

# Directional fold bias: fabric tends to fold along the short axis (X),
# so amplify noise variation in X by modulating with a slow sine in Y.
fold_bias = 1.0 + 0.45 * np.sin(Y * 2*np.pi / 11.0)   # ~11 mm period
side_bias = 1.0 + 0.35 * (np.abs(X) / 8.0)             # edges wrinkle more

# Top of blanket is pulled tight → smooth it there
tight_top = np.clip(1.0 - (Z - 9.5) / 3.0, 0.0, 1.0)  # 0 at very top, 1 below

fabric = (n_large + n_medium + n_fine) * fold_bias * side_bias * tight_top

# Only displace where we are near the body surface (|d| < 4 mm)
body_weight = np.clip(1.0 - np.abs(d_body) / 4.0, 0, 1)
d_body = d_body + fabric * body_weight

# ── Chest fold ridge ──────────────────────────────────────────────────────────
# Raised blanket edge near y = +10, modelled as a capsule.
d_fold_ridge = capsule(-8, 10, 12.2,  8, 10, 12.2,  r=1.5)
d_body = smin(d_body, d_fold_ridge, k=1.2)


# ─────────────────────────────────────────────────────────────────────────────
# 2. NECK
#    Capsule bridging body end (y ≈ +18) to head start (y ≈ +20).
# ─────────────────────────────────────────────────────────────────────────────

d_neck = capsule(0, 17.5, 8.5,  0, 22.0, 9.5,  r=4.2)


# ─────────────────────────────────────────────────────────────────────────────
# 3. HEAD
#    Sphere r = 8 mm, centre (0, 27, 10).
#    Face tilted UPWARD (+Z) and slightly toward +Y so features are
#    visible from above when the baby is lying in the dollhouse.
# ─────────────────────────────────────────────────────────────────────────────

HR = 8.0
HCX, HCY, HCZ = 0.0, 27.0, 10.0

d_head = sphere(HCX, HCY, HCZ, HR)

# Very subtle skin micro-texture (σ ≈ 0.8 mm, amplitude 0.07 mm)
skin_n = gnoise(sigma_vox=2.5, amplitude=0.07, seed=7)
head_weight = np.clip(1.0 - np.abs(d_head) / 3.0, 0, 1)
d_head = d_head + skin_n * head_weight

# ── Chubby cheeks ─────────────────────────────────────────────────────────────
for xs_ in (+1, -1):
    d_head = smin(d_head, ellipsoid(xs_*4.0, HCY+5.0, HCZ-2.0, 3.5, 2.8, 3.0), k=2.0)

# Chin
d_head = smin(d_head, ellipsoid(0, HCY+6.2, HCZ-4.5, 2.8, 2.2, 1.8), k=1.8)


# ─────────────────────────────────────────────────────────────────────────────
# 4. FACE FEATURES
#    Face normal ≈ (0, +0.38, +0.92) → face points mostly up, tilted toward +Y.
#    Face surface centre: (0, HCY + 0.38*HR, HCZ + 0.92*HR) ≈ (0, 30, 17.4)
# ─────────────────────────────────────────────────────────────────────────────

# Convenience: face reference point
FX = HCX
FY = HCY + 3.0     # tilted-forward face centre Y
FZ = HCZ + HR - 1.5  # near top of sphere

# ── Eye sockets (shallow oval depressions) ────────────────────────────────────
for xs_ in (+1, -1):
    d_sock = ellipsoid(xs_*2.7, FY-0.5, FZ+1.3,  ax=2.5, ay=0.9, az=1.8)
    d_head = ssub(d_head, d_sock, k=1.2)

# ── Eyelids (thin raised arcs) ────────────────────────────────────────────────
for xs_ in (+1, -1):
    d_lid = ellipsoid(xs_*2.7, FY-0.2, FZ+1.6,  ax=2.3, ay=0.7, az=0.9)
    d_head = smin(d_head, d_lid, k=1.0)

# ── Nose bridge (slight ridge between brows) ──────────────────────────────────
d_head = smin(d_head, ellipsoid(0, FY+0.0, FZ+0.6, 0.9, 0.65, 1.9), k=1.2)

# ── Nose tip (small button nose, typical newborn) ─────────────────────────────
d_head = smin(d_head, ellipsoid(0, FY+1.2, FZ-0.4, 1.7, 1.3, 1.5), k=1.3)

# Nostril hints
for xs_ in (+1, -1):
    d_nost = ellipsoid(xs_*0.9, FY+1.7, FZ-0.9,  ax=0.75, ay=0.75, az=0.7)
    d_head = ssub(d_head, d_nost, k=0.8)

# ── Upper lip (cupid's bow) ───────────────────────────────────────────────────
for xs_ in (+1, -1):
    d_head = smin(d_head, ellipsoid(xs_*1.1, FY+1.1, FZ-2.0, 1.3, 0.85, 0.85), k=1.0)

# ── Lower lip ─────────────────────────────────────────────────────────────────
d_head = smin(d_head, ellipsoid(0, FY+1.05, FZ-3.1, 2.6, 0.95, 0.95), k=1.0)

# ── Mouth crease (thin groove) ────────────────────────────────────────────────
d_mouth_cut = ellipsoid(0, FY+1.45, FZ-2.55,  ax=3.0, ay=0.45, az=0.35)
d_head = ssub(d_head, d_mouth_cut, k=0.7)

# ── Philtrum ──────────────────────────────────────────────────────────────────
d_head = ssub(d_head, ellipsoid(0, FY+1.25, FZ-1.4, 0.55, 0.5, 1.3), k=0.8)

# ── Ears (flat, flush with head sides) ───────────────────────────────────────
for xs_ in (+1, -1):
    # Pinna: thin oval barely proud of the sphere
    d_pinna = ellipsoid(xs_*(HR-0.5), HCY-1.5, HCZ,  ax=0.85, ay=1.5, az=2.2)
    d_head = smin(d_head, d_pinna, k=1.0)
    # Concha depression
    d_concha = ellipsoid(xs_*(HR+0.1), HCY-1.5, HCZ,  ax=0.6, ay=0.9, az=1.3)
    d_head = ssub(d_head, d_concha, k=0.7)
    # Earlobe
    d_head = smin(d_head, ellipsoid(xs_*(HR-0.8), HCY-1.0, HCZ-2.3, 0.7, 0.95, 1.0), k=1.0)


# ─────────────────────────────────────────────────────────────────────────────
# 5. ASSEMBLE FULL FIELD
# ─────────────────────────────────────────────────────────────────────────────

d_head_neck = smin(d_head, d_neck, k=2.5)
d_full = smin(d_head_neck, d_body, k=2.0)

print(f"SDF built  ({time.time()-t0:.1f}s)")


# ─────────────────────────────────────────────────────────────────────────────
# 6. MARCHING CUBES  (iso-surface at d = 0)
# ─────────────────────────────────────────────────────────────────────────────

t1 = time.time()
verts, faces, normals, _ = measure.marching_cubes(d_full, level=0.0, spacing=(VOXEL, VOXEL, VOXEL))

# Shift vertices to world coordinates
verts[:, 0] += xs[0]
verts[:, 1] += ys[0]
verts[:, 2] += zs[0]

print(f"Marching cubes: {len(verts):,} vertices, {len(faces):,} triangles  ({time.time()-t1:.1f}s)")


# ─────────────────────────────────────────────────────────────────────────────
# 7. EXPORT BINARY STL
# ─────────────────────────────────────────────────────────────────────────────

def write_binary_stl(path, verts, faces, normals):
    header = b"Baby doll in blanket - SDF marching cubes - 1:12 dollhouse scale"
    header = header[:80].ljust(80, b"\x00")
    with open(path, "wb") as f:
        f.write(header)
        f.write(struct.pack("<I", len(faces)))
        for i, face in enumerate(faces):
            n = normals[i] if i < len(normals) else (0.0, 0.0, 1.0)
            f.write(struct.pack("<fff", *n))
            for vi in face:
                f.write(struct.pack("<fff", *verts[vi]))
            f.write(struct.pack("<H", 0))

out = "baby_doll.stl"
write_binary_stl(out, verts, faces, normals)
size_mb = os.path.getsize(out) / 1024 / 1024
print(f"Written '{out}'  ({size_mb:.1f} MB)")
print(f"Total time: {time.time()-t0:.1f}s")
print()
print("Technique : Marching cubes on textured SDF")
print("Texture   : Multi-scale Gaussian noise fields (cloth folds + skin)")
print("Features  : Smooth-union/subtract (zero seams) — cheeks, eye sockets,")
print("            eyelids, nose bridge, button nose, nostrils, cupid's bow")
print("            lips, mouth crease, philtrum, flush ears + earlobes")
print("Scale     : 1:12 dollhouse  (~50 mm total length)")
