#!/usr/bin/env python

import glfw
import OpenGL.GL as gl
import moderngl
import pyassimp
import numpy as np
from pyrr import Matrix44, Matrix33, Vector3
import os.path

import imgui
from imgui.integrations.glfw import GlfwRenderer

def gen_wave_directions():
    # choose a set of directions
    directions = np.empty((4,2))
    primary_direction = np.random.randn(2)
    directions[0,:] = primary_direction / np.linalg.norm(primary_direction)
    def rot(theta):
        theta = np.radians(theta)
        return np.array([[np.cos(theta), -np.sin(theta)],
                         [np.sin(theta),  np.cos(theta)]])
    for i in range(1,4):
        directions[i,:] = rot(np.random.randn() * 30) @ directions[0,:]

    return directions

def init_model(ctx):
    with open('model.vert') as vert_file, open('diffuse.frag') as frag_file:
        prog = ctx.program(vertex_shader=vert_file.read(), fragment_shader=frag_file.read())
    prog['u_ambient'].value = 0
    prog['u_diffuse'].value = 1

    mesh = pyassimp.load('monkey.obj')

    vbo = ctx.buffer(np.hstack((mesh.meshes[0].vertices, mesh.meshes[0].normals)))
    index_vbo = ctx.buffer(mesh.meshes[0].faces)
    vao = ctx.simple_vertex_array(prog, vbo, 'in_vert', 'in_norm', index_buffer=index_vbo)

    # fixed light
    prog['light'].write(np.array([2, 2, 2], dtype=np.float32))

    return vao

def init_waves(ctx):
    with open('wave.vert') as vert_file, open('diffuse.frag') as frag_file, open('pass.geom') as geom_file:
        prog = ctx.program(vertex_shader=vert_file.read(),
                           fragment_shader=frag_file.read(),
                           geometry_shader=geom_file.read())

    prog['u_direction'].write(gen_wave_directions().astype('f4'))
    prog['u_ambient'].value = .1
    prog['u_diffuse'].value = .9
    prog['light'].write(np.array([2,2,2], dtype=np.float32))

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
    vbo_plane = ctx.buffer(plane_points.astype('f4'))

    plane_indices = []
    for i in range(plane_nx*(plane_ny - 1)):
        # skip end points
        if (i+1) % plane_nx == 0:
            continue
        plane_indices.append([i, i+1, i+plane_nx])
        plane_indices.append([i+plane_nx, i+1, i+plane_nx+1])
    ivbo_plane = ctx.buffer(np.asarray(plane_indices, dtype=np.int32))
    vao_plane = ctx.simple_vertex_array(prog, vbo_plane, 'in_vert', index_buffer=ivbo_plane)

    return vao_plane

def main():
    # initialisation
    window = impl_glfw_init()
    impl = GlfwRenderer(window)
    ctx = moderngl.create_context()
    width, height = glfw.get_window_size(window)

    # initialise model demo
    vao = init_model(ctx)
    prog = vao.program

    # load each program
    mat_proj = Matrix44.perspective_projection(45, width / height, 0.1, 100.0)
    mat_view = Matrix44.look_at(np.array([4., 3., 3.]),
                                np.array([0., 0., 0.]),
                                np.array([0., 1., 0.]))
    mat_model = Matrix44.identity()
    mat_camera = mat_proj * mat_view
    prog['u_model'].write(mat_model.astype('f4'))
    prog['u_normal'].write(mat_model.astype('f4'))

    # initialise waves demo
    vao_plane = init_waves(ctx)
    prog_plane = vao_plane.program

    prev_camera_pos = Vector3([5,5,5])
    last_camera_pos = prev_camera_pos
    plane_params = {'amplitude': 0.08, 'frequency': 3, 'speed': 1, 'steepness': 0.3}
    plane_sphere_radius = 2.5
    plane_sphericity = 0
    prog_plane['u_radius'].value = plane_sphere_radius
    prog_plane['u_blend'].value = plane_sphericity
    for k, v in plane_params.items():
        prog_plane['u_' + k].value = [v,v,v,v]

    # main loop state
    demo_selection = 0
    prev_mouse_down = False
    rot_speed = np.pi

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        imgui.new_frame()
        io = imgui.get_io()

        # set up the menu bar
        clicked_quit = False
        clicked_demo1 = False
        clicked_demo2 = False
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File", True):
                clicked_quit, _ = imgui.menu_item('Quit', 'Ctrl+Q', False, True)
                imgui.end_menu()

            if imgui.begin_menu("Demos", True):
                clicked_demo1, _ = imgui.menu_item('Model', 'F1', False, True)
                clicked_demo2, _ = imgui.menu_item('Waves', 'F2', False, True)
                imgui.end_menu()
            imgui.end_main_menu_bar()

        if clicked_quit or (io.keys_down[glfw.KEY_Q] and io.key_ctrl):
            exit(1)

        if io.keys_down[glfw.KEY_F1] or clicked_demo1:
            demo_selection = 0
        if io.keys_down[glfw.KEY_F2] or clicked_demo2:
            demo_selection = 1

        imgui.begin("Stats")
        imgui.text("Framerate: {}".format(io.framerate))
        if demo_selection == 0:
            imgui.text("Vertices: {}".format(vao.vertices))
        elif demo_selection == 1:
            imgui.text("Vertices: {}".format(vao_plane.vertices))
        _, demo_selection = imgui.combo("Demo", demo_selection, ["Monkey", "Plane\0"])
        imgui.end()

        ctx.clear(.2, .2, .2, 0.)
        ctx.enable(moderngl.DEPTH_TEST)

        if demo_selection == 0:
            # TODO: decompose rotation?
            changed = False
            if io.keys_down[glfw.KEY_RIGHT]:
                mat_model *= Matrix44.from_y_rotation(-io.delta_time * np.pi)
                changed = True
            if io.keys_down[glfw.KEY_LEFT]:
                mat_model *= Matrix44.from_y_rotation(io.delta_time * np.pi)
                changed = True
            if io.keys_down[glfw.KEY_DOWN]:
                mat_model *= Matrix44.from_x_rotation(-io.delta_time * np.pi)
                changed = True
            if io.keys_down[glfw.KEY_UP]:
                mat_model *= Matrix44.from_x_rotation(io.delta_time * np.pi)
                changed = True

            # set model-view-projection matrix
            # we don't strictly need to take the inverse transpose
            # if the model matrix doesn't scale
            if changed:
                prog['u_model'].write(mat_model.astype('f4'))
                prog['u_normal'].write(mat_model.inverse.transpose().astype('f4').tobytes())
            prog['u_camera'].write(mat_camera.astype('f4'))
            vao.render()
        elif demo_selection == 1:
            imgui.begin("Params")
            for k in plane_params.keys():
                changed, plane_params[k] = imgui.drag_float(k.capitalize(), plane_params[k], 0.01)
                if changed:
                    v = plane_params[k]
                    prog_plane['u_' + k].value = [v,v,v,v]

            changed, plane_sphere_radius = imgui.drag_float("Radius", plane_sphere_radius, 0.1)
            if changed:
                prog_plane['u_radius'].value = plane_sphere_radius

            changed, plane_sphericity = imgui.drag_float("Sphericity", plane_sphericity, 0.01, 0, 1)
            if changed:
                prog_plane['u_blend'].value = plane_sphericity

            if imgui.button("Randomise directions"):
                prog_plane['u_direction'].write(gen_wave_directions().astype('f4'))

            prog_plane['u_time'].value = glfw.get_time()

            imgui.end()

            if not imgui.is_any_item_active():
                mx, my = imgui.get_mouse_drag_delta()
            else:
                mx, my = (0, 0)

            camera_pos = Matrix33.from_z_rotation(rot_speed * mx / width) * Matrix33.from_x_rotation(-rot_speed * my / height) * prev_camera_pos
            if prev_mouse_down and not io.mouse_down[0]:
                prev_camera_pos = last_camera_pos
                camera_pos = last_camera_pos
            last_camera_pos = camera_pos
            prev_mouse_down = io.mouse_down[0]
            mat_plane_view = Matrix44.look_at(camera_pos,
                                              np.array([0, 0, 0]),
                                              np.array([0, 0, 1]))
            mat_plane_camera = mat_proj * mat_plane_view
            prog_plane['u_camera'].write(mat_plane_camera.astype('f4'))

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
