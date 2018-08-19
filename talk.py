#!/usr/bin/env python

import glfw
import OpenGL.GL as gl
import moderngl
import pyassimp
import numpy as np
from pyrr import Matrix44
import os.path

import imgui
from imgui.integrations.glfw import GlfwRenderer

def main():
    window = impl_glfw_init()
    impl = GlfwRenderer(window)
    ctx = moderngl.create_context()

    mesh = pyassimp.load('monkey.obj')

    with open('model.vert') as vert_file, open('diffuse.frag') as frag_file:
        prog = ctx.program(vertex_shader=vert_file.read(), fragment_shader=frag_file.read())
    prog['u_ambient'].value = 0
    prog['u_diffuse'].value = 1

    with open('wave.vert') as vert_file, open('diffuse.frag') as frag_file, open('wireframe.geom') as geom_file:
        prog_plane = ctx.program(vertex_shader=vert_file.read(),
                                 fragment_shader=frag_file.read(),
                                 geometry_shader=geom_file.read())
    directions = np.random.randn(4,2)
    directions /= np.linalg.norm(directions, axis=1)[:,None]

    prog_plane['u_direction'].write(directions.astype('f4'))
    prog_plane['u_ambient'].value = .5
    prog_plane['u_diffuse'].value = .5

    vbo = ctx.buffer(np.hstack((mesh.meshes[0].vertices, mesh.meshes[0].normals)))
    index_vbo = ctx.buffer(mesh.meshes[0].faces)
    vao = ctx.simple_vertex_array(prog, vbo, 'in_vert', 'in_norm', index_buffer=index_vbo)
    uni_model = prog['u_model']
    uni_camera = prog['u_camera']

    # fixed light
    uni_light = prog['light']
    uni_light.write(np.array([2, 2, 2], dtype=np.float32))
    
    width, height = glfw.get_window_size(window)
    mat_proj = Matrix44.perspective_projection(45, width / height, 0.1, 100.0)
    mat_view = Matrix44.look_at(np.array([4., 3., 3.]),
                                np.array([0., 0., 0.]),
                                np.array([0., 1., 0.]))
    mat_model = Matrix44.identity()
    mat_camera = mat_proj * mat_view

    x_coords = np.linspace(-10., 10., 50)
    plane_points = np.empty((len(x_coords), len(x_coords), 2), dtype=np.float32)
    plane_points[..., 0] = x_coords[:, None]
    plane_points[..., 1] = x_coords
    vbo_plane = ctx.buffer(plane_points)
    plane_indices = []
    for i in range(len(x_coords)*(len(x_coords) - 1)):
        # skip end points
        if (i+1) % len(x_coords) == 0:
            continue
        plane_indices.append([i, i+1, i+len(x_coords)])
        plane_indices.append([i+len(x_coords), i+1, i+len(x_coords)+1])
    ivbo_plane = ctx.buffer(np.asarray(plane_indices, dtype=np.int32))
    vao_plane = ctx.simple_vertex_array(prog_plane, vbo_plane, 'in_vert', index_buffer=ivbo_plane)
    mat_plane_view = Matrix44.look_at(np.array([5, 5, 5]),
                                      np.array([0, 0, 0]),
                                      np.array([0, 0, 1]))
    mat_plane_camera = mat_proj * mat_plane_view
    prog_plane['u_camera'].write(mat_plane_camera.astype('f4'))
    plane_params = {'amplitude': 0.1, 'frequency': 1, 'speed': 1, 'steepness': 0.5}
    for k, v in plane_params.items():
        prog_plane['u_' + k].value = [v,v,v,v]

    demo_selection = 0

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        imgui.new_frame()

        io = imgui.get_io()

        clicked_quit = False
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File", True):
                clicked_quit, selected_quit = imgui.menu_item(
                    'Quit', 'Ctrl+Q', False, True
                )


                imgui.end_menu()
            imgui.end_main_menu_bar()

        if clicked_quit or (io.keys_down[glfw.KEY_Q] and io.key_ctrl):
            exit(1)

        if io.keys_down[glfw.KEY_F1]:
            demo_selection = 0
        if io.keys_down[glfw.KEY_F2]:
            demo_selection = 1

        imgui.begin("Stats")
        imgui.text("Framerate: {}".format(io.framerate))
        if demo_selection == 0:
            imgui.text("Vertices: {}".format(vao.vertices))
        elif demo_selection == 1:
            imgui.text("Vertices: {}".format(vao_plane.vertices))
        _, demo_selection = imgui.combo("Demo", demo_selection, ["Monkey", "Plane\0"])
        imgui.end()

        ctx.clear(0., 0., .4, 0.)
        ctx.enable(moderngl.DEPTH_TEST)

        if demo_selection == 0:
            # TODO: decompose rotation?
            if io.keys_down[glfw.KEY_RIGHT]:
                mat_model *= Matrix44.from_y_rotation(-io.delta_time * np.pi)
            if io.keys_down[glfw.KEY_LEFT]:
                mat_model *= Matrix44.from_y_rotation(io.delta_time * np.pi)
            if io.keys_down[glfw.KEY_DOWN]:
                mat_model *= Matrix44.from_x_rotation(-io.delta_time * np.pi)
            if io.keys_down[glfw.KEY_UP]:
                mat_model *= Matrix44.from_x_rotation(io.delta_time * np.pi)

            # set model-view-projection matrix
            uni_model.write(mat_model.astype('f4'))
            uni_camera.write(mat_camera.astype('f4'))
            vao.render()
        elif demo_selection == 1:
            imgui.begin("Params")
            for k in plane_params.keys():
                changed, plane_params[k] = imgui.drag_float(k.capitalize(), plane_params[k], 0.01)
                if changed:
                    v = plane_params[k]
                    prog_plane['u_' + k].value = [v,v,v,v]

            prog_plane['u_time'].value = glfw.get_time()

            imgui.end()
            vao_plane.render()

        # render gui on top
        imgui.render()
        impl.render(imgui.get_draw_data())
        
        glfw.swap_buffers(window)

    impl.shutdown()
    imgui.shutdown()
    glfw.terminate()

def impl_glfw_init():
    width, height = 1280, 720
    window_name = 'minimal imgui/glfw3 example'

    if not glfw.init():
        print('Could not init opengl context')
        exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

    window = glfw.create_window(
        int(width), int(height), window_name, None, None
    )
    glfw.make_context_current(window)

    if not window:
        glfw.terminate()
        print('Could not init window')
        exit(1)

    return window

if __name__ == '__main__':
    main()
