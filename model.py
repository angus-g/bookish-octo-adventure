import numpy as np
import pyassimp
from pyrr import Matrix44

class Model(object):
    def __init__(self, context, dims):
        with open('model.vert') as vert_file, open('diffuse.frag') as frag_file:
            self.prog = context.program(vertex_shader=vert_file.read(), fragment_shader=frag_file.read())
            
        self.prog['u_ambient'].value = 0
        self.prog['u_diffuse'].value = 1

        self.mesh = pyassimp.load('monkey.obj')

        vbo = context.buffer(np.hstack((self.mesh.meshes[0].vertices,
                                        self.mesh.meshes[0].normals)))
        index_vbo = context.buffer(self.mesh.meshes[0].faces)
        self.vao = context.simple_vertex_array(self.prog, vbo, 'in_vert', 'in_norm', index_buffer=index_vbo)

        # fixed light
        self.prog['light'].write(np.array([2, 2, 2], dtype=np.float32))

        width, height = dims
        mat_proj = Matrix44.perspective_projection(45, width / height, 0.1, 100.0)
        mat_view = Matrix44.look_at(np.array([4., 3., 3.]),
                                    np.array([0., 0., 0.]),
                                    np.array([0., 1., 0.]))
        mat_camera = mat_proj * mat_view
        self.prog['u_camera'].write(mat_camera.astype('f4'))

        self.mat_model = Matrix44.identity()
        self.update_model_transform()
        
    def update_model_transform(self):
        self.prog['u_model'].write(self.mat_model.astype('f4'))
        self.prog['u_normal'].write(self.mat_model.inverse.transpose().astype('f4').tobytes())

    def render(self):
        self.vao.render()
