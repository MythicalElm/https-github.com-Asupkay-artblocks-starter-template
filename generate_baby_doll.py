#!/usr/bin/env python3
"""
Realistic toy baby wrapped in a blanket — dollhouse 1:12 scale.

Uses CadQuery (OpenCASCADE kernel) for proper CAD design:
  - Non-uniform scaling via BRepBuilderAPI_GTransform (OCCT GTrsf)
  - Boolean CSG union / cut operations for all features
  - Correct newborn proportions: large head (~1/4 body length), chubby cheeks
  - Facial anatomy: eye sockets, eyelids, nose with nostrils + bridge,
    cupid's bow lips, mouth crease, philtrum, ears with concha + earlobes
  - Blanket details: flattened top surface, chest fold ridge, side tuck grooves,
    flat bottom for stable placement

Dimensions (1:12 dollhouse scale):
  Body  : 18 mm W × 38 mm L × 11 mm H
  Head  : 14 mm W × 17 mm L  (slightly elongated newborn cranium)
  Total length (lying down) : ~52 mm
"""

import os
import cadquery as cq
from cadquery import exporters
from OCP.gp import gp_GTrsf, gp_Mat
from OCP.BRepBuilderAPI import BRepBuilderAPI_GTransform


# ── Core helpers ─────────────────────────────────────────────────────────────

def _scale_xyz(shape_val, sx, sy, sz):
    """Non-uniform axis scale on a raw CadQuery Shape value."""
    mat = gp_Mat(sx, 0, 0,
                  0, sy, 0,
                  0, 0, sz)
    t = gp_GTrsf()
    t.SetVectorialPart(mat)
    builder = BRepBuilderAPI_GTransform(shape_val.wrapped, t, True)
    return cq.Solid(builder.Shape())


def ellipsoid(ax, ay, az):
    """Axis-aligned solid ellipsoid with half-axes (ax, ay, az)."""
    unit_sphere = cq.Workplane("XY").sphere(1.0).val()
    return _scale_xyz(unit_sphere, ax, ay, az)


def wp(solid, tx=0.0, ty=0.0, tz=0.0):
    """Wrap a Solid in a Workplane, optionally translating it."""
    return cq.Workplane("XY").add(solid).translate((tx, ty, tz))


# ═════════════════════════════════════════════════════════════════════════════
# 1. SWADDLED BODY
#    Ellipsoid: 9 W × 19 L × 6.5 H mm half-axes
#    Lifted so base rests at z = 0, then top flattened.
# ═════════════════════════════════════════════════════════════════════════════

BX, BY, BZ, BCZ = 9.0, 19.0, 6.5, 6.5

body = wp(ellipsoid(BX, BY, BZ), tz=BCZ)

# Flatten top surface (blanket lies flat) — remove top 1.4 mm cap
body = body.cut(
    cq.Workplane("XY").box(50, 60, 6).translate((0, 0, BCZ + BZ - 1.0))
)

# Flat bottom — trim bottom 0.8 mm so baby sits level
body = body.cut(
    cq.Workplane("XY").box(50, 60, 2).translate((0, 0, -1.0))
)

# ── Chest fold ridge ──────────────────────────────────────────────────────────
# Half-oval ridge at y ≈ +11 mm, represents the turned-down blanket edge.
fold = (
    cq.Workplane("XZ")
    .workplane(offset=11)
    .moveTo(0, BCZ + BZ - 1.0)
    .ellipseArc(7.5, 1.7, 0, 180, startAtCurrent=False)
    .close()
    .extrude(0.9, both=True)
)
body = body.union(fold)

# ── Side tuck grooves ─────────────────────────────────────────────────────────
# Thin ellipsoidal cutter on each flank, mimicking where blanket tucks under.
for xs in (+1, -1):
    groove = wp(ellipsoid(1.3, 18.5, 2.2), tx=xs * (BX - 0.2), tz=BCZ * 0.5)
    body = body.cut(groove)


# ═════════════════════════════════════════════════════════════════════════════
# 2. NECK
#    Small connecting ellipsoid that blends body into head.
# ═════════════════════════════════════════════════════════════════════════════

neck = wp(ellipsoid(4.5, 5.5, 4.5), ty=20.5, tz=8.5)


# ═════════════════════════════════════════════════════════════════════════════
# 3. HEAD
#    Slightly elongated newborn cranium: 7 W × 8.5 L × 8 H half-axes.
# ═════════════════════════════════════════════════════════════════════════════

HCY, HCZ = 27.0, 10.0

head = wp(ellipsoid(7.0, 8.5, 8.0), ty=HCY, tz=HCZ)

# Chubby cheeks
for xs in (+1, -1):
    cheek = wp(ellipsoid(3.8, 3.0, 3.0), tx=xs * 4.5, ty=HCY + 5.5, tz=HCZ - 1.5)
    head = head.union(cheek)

# Chin
head = head.union(wp(ellipsoid(3.0, 2.2, 2.0), ty=HCY + 7.0, tz=HCZ - 4.0))


# ═════════════════════════════════════════════════════════════════════════════
# 4. FACE FEATURES  (face points in the +Y direction)
# ═════════════════════════════════════════════════════════════════════════════

FY = HCY + 8.0   # approximate front face surface Y

# ── Eye sockets ───────────────────────────────────────────────────────────────
for xs in (+1, -1):
    head = head.cut(
        wp(ellipsoid(2.9, 1.1, 2.2), tx=xs * 3.1, ty=FY + 0.2, tz=HCZ + 1.8)
    )

# ── Eyelids ───────────────────────────────────────────────────────────────────
for xs in (+1, -1):
    head = head.union(
        wp(ellipsoid(2.7, 0.9, 1.1), tx=xs * 3.1, ty=FY + 0.5, tz=HCZ + 2.1)
    )

# ── Nose ──────────────────────────────────────────────────────────────────────
head = head.union(wp(ellipsoid(2.3, 1.7, 1.8), ty=FY + 1.2, tz=HCZ - 0.5))

# Nose bridge
head = head.union(wp(ellipsoid(1.1, 0.8, 2.2), ty=FY + 0.4, tz=HCZ + 0.9))

# Nostrils
for xs in (+1, -1):
    head = head.cut(
        wp(ellipsoid(0.9, 0.9, 0.9), tx=xs * 1.15, ty=FY + 1.8, tz=HCZ - 1.0)
    )

# ── Lips ──────────────────────────────────────────────────────────────────────
# Cupid's bow: two upper-lip lobes
for xs in (+1, -1):
    head = head.union(
        wp(ellipsoid(1.5, 1.0, 1.0), tx=xs * 1.25, ty=FY + 1.0, tz=HCZ - 2.3)
    )
# Lower lip
head = head.union(wp(ellipsoid(2.9, 1.1, 1.1), ty=FY + 0.95, tz=HCZ - 3.4))

# Mouth crease
head = head.cut(
    cq.Workplane("XY").box(5.8, 0.9, 0.5).translate((0, FY + 1.4, HCZ - 2.85))
)

# Philtrum (vertical groove under nose)
head = head.cut(
    wp(ellipsoid(0.6, 0.55, 1.5), ty=FY + 1.2, tz=HCZ - 1.75)
)

# ── Ears ──────────────────────────────────────────────────────────────────────
for xs in (+1, -1):
    head = head.union(
        wp(ellipsoid(1.8, 1.3, 2.5), tx=xs * 7.5, ty=HCY + 1.0, tz=HCZ)
    )
    head = head.cut(
        wp(ellipsoid(1.0, 0.9, 1.5), tx=xs * 8.0, ty=HCY + 0.8, tz=HCZ)
    )
    # Earlobe
    head = head.union(
        wp(ellipsoid(1.2, 0.9, 1.2), tx=xs * 7.2, ty=HCY + 1.5, tz=HCZ - 2.6)
    )


# ═════════════════════════════════════════════════════════════════════════════
# 5. ASSEMBLE
# ═════════════════════════════════════════════════════════════════════════════

baby = body.union(neck).union(head)


# ═════════════════════════════════════════════════════════════════════════════
# 6. EXPORT
# ═════════════════════════════════════════════════════════════════════════════

out = "baby_doll.stl"
exporters.export(baby, out, exportType="STL", tolerance=0.04, angularTolerance=0.08)

size_kb = os.path.getsize(out) / 1024
print(f"Generated '{out}'  ({size_kb:.1f} KB)")
print("Parts   : swaddled body, neck, head")
print("Details : blanket fold ridge, tuck grooves, flat top & bottom,")
print("          chubby cheeks, chin, eye sockets, eyelids, nose bridge,")
print("          nostrils, cupid's bow lips, mouth crease, philtrum,")
print("          ears with concha + earlobes")
print("Scale   : 1:12 dollhouse  (~52 mm total length)")
