#!/usr/bin/env python

import g
import imgui
import moderngl
import numpy as np
from pyrr import Matrix44

num_pieces = 15

class C(g.App):
    def __init__(self):
        super().__init__(gui=True, width=1280, height=800)

        # GUI state variables
        # these are directly controllable through some kind of GUI element
        self.gui = {
            'u_unwrap': 0,
            'u_separation': 0,
            'animate': False,
            'isolate': 0,
            'layers': 1,
            'piece': (num_pieces//2, num_pieces//2),
            'num_pieces': 6,
            'cam_init': (0, -0.5, 4),
            'cam_final': (0, -1.0, 0),
        }

        # load shaders
        # we have a pretty standard vertex-geometry-fragment shader setup
        # the geometry shader exists only to toggle wireframe on/off
        self.prog = self.ctx.program(vertex_shader=open('shaders/talk.vert').read(),
                                     fragment_shader=open('shaders/talk.frag').read(),
                                     geometry_shader=open('shaders/talk.geom').read())

        # set up camera
        self.init_camera(self.gui['cam_init'])
        self.prog['m_mvp'].write(self.camera['mat'])

        # load 1deg hgrid, halve the number of points so that the grid agrees with topography
        decimation = 2
        data = np.load('data.npz')
        grid = data['grid'][::decimation,::decimation,:]
        ny, nx, _ = grid.shape

        # load 1deg topography
        # centre nearer australia
        topog = data['topo'][::decimation,::decimation]
        topog = np.repeat(np.repeat(topog, 2, axis=0), 2, axis=1)
        topog = np.vstack((topog[0,:], topog))
        topog = np.hstack((topog[:,[0]], topog))

        # build up the vertex buffers for vertex positions (hgrid
        # combined with topo) and the i,j index of the quad to which
        # the vertex belongs
        points = np.dstack((grid, topog)).reshape(-1, 3)
        point_buf = []
        quad_buf = []
        piece_idxes = {}
        cur_idx = 0
        for ix in range(nx - 1):
            for iy in range(ny - 1):
                indices = [iy*nx + ix,   iy*nx + ix+1,     (iy+1)*nx + ix,
                           iy*nx + ix+1, (iy+1)*nx + ix+1, (iy+1)*nx + ix]

                # associate this quad with a discrete piece
                piece = [min(num_pieces-1, int(num_pieces * ix / (nx-2))),
                         min(num_pieces-1, int(num_pieces * iy / (ny-2)))]

                # actual vertices of the quad by indexing into our vertices
                point_buf.extend(points[i] for i in indices)
                # index of this quad (for "exploding" effect)
                quad_buf.extend([p / (num_pieces-1) - 0.5 for p in piece] * 6)

                # we could do this analytically, but I'm lazy
                k = '{}.{}'.format(*piece)
                if k not in piece_idxes:
                    piece_idxes[k] = []
                piece_idxes[k].extend(range(cur_idx, cur_idx+6))
                cur_idx += 6

        self.num_piece_vertices = len(piece_idxes['0.0'])
        piece_idx = np.empty((num_pieces, num_pieces, self.num_piece_vertices))
        for ix in range(num_pieces):
            for iy in range(num_pieces):
                piece_idx[iy,ix,:] = piece_idxes['{}.{}'.format(ix, iy)]


        vbo = self.ctx.buffer(np.asarray(point_buf, dtype=np.float32))
        vboq = self.ctx.buffer(np.asarray(quad_buf, dtype=np.float32))
        self.ivbo = self.ctx.buffer(np.asarray(piece_idx, dtype=np.int32))
        self.vao = self.ctx.vertex_array(self.prog, [(vbo, '3f', 'aPos'),
                                                     (vboq, '2f', 'aQuad')], index_buffer=self.ivbo)

    def draw_gui(self):
        imgui.begin('Controls')
        imgui.text('Framerate: {:.2f}'.format(self.io.framerate))
        imgui.text('Vertices: {}'.format(self.vao.vertices))
        _, self.gui['animate'] = imgui.checkbox('Animate', self.gui['animate'])
        _, self.gui['u_unwrap'] = imgui.drag_float('Unwrap', self.gui['u_unwrap'], 0.01, 0, 1)
        _, self.gui['u_separation'] = imgui.drag_float('Separation', self.gui['u_separation'], 0.01, 0, 1)
        cam_changed, self.gui['isolate'] = imgui.drag_float('Isolate', self.gui['isolate'], 0.01, 0, 1)
        _, self.gui['piece'] = imgui.drag_int2('Piece', *self.gui['piece'], 0.1, 0, num_pieces-1)
        _, self.gui['num_pieces'] = imgui.drag_int('Num pieces', self.gui['num_pieces'], 0.1, 0)
        _, self.gui['layers'] = imgui.drag_int('Layers', self.gui['layers'], 0.1, 0)

        if self.gui['animate']:
            self.gui['u_unwrap'] = (np.sin(self.time()) + 1) / 2

        # for some reason imgui isn't enforcing these minimums
        self.gui['layers'] = max(self.gui['layers'], 0)
        self.gui['num_pieces'] = max(self.gui['num_pieces'], 0)

        if cam_changed:
            cam_pos = self.gui['isolate'] * np.array(self.gui['cam_final']) \
                + (1.0 - self.gui['isolate']) * np.array(self.gui['cam_init'])

            # look at middle of piece
            x_coord = self.gui['isolate'] * ((self.gui['piece'][0] + self.gui['num_pieces']/2) / num_pieces - 0.5)
            # avoid some weird perspective stuff
            z_coord = self.gui['isolate'] * -.3
            cam_pos[0] = x_coord
            self.camera['look_at'] = (x_coord, 0, z_coord)

            # update camera
            self.move_camera(cam_pos)
            self.update_camera()
            self.prog['m_mvp'].write(self.camera['mat'])

        imgui.end()

    def render(self):
        self.draw_gui()
        if self.drag_camera():
            self.prog['m_mvp'].write(self.camera['mat'])

        self.ctx.clear(0., 0., 0., 0.)
        self.ctx.enable(moderngl.DEPTH_TEST | moderngl.BLEND | moderngl.CULL_FACE)

        # set uniforms from gui
        self.prog['u_unwrap'].value = self.gui['u_unwrap']
        self.prog['u_separation'].value = self.gui['u_separation']

        # calculate offset of selected piece
        vertices = -1
        first_vertex = 0
        if self.gui['isolate'] == 1:
            vertices = self.num_piece_vertices * self.gui['num_pieces']
            first_vertex = self.num_piece_vertices * (self.gui['piece'][1] * num_pieces + self.gui['piece'][0])

        # render topography
        self.prog['u_color'].value = (.1, .1, 0., 1.0)
        self.prog['u_z_offset'].value = 0.
        self.vao.render(vertices=vertices, first=first_vertex)

        # render water surface
        self.prog['u_color'].value = (.3, .3, 1., 0.5)
        self.prog['u_z_offset'].value = 0.01
        self.vao.render(vertices=vertices, first=first_vertex, instances=self.gui['layers'])

if __name__ == '__main__':
    C().run()
