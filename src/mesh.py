import numpy as np
import open3d as o3d

# Triangulate input cloud points using ball pivoting algorithm
def triangulate(input, output):
    point_cloud = np.loadtxt(input)
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(point_cloud[:,:3])
    pcd.normals = o3d.utility.Vector3dVector(np.zeros((1, 3)))
    pcd.estimate_normals()
    pcd.orient_normals_consistent_tangent_plane(100)
    distances = pcd.compute_nearest_neighbor_distance()
    avg_dist = np.mean(distances)
    #print(avg_dist)
    radius = [avg_dist * 1 * (1 + r/25) for r in range(0,100)] # Compute different radius to try for the ball
    #print(radius)
    bpa_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(pcd,o3d.utility.DoubleVector(radius))
    o3d.io.write_triangle_mesh(output, bpa_mesh)