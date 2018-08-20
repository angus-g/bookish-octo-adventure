#!/usr/bin/env python

import glfw
import OpenGL.GL as gl
import moderngl
import numpy as np
from pyrr import Matrix44, Matrix33, Vector3
import os.path

import imgui
from imgui.integrations.glfw import GlfwRenderer

from waves import Waves
from model import Model

def main():
    # initialisation
    window = impl_glfw_init()
    impl = GlfwRenderer(window)
    ctx = moderngl.create_context()
    width, height = glfw.get_window_size(window)

    # initialise model demo
    model = Model(ctx, (width, height))
    prog = model.prog

    # initialise waves demo
    waves = Waves(ctx, (width, height))
    prog_plane = waves.prog

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
            imgui.text("Vertices: {}".format(model.vao.vertices))
        elif demo_selection == 1:
            imgui.text("Vertices: {}".format(waves.vao.vertices))
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
                model.update_camera()
            model.render()
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
                waves.gen_wave_directions()

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
            waves.update_camera(camera_pos)
            waves.render(glfw.get_time())

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
