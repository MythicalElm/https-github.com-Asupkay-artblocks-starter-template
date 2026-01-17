#!/usr/bin/env python3
"""
Generate a Chicago Bears Trophy STL file matching the detailed reference design
"""

import numpy as np
import trimesh
import math

def create_cylinder(radius, height, segments=32):
    """Create a cylinder mesh using trimesh"""
    return trimesh.creation.cylinder(radius=radius, height=height, sections=segments)

def create_torus(major_radius, minor_radius, segments=32):
    """Create a torus (ring) mesh"""
    return trimesh.creation.annulus(r_min=major_radius-minor_radius, r_max=major_radius+minor_radius, height=minor_radius*2)

def create_multi_tier_base():
    """Create the multi-tiered circular base"""
    meshes = []

    # Bottom tier (largest)
    tier1 = create_cylinder(radius=50, height=8, segments=64)
    tier1.apply_translation([0, 0, 4])
    meshes.append(tier1)

    # Decorative ring on tier 1
    ring1 = create_cylinder(radius=48, height=2, segments=64)
    ring1.apply_translation([0, 0, 9])
    meshes.append(ring1)

    # Middle tier
    tier2 = create_cylinder(radius=45, height=6, segments=64)
    tier2.apply_translation([0, 0, 11])
    meshes.append(tier2)

    # Top tier (where text goes - "CHICAGO BEARS")
    tier3 = create_cylinder(radius=42, height=10, segments=64)
    tier3.apply_translation([0, 0, 19])
    meshes.append(tier3)

    # Add decorative bumps/details around the text tier
    num_bumps = 16
    for i in range(num_bumps):
        angle = 2 * math.pi * i / num_bumps
        x = 42 * math.cos(angle)
        y = 42 * math.sin(angle)
        bump = trimesh.creation.cylinder(radius=2, height=10, segments=8)
        bump.apply_translation([x, y, 19])
        meshes.append(bump)

    # Top platform for columns
    platform = create_cylinder(radius=40, height=4, segments=64)
    platform.apply_translation([0, 0, 26])
    meshes.append(platform)

    return trimesh.util.concatenate(meshes)

def create_columns():
    """Create the columnar supports"""
    meshes = []
    num_columns = 6
    column_radius = 3
    column_height = 35
    column_distance = 28

    for i in range(num_columns):
        angle = 2 * math.pi * i / num_columns
        x = column_distance * math.cos(angle)
        y = column_distance * math.sin(angle)

        # Main column
        column = create_cylinder(radius=column_radius, height=column_height, segments=16)
        column.apply_translation([x, y, 28 + column_height/2])
        meshes.append(column)

        # Column cap (top)
        cap_top = create_cylinder(radius=column_radius * 1.2, height=2, segments=16)
        cap_top.apply_translation([x, y, 28 + column_height + 1])
        meshes.append(cap_top)

        # Column base (bottom)
        cap_bottom = create_cylinder(radius=column_radius * 1.2, height=2, segments=16)
        cap_bottom.apply_translation([x, y, 28 + 1])
        meshes.append(cap_bottom)

    return trimesh.util.concatenate(meshes)

def create_bear_head():
    """Create a detailed bear head logo"""
    meshes = []

    # Main head (base oval/sphere)
    head = trimesh.creation.icosphere(subdivisions=3, radius=25)
    head.apply_scale([1.0, 0.8, 1.2])  # Make it more oval
    head.apply_translation([0, 0, 85])
    meshes.append(head)

    # Snout/muzzle (protruding forward)
    snout = trimesh.creation.icosphere(subdivisions=2, radius=12)
    snout.apply_scale([1.2, 1.5, 0.8])
    snout.apply_translation([0, 15, 78])
    meshes.append(snout)

    # Nose
    nose = trimesh.creation.icosphere(subdivisions=2, radius=5)
    nose.apply_scale([1.0, 1.2, 0.8])
    nose.apply_translation([0, 25, 78])
    meshes.append(nose)

    # Eyes (left and right)
    eye_left = trimesh.creation.icosphere(subdivisions=2, radius=4)
    eye_left.apply_translation([-10, 10, 90])
    meshes.append(eye_left)

    eye_right = trimesh.creation.icosphere(subdivisions=2, radius=4)
    eye_right.apply_translation([10, 10, 90])
    meshes.append(eye_right)

    # Ears (left and right)
    ear_left = trimesh.creation.icosphere(subdivisions=2, radius=8)
    ear_left.apply_scale([1.0, 0.8, 1.3])
    ear_left.apply_translation([-20, -5, 100])
    meshes.append(ear_left)

    ear_right = trimesh.creation.icosphere(subdivisions=2, radius=8)
    ear_right.apply_scale([1.0, 0.8, 1.3])
    ear_right.apply_translation([20, -5, 100])
    meshes.append(ear_right)

    # Brow ridges (for fierce look)
    brow_left = trimesh.creation.cylinder(radius=3, height=12, sections=8)
    brow_left.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [0, 1, 0]))
    brow_left.apply_transform(trimesh.transformations.rotation_matrix(math.pi/6, [0, 0, 1]))
    brow_left.apply_translation([-12, 8, 92])
    meshes.append(brow_left)

    brow_right = trimesh.creation.cylinder(radius=3, height=12, sections=8)
    brow_right.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [0, 1, 0]))
    brow_right.apply_transform(trimesh.transformations.rotation_matrix(-math.pi/6, [0, 0, 1]))
    brow_right.apply_translation([12, 8, 92])
    meshes.append(brow_right)

    # Mouth/jaw detail
    jaw_left = trimesh.creation.cylinder(radius=2.5, height=10, sections=8)
    jaw_left.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [0, 1, 0]))
    jaw_left.apply_transform(trimesh.transformations.rotation_matrix(math.pi/4, [0, 0, 1]))
    jaw_left.apply_translation([-8, 20, 75])
    meshes.append(jaw_left)

    jaw_right = trimesh.creation.cylinder(radius=2.5, height=10, sections=8)
    jaw_right.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [0, 1, 0]))
    jaw_right.apply_transform(trimesh.transformations.rotation_matrix(-math.pi/4, [0, 0, 1]))
    jaw_right.apply_translation([8, 20, 75])
    meshes.append(jaw_right)

    # Teeth (upper)
    for i in range(4):
        x_pos = -6 + i * 4
        tooth = trimesh.creation.cylinder(radius=1.5, height=4, sections=6)
        tooth.apply_translation([x_pos, 24, 74])
        meshes.append(tooth)

    # Lower jaw/chin
    chin = trimesh.creation.icosphere(subdivisions=2, radius=8)
    chin.apply_scale([1.2, 1.0, 0.6])
    chin.apply_translation([0, 18, 70])
    meshes.append(chin)

    # Add some fur texture detail using small spheres
    np.random.seed(42)
    for _ in range(30):
        # Random position on the head surface
        theta = np.random.uniform(0, 2 * math.pi)
        phi = np.random.uniform(0, math.pi)
        r = 24
        x = r * math.sin(phi) * math.cos(theta) * 0.8
        y = r * math.sin(phi) * math.sin(theta) * 0.6 + np.random.uniform(-5, 5)
        z = r * math.cos(phi) * 1.0 + 85

        if z > 75 and z < 100:  # Only on upper head
            fur = trimesh.creation.icosphere(subdivisions=0, radius=1.5)
            fur.apply_translation([x, y, z])
            meshes.append(fur)

    return trimesh.util.concatenate(meshes)

def create_text_embossing():
    """Create embossed text effect on the base"""
    # This is a simplified representation using small cylinders
    # Real text would require font rendering
    meshes = []

    text_radius = 42
    text_height = 24

    # Create small bumps to represent text "CHICAGO BEARS"
    # Simplified as decorative elements since true text rendering is complex
    num_decorations = 24
    for i in range(num_decorations):
        angle = 2 * math.pi * i / num_decorations
        x = text_radius * math.cos(angle)
        y = text_radius * math.sin(angle)

        # Small decorative bump
        bump = trimesh.creation.box(extents=[2, 1, 6])

        # Rotate to face outward
        rotation = trimesh.transformations.rotation_matrix(angle + math.pi/2, [0, 0, 1])
        bump.apply_transform(rotation)
        bump.apply_translation([x, y, text_height])
        meshes.append(bump)

    return trimesh.util.concatenate(meshes)

def main():
    print("Generating detailed Chicago Bears Trophy STL...")

    print("Creating multi-tiered base...")
    base = create_multi_tier_base()

    print("Creating columnar supports...")
    columns = create_columns()

    print("Creating text embossing...")
    text = create_text_embossing()

    print("Creating detailed bear head...")
    bear_head = create_bear_head()

    print("Combining all components...")
    trophy = trimesh.util.concatenate([base, columns, text, bear_head])

    # Center the trophy
    trophy.apply_translation([0, 0, -trophy.bounds[0][2]])

    # Export to STL
    output_file = 'chicago_bears_trophy.stl'
    print(f"Saving to {output_file}...")
    trophy.export(output_file)

    print(f"✓ Successfully created {output_file}")
    print(f"  Total triangles: {len(trophy.faces)}")
    bounds = trophy.bounds
    dimensions = bounds[1] - bounds[0]
    print(f"  Dimensions: {dimensions[0]:.1f}mm x {dimensions[1]:.1f}mm x {dimensions[2]:.1f}mm")
    print(f"  Volume: {trophy.volume:.1f} mm³")

if __name__ == '__main__':
    main()
