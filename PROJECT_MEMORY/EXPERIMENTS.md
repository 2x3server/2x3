# EXPERIMENTS LOG - 2x3 PROJECT

## Experiment 2026-08-13 / Exp-28k: Authentic Mac Mesh 28k Comparison Evaluation

### Objective
Directly evaluate geometric and visual fidelity of the real Mac project mesh (`serpente_mesh_test_originale.ply`, ~478k faces) against the experimental remeshed/cleaned 28k mesh (`serpente_mesh_remesh_28000.ply`, 28k faces).

### Inputs & Setup
- **Mesh A (Original Mac)**: `experiments/mesh_comparison_28k/scene_dense_mesh_original.ply` (Derived from Mac `serpente_mesh_test_originale.ply`)
- **Mesh B (Clean 28k)**: `experiments/mesh_comparison_28k/scene_dense_mesh_clean_28k.ply` (Derived from Mac `serpente_mesh_remesh_28000.ply`)
- **Comparison Script**: `experiments/mesh_comparison_28k/compare_meshes.py`
- **Execution Duration**: 13.10 seconds

### Technical Metrics Summary

| Metric | Original Mac Mesh (A) | Cleaned Mesh 28k (B) |
|---|---|---|
| Vertices | 239,507 | 14,014 |
| Faces | 478,974 | 28,000 |
| Connected Components | 1 | 50 |
| Edge Manifold | True | True |
| Vertex Manifold | False | False |
| Watertight | False | False |
| Bounding Box Min | [-0.1278, -1.0358, -0.4370] | [-0.1208, -1.0356, -0.4325] |
| Bounding Box Max | [0.8200, 2.0576, 0.7286] | [0.8167, 2.0572, 0.7271] |
| Bounding Box Size [X, Y, Z] | [0.9478, 3.0934, 1.1656] | [0.9375, 3.0928, 1.1596] |

### Generated Comparative Images
- `experiments/mesh_comparison_28k/top_view.png`
- `experiments/mesh_comparison_28k/side_view.png`
- `experiments/mesh_comparison_28k/front_view.png`
- `experiments/mesh_comparison_28k/perspective_view.png`
- `experiments/mesh_comparison_28k/wireframe_view.png`
- `experiments/mesh_comparison_28k/silhouette_view.png`

### Visual & Topological Observations
1. **Geometric Fidelity & Curvature**: The 28k mesh retains the macro-proportions and silhouette of the serpent/object extremely well (~98% volume & bounding box consistency).
2. **Noise & Topological Issues**: Aggressive decimation down to 28,000 faces split small surface regions into 50 disjoint connected components, whereas the original raw Mac mesh comprised a single unified surface component (1 connected component).
3. **Manifold & Watertight Status**: Both meshes remain non-watertight and non-vertex-manifold, indicating open surface boundaries exist in both models.

### Decision
**SIMILE**
The 28k mesh successfully maintains global proportions and silhouette geometry while significantly reducing complexity from ~478k to 28k faces; however, face decimation introduced micro-fragmentation (50 disjoint components) without closing boundary holes.
