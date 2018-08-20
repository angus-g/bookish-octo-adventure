import numpy as np
from pyrr import Matrix44

class Waves(object):
    def __init__(self, context, dims, wireframe=False):
        geom_filename = 'pass.geom'
        if wireframe:
            geom_filename = 'wireframe.geom'
        
        with open('wave.vert') as vert_file, open('diffuse.frag') as frag_file, open(geom_filename) as geom_file:
            self.prog = context.program(vertex_shader=vert_file.read(),
                                        fragment_shader=frag_file.read(),
                                        geometry_shader=geom_file.read())

        self.gen_wave_directions()
        self.prog['u_ambient'].value = .1
        self.prog['u_diffuse'].value = .9
        self.prog['light'].write(np.array([2,2,2], dtype=np.float32))
    
        x_coords = np.linspace(-10., 10., 100)
        plane_points = np.empty((len(x_coords), len(x_coords), 2), dtype=np.float32)
        plane_points[..., 0] = x_coords[:, None]
        plane_points[..., 1] = x_coords
    
        """
        plane_points = np.load('hgrid.npy')[::4,::4,:]
        plane_points += [100,0]
        plane_points /= [180, 80]
        """
    
        plane_nx, plane_ny, _ = plane_points.shape
        vbo_plane = context.buffer(plane_points.astype('f4'))
    
        plane_indices = []
        for i in range(plane_nx*(plane_ny - 1)):
            # skip end points
            if (i+1) % plane_nx == 0:
                continue
            plane_indices.append([i, i+1, i+plane_nx])
            plane_indices.append([i+plane_nx, i+1, i+plane_nx+1])
        ivbo_plane = context.buffer(np.asarray(plane_indices, dtype=np.int32))
        self.vao = context.simple_vertex_array(self.prog, vbo_plane, 'in_vert', index_buffer=ivbo_plane)

        width, height = dims
        self.mat_proj = Matrix44.perspective_projection(45, width / height, 0.1, 100.0)
     
    def gen_wave_directions(self):
        # choose a set of directions
        self.directions = np.empty((4,2))
        primary_direction = np.random.randn(2)
        self.directions[0,:] = primary_direction / np.linalg.norm(primary_direction)
        # helper function to generate a rotation matrix
        def rot(theta):
            theta = np.radians(theta)
            return np.array([[np.cos(theta), -np.sin(theta)],
                             [np.sin(theta),  np.cos(theta)]])

        # rotate by a small random amount
        for i in range(1,4):
            self.directions[i,:] = rot(np.random.randn() * 30) @ self.directions[0,:]

        self.prog['u_direction'].write(self.directions.astype('f4'))

    def render(self, time):
        self.prog['u_time'].value = time
        self.vao.render()

    def update_camera(self, camera_pos):
        mat_view = Matrix44.look_at(camera_pos,
                                    np.array([0, 0, 0]),
                                    np.array([0, 0, 1]))
        mat_camera = self.mat_proj * mat_view
        self.prog['u_camera'].write(mat_camera.astype('f4'))
