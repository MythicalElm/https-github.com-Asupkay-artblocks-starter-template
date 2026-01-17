#!/usr/bin/env python3
"""
Generate a Chicago Bears Trophy STL file
"""

import numpy as np
from stl import mesh
import math

def create_box(width, depth, height, offset=(0, 0, 0)):
    """Create a rectangular box mesh"""
    vertices = np.array([
        # Bottom face
        [-width/2, -depth/2, 0],
        [width/2, -depth/2, 0],
        [width/2, depth/2, 0],
        [-width/2, depth/2, 0],
        # Top face
        [-width/2, -depth/2, height],
        [width/2, -depth/2, height],
        [width/2, depth/2, height],
        [-width/2, depth/2, height],
    ])

    # Apply offset
    vertices += np.array(offset)

    # Define the 12 triangles (2 per face * 6 faces)
    faces = np.array([
        # Bottom
        [0, 2, 1],
        [0, 3, 2],
        # Top
        [4, 5, 6],
        [4, 6, 7],
        # Front
        [0, 1, 5],
        [0, 5, 4],
        # Back
        [2, 3, 7],
        [2, 7, 6],
        # Left
        [0, 4, 7],
        [0, 7, 3],
        # Right
        [1, 2, 6],
        [1, 6, 5],
    ])

    return vertices, faces

def create_cylinder(radius, height, segments=32, offset=(0, 0, 0)):
    """Create a cylinder mesh"""
    vertices = []

    # Bottom circle
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        vertices.append([x, y, 0])

    # Top circle
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        vertices.append([x, y, height])

    # Bottom center
    vertices.append([0, 0, 0])
    # Top center
    vertices.append([0, 0, height])

    vertices = np.array(vertices)
    vertices += np.array(offset)

    faces = []

    # Bottom cap
    bottom_center = len(vertices) - 2
    for i in range(segments):
        next_i = (i + 1) % segments
        faces.append([bottom_center, next_i, i])

    # Top cap
    top_center = len(vertices) - 1
    for i in range(segments):
        next_i = (i + 1) % segments
        faces.append([top_center, i + segments, next_i + segments])

    # Side faces
    for i in range(segments):
        next_i = (i + 1) % segments
        # Two triangles per side face
        faces.append([i, next_i, next_i + segments])
        faces.append([i, next_i + segments, i + segments])

    return vertices, np.array(faces)

def create_c_logo(outer_radius, inner_radius, thickness, opening_angle=100, segments=64, offset=(0, 0, 0)):
    """Create the Chicago Bears 'C' logo shape"""
    vertices = []

    # Convert opening angle to radians
    opening_rad = math.radians(opening_angle)
    start_angle = -math.pi/2 + opening_rad/2
    end_angle = -math.pi/2 - opening_rad/2 + 2*math.pi

    # Generate outer arc
    for i in range(segments):
        t = i / (segments - 1)
        angle = start_angle + (end_angle - start_angle) * t
        x = outer_radius * math.cos(angle)
        y = outer_radius * math.sin(angle)
        vertices.append([x, y, 0])  # Bottom outer
        vertices.append([x, y, thickness])  # Top outer

    # Generate inner arc (reverse direction)
    for i in range(segments):
        t = i / (segments - 1)
        angle = end_angle - (end_angle - start_angle) * t
        x = inner_radius * math.cos(angle)
        y = inner_radius * math.sin(angle)
        vertices.append([x, y, 0])  # Bottom inner
        vertices.append([x, y, thickness])  # Top inner

    vertices = np.array(vertices)
    vertices += np.array(offset)

    faces = []

    # Create faces for the C shape
    # Outer surface
    for i in range(segments - 1):
        v1 = i * 2
        v2 = i * 2 + 1
        v3 = (i + 1) * 2
        v4 = (i + 1) * 2 + 1
        faces.append([v1, v3, v2])
        faces.append([v2, v3, v4])

    # Inner surface
    offset_inner = segments * 2
    for i in range(segments - 1):
        v1 = offset_inner + i * 2
        v2 = offset_inner + i * 2 + 1
        v3 = offset_inner + (i + 1) * 2
        v4 = offset_inner + (i + 1) * 2 + 1
        faces.append([v1, v2, v3])
        faces.append([v2, v4, v3])

    # Bottom face
    for i in range(segments - 1):
        v1_outer = i * 2
        v2_outer = (i + 1) * 2
        v1_inner = offset_inner + (segments - 1 - i) * 2
        v2_inner = offset_inner + (segments - 2 - i) * 2 if i < segments - 1 else offset_inner
        faces.append([v1_outer, v1_inner, v2_outer])
        faces.append([v2_outer, v1_inner, v2_inner])

    # Top face
    for i in range(segments - 1):
        v1_outer = i * 2 + 1
        v2_outer = (i + 1) * 2 + 1
        v1_inner = offset_inner + (segments - 1 - i) * 2 + 1
        v2_inner = offset_inner + (segments - 2 - i) * 2 + 1 if i < segments - 1 else offset_inner + 1
        faces.append([v1_outer, v2_outer, v1_inner])
        faces.append([v2_outer, v2_inner, v1_inner])

    # End caps
    # Start cap
    faces.append([0, offset_inner + (segments - 1) * 2, 1])
    faces.append([1, offset_inner + (segments - 1) * 2, offset_inner + (segments - 1) * 2 + 1])

    # End cap
    faces.append([(segments - 1) * 2, (segments - 1) * 2 + 1, offset_inner])
    faces.append([(segments - 1) * 2 + 1, offset_inner + 1, offset_inner])

    return vertices, np.array(faces)

def combine_meshes(mesh_list):
    """Combine multiple meshes into one"""
    total_faces = sum(len(faces) for _, faces in mesh_list)
    combined_data = np.zeros(total_faces, dtype=mesh.Mesh.dtype)

    current_idx = 0
    for vertices, faces in mesh_list:
        for face in faces:
            for i in range(3):
                combined_data['vectors'][current_idx][i] = vertices[face[i]]
            current_idx += 1

    return mesh.Mesh(combined_data)

def main():
    print("Generating Chicago Bears Trophy STL...")

    # Trophy dimensions
    base_width = 80
    base_depth = 80
    base_height = 10

    pedestal_radius = 20
    pedestal_height = 40

    logo_outer_radius = 40
    logo_inner_radius = 28
    logo_thickness = 8

    # Create components
    print("Creating base...")
    base_verts, base_faces = create_box(
        base_width, base_depth, base_height,
        offset=(0, 0, 0)
    )

    print("Creating pedestal...")
    pedestal_verts, pedestal_faces = create_cylinder(
        pedestal_radius, pedestal_height,
        offset=(0, 0, base_height)
    )

    print("Creating Chicago Bears 'C' logo...")
    logo_verts, logo_faces = create_c_logo(
        logo_outer_radius, logo_inner_radius, logo_thickness,
        opening_angle=90,
        offset=(0, 0, base_height + pedestal_height)
    )

    # Combine all meshes
    print("Combining meshes...")
    trophy_mesh = combine_meshes([
        (base_verts, base_faces),
        (pedestal_verts, pedestal_faces),
        (logo_verts, logo_faces)
    ])

    # Save to file
    output_file = 'chicago_bears_trophy.stl'
    print(f"Saving to {output_file}...")
    trophy_mesh.save(output_file)

    print(f"✓ Successfully created {output_file}")
    print(f"  Total triangles: {len(trophy_mesh.data)}")
    print(f"  Dimensions: {base_width}mm x {base_depth}mm x {base_height + pedestal_height + logo_thickness}mm")

if __name__ == '__main__':
    main()
