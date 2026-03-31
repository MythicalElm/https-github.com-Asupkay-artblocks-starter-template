#!/usr/bin/env python3
"""
Generate STL file for a toy baby wrapped in a blanket (dollhouse 1:12 scale).

Dimensions (approx 1:12 scale):
  Swaddled body: 18mm wide x 40mm long x 14mm tall
  Head: 16mm diameter sphere
  Total height: ~25mm
"""

import math
import struct


def normalize(v):
    x, y, z = v
    mag = math.sqrt(x * x + y * y + z * z)
    if mag < 1e-10:
        return (0.0, 0.0, 1.0)
    return (x / mag, y / mag, z / mag)


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def tri_normal(v0, v1, v2):
    return normalize(cross(sub(v1, v0), sub(v2, v0)))


tris = []


def add_tri(v0, v1, v2):
    n = tri_normal(v0, v1, v2)
    tris.append((n, v0, v1, v2))


def superellipsoid_point(lat, lon, a, b, c, n=1.4):
    """
    Superellipsoid: gives a softer-rectangular 'swaddled' silhouette.
    n > 1 makes the cross-section more rectangular (blanket-like).
    """
    cos_lat = math.cos(lat)
    sin_lat = math.sin(lat)
    cos_lon = math.cos(lon)
    sin_lon = math.sin(lon)

    def signed_pow(val, p):
        s = 1.0 if val >= 0 else -1.0
        return s * (abs(val) ** p)

    x = a * signed_pow(cos_lat, 2.0 / n) * signed_pow(cos_lon, 2.0 / n)
    y = b * signed_pow(cos_lat, 2.0 / n) * signed_pow(sin_lon, 2.0 / n)
    z = c * signed_pow(sin_lat, 2.0 / n)
    return (x, y, z)


# ============================================================
# SWADDLED BODY
# Superellipsoid: 9mm half-width (X), 20mm half-length (Y), 7mm half-height (Z)
# Center lifted to Z=7 so base sits at Z=0
# n=1.6 gives a boxy blanket profile
# ============================================================
U = 40  # longitude divisions
V = 28  # latitude divisions

bx, by, bz = 9.0, 20.0, 7.0
bcz = 7.0  # center Z
n_body = 1.6  # superellipsoid exponent (boxy)


def body_vertex(ui, vi):
    lat = math.pi * (-0.5 + vi / V)
    lon = 2 * math.pi * ui / U
    x, y, z = superellipsoid_point(lat, lon, bx, by, bz, n_body)
    return (x, y, z + bcz)


for vi in range(V):
    for ui in range(U):
        v00 = body_vertex(ui, vi)
        v10 = body_vertex((ui + 1) % U, vi)
        v01 = body_vertex(ui, vi + 1)
        v11 = body_vertex((ui + 1) % U, vi + 1)
        add_tri(v00, v01, v10)
        add_tri(v10, v01, v11)


# ============================================================
# BLANKET FOLD RIDGE
# A thin torus-like ridge across the upper body (X axis),
# simulating the folded blanket edge near the chest.
# ============================================================
def torus_vertex(theta, phi, R, r, cx, cy, cz):
    """Torus centered at (cx,cy,cz), ring around Z axis."""
    x = cx + (R + r * math.cos(phi)) * math.cos(theta)
    y = cy + (R + r * math.cos(phi)) * math.sin(theta)
    z = cz + r * math.sin(phi)
    return (x, y, z)


# A small ridge strip at y≈+12mm (chest area), running across X
# Modeled as a half-cylinder bump along X axis
ridge_y = 12.0
ridge_z = bcz + bz * 0.55  # on the upper surface
ridge_r = 1.2  # radius of the ridge
ridge_half_len = bx * 0.85  # length across

RU = 20  # segments along length
RV = 10  # segments around ridge (half circle, top only)


def ridge_vertex(ri, rv):
    t = -ridge_half_len + (2 * ridge_half_len) * ri / RU
    phi = math.pi * rv / RV  # 0..pi (top half)
    x = t
    y = ridge_y + ridge_r * math.sin(phi)
    z = ridge_z + ridge_r * math.cos(phi)
    return (x, y, z)


for ri in range(RU):
    for rv in range(RV - 1):
        v00 = ridge_vertex(ri, rv)
        v10 = ridge_vertex(ri + 1, rv)
        v01 = ridge_vertex(ri, rv + 1)
        v11 = ridge_vertex(ri + 1, rv + 1)
        add_tri(v00, v01, v10)
        add_tri(v10, v01, v11)

# End caps for the ridge
for rv in range(RV - 1):
    tip = (0.0, ridge_y, ridge_z)
    v0 = ridge_vertex(0, rv)
    v1 = ridge_vertex(0, rv + 1)
    add_tri(tip, v1, v0)
    v0r = ridge_vertex(RU, rv)
    v1r = ridge_vertex(RU, rv + 1)
    add_tri(tip, v0r, v1r)


# ============================================================
# HEAD
# Sphere r=8mm at +Y end, slightly raised
# Center at (0, 22, 9)
# ============================================================
HR = 8.0
hcx, hcy, hcz = 0.0, 22.0, 9.0
HU, HV = 28, 20


def head_vertex(ui, vi):
    lat = math.pi * (-0.5 + vi / HV)
    lon = 2 * math.pi * ui / HU
    x = hcx + HR * math.cos(lat) * math.cos(lon)
    y = hcy + HR * math.cos(lat) * math.sin(lon)
    z = hcz + HR * math.sin(lat)
    return (x, y, z)


for vi in range(HV):
    for ui in range(HU):
        v00 = head_vertex(ui, vi)
        v10 = head_vertex((ui + 1) % HU, vi)
        v01 = head_vertex(ui, vi + 1)
        v11 = head_vertex((ui + 1) % HU, vi + 1)
        add_tri(v00, v01, v10)
        add_tri(v10, v01, v11)


# ============================================================
# FACE FEATURES
# Small bumps for eyes and a subtle nose on the head
# ============================================================
def bump_sphere(cx, cy, cz, r, u_segs=10, v_segs=8):
    """Add a small convex bump (half-sphere) protruding from the face."""
    for vi in range(v_segs):
        for ui in range(u_segs):
            lat0 = math.pi * 0.5 * vi / v_segs         # 0..pi/2 (hemisphere)
            lat1 = math.pi * 0.5 * (vi + 1) / v_segs
            lon0 = 2 * math.pi * ui / u_segs
            lon1 = 2 * math.pi * (ui + 1) / u_segs

            def bv(lat, lon):
                # Orient bump outward along +Y (face direction)
                bx_ = cx + r * math.sin(lat) * math.cos(lon)
                by_ = cy + r * math.cos(lat)   # protruding in +Y
                bz_ = cz + r * math.sin(lat) * math.sin(lon)
                return (bx_, by_, bz_)

            v00 = bv(lat0, lon0)
            v10 = bv(lat0, lon1)
            v01 = bv(lat1, lon0)
            v11 = bv(lat1, lon1)
            add_tri(v00, v01, v10)
            add_tri(v10, v01, v11)


# Face direction: +Y from head center
# Eyes: symmetric about X=0, slightly above center, at front of head
face_y_offset = HR * 0.88  # face surface
eye_z_offset = 1.5         # slightly above center
eye_x_offset = 2.8         # separation

bump_sphere(hcx + eye_x_offset, hcy + face_y_offset, hcz + eye_z_offset, 1.0)
bump_sphere(hcx - eye_x_offset, hcy + face_y_offset, hcz + eye_z_offset, 1.0)

# Nose: center, slightly below eyes
bump_sphere(hcx, hcy + face_y_offset, hcz - 0.5, 0.85)


# ============================================================
# WRITE BINARY STL
# ============================================================
fname = "baby_doll.stl"
header_text = b"Baby doll in blanket - dollhouse 1:12 scale by generate_baby_doll.py"
header = header_text[:80].ljust(80, b"\x00")

with open(fname, "wb") as f:
    f.write(header)
    f.write(struct.pack("<I", len(tris)))
    for n, v0, v1, v2 in tris:
        f.write(struct.pack("<fff", *n))
        f.write(struct.pack("<fff", *v0))
        f.write(struct.pack("<fff", *v1))
        f.write(struct.pack("<fff", *v2))
        f.write(struct.pack("<H", 0))  # attribute byte count

size_kb = len(tris) * 50 / 1024
print(f"Generated '{fname}'")
print(f"  Triangles : {len(tris)}")
print(f"  File size : ~{size_kb:.1f} KB")
print(f"  Body dims : {2*bx:.0f}mm W x {2*by:.0f}mm L x {2*bz:.0f}mm H")
print(f"  Head diam : {2*HR:.0f}mm")
print(f"  Scale     : 1:12 dollhouse")
