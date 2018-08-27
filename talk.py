#!/usr/bin/env python

import g
import imgui
import moderngl
import numpy as np
from pyrr import Matrix44

class C(g.App):
    def __init__(self):
        super().__init__(gui=True)

        # GUI state variables
        self.gui = {
            'u_unwrap': 0,
            'animate': False,
            'u_color': (.1, .1, 0.),
        }

        # load shaders
        self.prog = self.ctx.program(vertex_shader=open('shaders/talk.vert').read(),
                                     fragment_shader=open('shaders/talk.frag').read(),
                                     geometry_shader=open('shaders/talk.geom').read())

        # set up camera
        self.init_camera([1, 1, 2])
        self.prog['m_mvp'].write(self.camera['mat'])

        # load 1deg hgrid, halve the number of points so that the grid agrees with topography
        decimation = 4
        grid = np.load('hgrid.npy')
        #points = grid[::decimation,::decimation,:]
        grid = grid[:-1:decimation,:-1:decimation,:]
        ny, nx, _ = grid.shape

        # load 1deg topography
        topog_raw = np.load('topog.npy')
        # centre nearer australia
        topog = topog_raw[::decimation,::decimation]
        topog = np.repeat(np.repeat(topog, 2, axis=0), 2, axis=1)

        points = np.dstack((grid, topog))
        vbo = self.ctx.buffer(points.astype('f4'))

        points_flat = np.dstack((grid, np.zeros(topog.shape)))
        vbo_flat = self.ctx.buffer(points_flat.astype('f4'))

        # the tricky bit: construct the index array
        indices = []
        # loop over all quads
        for ix in range(nx - 1):
            for iy in range(ny - 1):
                indices.extend([iy*nx + ix,   iy*nx + ix+1,     (iy+1)*nx + ix])
                indices.extend([iy*nx + ix+1, (iy+1)*nx + ix+1, (iy+1)*nx + ix])

        ivbo = self.ctx.buffer(np.asarray(indices, dtype=np.int32))
        self.vao = self.ctx.simple_vertex_array(self.prog, vbo, 'aPos', index_buffer=ivbo)
        self.vao_flat = self.ctx.simple_vertex_array(self.prog, vbo_flat, 'aPos', index_buffer=ivbo)

    def draw_gui(self):
        imgui.begin('Controls')
        _, self.gui['animate'] = imgui.checkbox('Animate', self.gui['animate'])
        _, self.gui['u_unwrap'] = imgui.drag_float('Unwrap', self.gui['u_unwrap'], 0.01, 0, 1)
        _, self.gui['u_color'] = imgui.color_edit3('Land', *self.gui['u_color'])
        imgui.end()

        if self.gui['animate']:
            self.gui['u_unwrap'] = (np.sin(self.time()) + 1) / 2

    def render(self):
        self.draw_gui()
        if self.drag_camera():
            self.prog['m_mvp'].write(self.camera['mat'])
        
        self.ctx.clear(0., 0., 0., 0.)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)

        # set uniforms from gui
        self.prog['u_unwrap'].value = self.gui['u_unwrap']

        # render topography
        self.prog['u_color'].value = self.gui['u_color'] + (1.,)
        self.prog['u_z_offset'].value = 0.
        self.vao.render()

        # render water surface
        self.prog['u_color'].value = (.3, .3, 1., 0.5)
        self.prog['u_z_offset'].value = 0.01
        self.vao_flat.render()

if __name__ == '__main__':
    C().run()
