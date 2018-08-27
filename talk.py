#!/usr/bin/env python

import g
import imgui
import numpy as np
from pyrr import Matrix44

class C(g.App):
    def __init__(self):
        super().__init__(gui=True)

        # GUI state variables
        self.gui = {
            'u_unwrap': 0,
            'animate': False,
        }

        # load shaders
        self.prog = self.ctx.program(vertex_shader=open('shaders/talk.vert').read(),
                                     fragment_shader=open('shaders/talk.frag').read(),
                                     geometry_shader=open('shaders/talk.geom').read())

        # set up camera
        self.init_camera([1, 1, 2])
        self.prog['m_mvp'].write(self.camera['mat'])

        # load 1deg hgrid, decimate down the number of points so we have a chance to view it
        grid = np.load('hgrid.npy')
        decimation = 20
        points = grid[::decimation,::decimation,:]
        #points = grid[::decimation,:100:decimation,:]
        ny, nx, _ = points.shape

        # load up vertices into a vbo
        vbo = self.ctx.buffer(points.astype('f4'))

        # the tricky bit: construct the index array
        indices = []
        # loop over all quads
        for ix in range(nx - 1):
            for iy in range(ny - 1):
                indices.extend([iy*nx     + ix, iy*nx + ix+1, (iy+1)*nx + ix])
                indices.extend([(iy+1)*nx + ix, iy*nx + ix+1, (iy+1)*nx + ix+1])

        ivbo = self.ctx.buffer(np.asarray(indices, dtype=np.int32))
        self.vao = self.ctx.simple_vertex_array(self.prog, vbo, 'aPos', index_buffer=ivbo)

    def draw_gui(self):
        imgui.begin('Controls')
        _, self.gui['animate'] = imgui.checkbox('Animate', self.gui['animate'])
        _, self.gui['u_unwrap'] = imgui.drag_float('Unwrap', self.gui['u_unwrap'], 0.01, 0, 1)
        imgui.end()

    def render(self):
        self.draw_gui()
        if self.drag_camera():
            self.prog['m_mvp'].write(self.camera['mat'])
        
        self.ctx.clear(0., 0., 0., 0.)
        if self.gui['animate']:
            self.gui['u_unwrap'] = (np.sin(self.time()) + 1) / 2
            
        self.prog['u_unwrap'].value = self.gui['u_unwrap']
        self.vao.render()

if __name__ == '__main__':
    C().run()
