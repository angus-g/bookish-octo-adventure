import numpy as np
import pyassimp
from pyrr import Matrix44

class Model(object):
    def __init__(self, context, dims):
        self.context = context

        with open('model.vert') as vert_file, open('model-diffuse.frag') as frag_file:
            self.prog = context.program(vertex_shader=vert_file.read(), fragment_shader=frag_file.read())

        # shader colors
        self.prog['u_ambient'].value = 0
        self.prog['u_diffuse'].value = 1

        # unwrap fraction
        self.prog['u_unwrap_frac'].value = 0

        self.load_mesh('monkey.obj')

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

    def load_mesh(self, filename):
        self.filename = filename
        self.mesh = pyassimp.load(self.filename)
        texcoords = self.mesh.meshes[0].texturecoords.squeeze()
        if texcoords.size == 0:
            texcoords = np.zeros_like(self.mesh.meshes[0].vertices)
        vbo = self.context.buffer(np.hstack((self.mesh.meshes[0].vertices,
                                             self.mesh.meshes[0].normals,
                                             texcoords[:,:2])))
        index_vbo = self.context.buffer(self.mesh.meshes[0].faces)
        self.vao = self.context.simple_vertex_array(self.prog, vbo, 'in_vert', 'in_norm', 'in_texcoord', index_buffer=index_vbo)
