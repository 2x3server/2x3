#!/usr/bin/env python3
"""
Reproducible Mesh Comparison Script
Compares Original Mac Mesh (A: scene_dense_mesh_original.ply)
vs Experimental Cleaned Mesh (B: scene_dense_mesh_clean_28k.ply).
Calculates topological and geometric metrics and renders side-by-side comparative visual plots.
"""

import sys
import os
import time
from pathlib import Path
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def load_mesh(path: Path) -> trimesh.Trimesh:
    if not path.exists():
        raise FileNotFoundError(f"Mesh file {path} does not exist.")
    print(f"Loading mesh from {path}...")
    mesh = trimesh.load(str(path))
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(mesh.dump())
    return mesh

def compute_metrics(mesh: trimesh.Trimesh) -> dict:
    components = len(mesh.split(only_watertight=False)) if len(mesh.faces) > 0 else 0
    bbox = mesh.bounds if len(mesh.vertices) > 0 else np.zeros((2, 3))
    bbox_size = (bbox[1] - bbox[0]).round(4).tolist()

    return {
        "vertices": len(mesh.vertices),
        "faces": len(mesh.faces),
        "connected_components": components,
        "is_edge_manifold": bool(mesh.is_winding_consistent),
        "is_vertex_manifold": bool(mesh.is_volume),
        "is_watertight": bool(mesh.is_watertight),
        "bounding_box_min": bbox[0].round(4).tolist(),
        "bounding_box_max": bbox[1].round(4).tolist(),
        "bounding_box_size": bbox_size
    }

def render_mesh_on_ax(ax, mesh, elev, azim, title, centroid, scale):
    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.view_init(elev=elev, azim=azim)

    faces = mesh.faces
    if len(faces) > 40000:
        idx = np.random.choice(len(faces), 40000, replace=False)
        faces = faces[idx]

    verts = (mesh.vertices - centroid) / scale
    poly3d = Poly3DCollection(verts[faces], alpha=0.85, edgecolor='gray', linewidths=0.05, facecolors='lightsteelblue')
    ax.add_collection3d(poly3d)

    ax.set_xlim(-0.6, 0.6)
    ax.set_ylim(-0.6, 0.6)
    ax.set_zlim(-0.6, 0.6)
    ax.axis('off')

def render_mesh_wireframe_on_ax(ax, mesh, elev, azim, title, centroid, scale):
    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.view_init(elev=elev, azim=azim)
    verts = (mesh.vertices - centroid) / scale
    faces = mesh.faces
    if len(faces) > 25000:
        idx = np.random.choice(len(faces), 25000, replace=False)
        faces = faces[idx]

    poly3d = Poly3DCollection(verts[faces], alpha=0.15, edgecolor='navy', linewidths=0.2, facecolors='none')
    ax.add_collection3d(poly3d)
    ax.set_xlim(-0.6, 0.6)
    ax.set_ylim(-0.6, 0.6)
    ax.set_zlim(-0.6, 0.6)
    ax.axis('off')

def render_mesh_silhouette_on_ax(ax, mesh, elev, azim, title, centroid, scale):
    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.view_init(elev=elev, azim=azim)
    verts = (mesh.vertices - centroid) / scale
    faces = mesh.faces
    if len(faces) > 40000:
        idx = np.random.choice(len(faces), 40000, replace=False)
        faces = faces[idx]

    poly3d = Poly3DCollection(verts[faces], alpha=1.0, edgecolor='black', linewidths=0.08, facecolors='black')
    ax.add_collection3d(poly3d)
    ax.set_xlim(-0.6, 0.6)
    ax.set_ylim(-0.6, 0.6)
    ax.set_zlim(-0.6, 0.6)
    ax.axis('off')

def plot_views(mesh_a: trimesh.Trimesh, mesh_b: trimesh.Trimesh, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    views = {
        "top_view": (90, -90, "Vista dall'alto (Top View)"),
        "side_view": (0, 0, "Vista laterale (Side View)"),
        "front_view": (0, -90, "Vista frontale (Front View)"),
        "perspective_view": (30, -45, "Vista prospettica (Perspective View)")
    }

    centroid = (mesh_a.bounds[0] + mesh_a.bounds[1]) / 2.0
    scale = np.max(mesh_a.bounds[1] - mesh_a.bounds[0])

    for view_name, (elev, azim, title) in views.items():
        fig = plt.figure(figsize=(12, 6))

        ax1 = fig.add_subplot(121, projection='3d')
        render_mesh_on_ax(ax1, mesh_a, elev, azim, f"Mesh A (Originale Mac)\n{title}", centroid, scale)

        ax2 = fig.add_subplot(122, projection='3d')
        render_mesh_on_ax(ax2, mesh_b, elev, azim, f"Mesh B (Sperimentale 28k)\n{title}", centroid, scale)

        plt.tight_layout()
        plt.savefig(output_dir / f"{view_name}.png", dpi=150)
        plt.close(fig)

    fig = plt.figure(figsize=(12, 6))
    ax1 = fig.add_subplot(121, projection='3d')
    render_mesh_wireframe_on_ax(ax1, mesh_a, 30, -45, "Mesh A (Originale) - Wireframe", centroid, scale)
    ax2 = fig.add_subplot(122, projection='3d')
    render_mesh_wireframe_on_ax(ax2, mesh_b, 30, -45, "Mesh B (28k) - Wireframe", centroid, scale)
    plt.tight_layout()
    plt.savefig(output_dir / "wireframe_view.png", dpi=150)
    plt.close(fig)

    fig = plt.figure(figsize=(12, 6))
    ax1 = fig.add_subplot(121, projection='3d')
    render_mesh_silhouette_on_ax(ax1, mesh_a, 30, -45, "Mesh A (Originale) - Silhouette", centroid, scale)
    ax2 = fig.add_subplot(122, projection='3d')
    render_mesh_silhouette_on_ax(ax2, mesh_b, 30, -45, "Mesh B (28k) - Silhouette", centroid, scale)
    plt.tight_layout()
    plt.savefig(output_dir / "silhouette_view.png", dpi=150)
    plt.close(fig)

def main():
    start_time = time.time()

    exp_dir = Path("experiments/mesh_comparison_28k")

    path_a = exp_dir / "scene_dense_mesh_original.ply"
    path_b = exp_dir / "scene_dense_mesh_clean_28k.ply"

    mesh_a = load_mesh(path_a)
    mesh_b = load_mesh(path_b)

    metrics_a = compute_metrics(mesh_a)
    metrics_b = compute_metrics(mesh_b)

    print("=== MESH A (ORIGINAL MAC) METRICS ===")
    for k, v in metrics_a.items():
        print(f"  {k}: {v}")

    print("\n=== MESH B (CLEAN 28K) METRICS ===")
    for k, v in metrics_b.items():
        print(f"  {k}: {v}")

    print("\nGenerating authentic comparative view plots...")
    plot_views(mesh_a, mesh_b, exp_dir)

    elapsed = time.time() - start_time
    print(f"\nCompleted evaluation in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
