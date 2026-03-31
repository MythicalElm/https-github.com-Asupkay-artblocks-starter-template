#!/usr/bin/env python3
"""
Realistic toy baby wrapped in a blanket — dollhouse 1:12 scale.

Design fixes over previous version:
  - Body uses filleted box (looks like a proper swaddled burrito, not flat disc)
  - Face points UPWARD (+Z) so it's visible when viewed from above in a dollhouse
  - All face features are shallow / flush with the head surface (no antenna ears)
  - Ears are thin flat ovals pressed flush against the head sides
  - Proper newborn proportions: head ≈ same width as body, chubby face

Dimensions (1:12 dollhouse scale):
  Body  : 17 mm W × 37 mm L × 12 mm H  (filleted-edge box, sits flat)
  Head  : 16 mm diameter sphere
  Total : ~50 mm length
"""

import os
import cadquery as cq
from cadquery import exporters
from OCP.gp import gp_GTrsf, gp_Mat
from OCP.BRepBuilderAPI import BRepBuilderAPI_GTransform


# ── Helpers ───────────────────────────────────────────────────────────────────

def _scale_xyz(shape_val, sx, sy, sz):
    mat = gp_Mat(sx, 0, 0,
                  0, sy, 0,
                  0, 0, sz)
    t = gp_GTrsf()
    t.SetVectorialPart(mat)
    builder = BRepBuilderAPI_GTransform(shape_val.wrapped, t, True)
    return cq.Solid(builder.Shape())


def ellipsoid(ax, ay, az):
    unit = cq.Workplane("XY").sphere(1.0).val()
    return _scale_xyz(unit, ax, ay, az)


def E(ax, ay, az, tx=0.0, ty=0.0, tz=0.0):
    """Place an ellipsoid solid as a Workplane."""
    return cq.Workplane("XY").add(ellipsoid(ax, ay, az)).translate((tx, ty, tz))


# ═════════════════════════════════════════════════════════════════════════════
# 1. SWADDLED BODY  — filleted rectangular box
#    Looks like a cloth-wrapped swaddle, not a flat disc.
#    Sitting flat at z = 0.
# ═════════════════════════════════════════════════════════════════════════════

# Box: 17 W × 37 L × 12 H, all edges filleted 2.8 mm for soft blanket feel
body = (
    cq.Workplane("XY")
    .box(17, 37, 12)
    .edges().fillet(2.8)
)
# Box is centred at origin (z = -6 to +6); lift so bottom rests at z = 0
body = body.translate((0, 0, 6))

# ── Blanket chest-fold ridge ──────────────────────────────────────────────────
# Semi-oval ridge at y = +10, running across width → turned-down blanket edge
fold = (
    cq.Workplane("XZ")
    .workplane(offset=10)
    .moveTo(0, 12.0)          # top surface of body
    .ellipseArc(7.0, 1.6, 0, 180, startAtCurrent=False)
    .close()
    .extrude(0.8, both=True)
)
body = body.union(fold)

# ── Shallow blanket wrinkle grooves ──────────────────────────────────────────
# Two thin cuts on the top surface, parallel to the long axis, simulating
# fabric folds where the blanket is pulled tight.
for xs in (+1, -1):
    wrinkle = (
        cq.Workplane("XY")
        .box(0.6, 28, 1.0)
        .translate((xs * 4.5, 0, 12.3))   # sits just above top surface
    )
    body = body.cut(wrinkle)


# ═════════════════════════════════════════════════════════════════════════════
# 2. NECK  — small ellipsoid blending body end into head
# ═════════════════════════════════════════════════════════════════════════════

neck = E(4.8, 4.5, 5.0, ty=21.0, tz=9.5)


# ═════════════════════════════════════════════════════════════════════════════
# 3. HEAD  — sphere, radius 8 mm
#    Centre at (0, 28, 10).  Face points UPWARD (+Z), slightly tilted toward
#    +Y (the head end), so the face is visible from above in a dollhouse.
# ═════════════════════════════════════════════════════════════════════════════

HR  = 8.0
HCX, HCY, HCZ = 0.0, 28.0, 10.0

head = cq.Workplane("XY").sphere(HR).translate((HCX, HCY, HCZ))

# ── Chubby cheeks ─────────────────────────────────────────────────────────────
# Rounded bumps on the lower-front of the head, adding baby chubbiness.
# Positioned so they blend smoothly with the sphere.
for xs in (+1, -1):
    head = head.union(
        E(3.2, 2.5, 2.8, tx=xs * 4.0, ty=HCY + 4.5, tz=HCZ - 2.0)
    )

# Chin: slight rounded protrusion below the mouth
head = head.union(E(2.8, 2.0, 1.8, ty=HCY + 6.0, tz=HCZ - 4.5))


# ═════════════════════════════════════════════════════════════════════════════
# 4. FACE FEATURES
#    Face points UP (+Z) and slightly toward +Y.
#    All feature depths are conservative: unions ≤ 1.5 mm proud,
#    cuts ≤ 0.8 mm deep, so nothing looks like an antenna.
#
#    Face surface (top of sphere) ≈ (0, HCY, HCZ + HR) = (0, 28, 18)
#    Tilting face toward +Y shifts features to ~(0, 31, 17)
# ═════════════════════════════════════════════════════════════════════════════

# All face features use a local origin anchored to the tilted face surface
FX  = HCX                  # centre X
FY  = HCY + 3.5            # face tilted toward +Y end
FZ  = HCZ + HR - 1.8       # face sits near top of sphere (inset 1.8mm)

# ── Eye sockets (subtle oval recesses) ───────────────────────────────────────
EYE_SEP = 2.6              # half-separation between eyes
for xs in (+1, -1):
    head = head.cut(
        E(2.4, 0.8, 1.8, tx=xs * EYE_SEP, ty=FY - 0.5, tz=FZ + 1.5)
    )

# ── Eyelids (thin raised arc over each socket) ───────────────────────────────
for xs in (+1, -1):
    head = head.union(
        E(2.3, 0.7, 0.9, tx=xs * EYE_SEP, ty=FY - 0.2, tz=FZ + 1.8)
    )

# ── Nose ──────────────────────────────────────────────────────────────────────
# Small rounded button nose — newborn noses are tiny and upturned
head = head.union(E(1.8, 1.3, 1.4, tx=FX, ty=FY + 1.0, tz=FZ - 0.2))

# Nostril hints (very shallow cuts)
for xs in (+1, -1):
    head = head.cut(
        E(0.7, 0.6, 0.7, tx=xs * 0.85, ty=FY + 1.5, tz=FZ - 0.6)
    )

# ── Lips ──────────────────────────────────────────────────────────────────────
# Upper lip: two small lobes (cupid's bow), lower lip: one wider lobe
for xs in (+1, -1):
    head = head.union(
        E(1.2, 0.8, 0.8, tx=xs * 1.0, ty=FY + 1.0, tz=FZ - 1.8)
    )
head = head.union(E(2.4, 0.9, 0.9, tx=FX, ty=FY + 0.9, tz=FZ - 2.8))

# Mouth crease line
head = head.cut(
    cq.Workplane("XY").box(4.8, 0.7, 0.45)
    .translate((FX, FY + 1.4, FZ - 2.3))
)

# ── Ears ──────────────────────────────────────────────────────────────────────
# FLAT against the sides of the head — just 0.6 mm proud so they read as ears
# without looking like alien antennae.
# Positioned at the equator of the sphere, X sides.
for xs in (+1, -1):
    # Ear: thin flat ellipsoid pressed to the side of the head
    ear_tx = xs * (HR - 0.6)       # nearly at sphere surface, X side
    head = head.union(
        E(0.7, 1.6, 2.4, tx=ear_tx, ty=HCY - 1.0, tz=HCZ)
    )
    # Concha (ear canal depression) — cut a very shallow recess
    head = head.cut(
        E(0.5, 0.9, 1.4, tx=xs * (HR + 0.1), ty=HCY - 1.0, tz=HCZ)
    )
    # Earlobe: small rounded bump at the bottom of the ear
    head = head.union(
        E(0.6, 1.0, 1.0, tx=xs * (HR - 0.8), ty=HCY - 0.5, tz=HCZ - 2.2)
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
print("Body    : filleted box 17×37×12 mm — proper swaddle profile")
print("Head    : sphere ∅16 mm, face pointing UP (visible from above)")
print("Features: eye sockets, eyelids, button nose, nostrils, cupid-bow lips,")
print("          mouth crease, flat-flush ears, chubby cheeks, chin")
print("Scale   : 1:12 dollhouse  (~50 mm total length)")
