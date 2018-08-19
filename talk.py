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

    vert_source = '''
#version 330 core

in vec3 in_vert;
in vec3 in_norm;
out vec3 v_vert;
out vec3 v_norm;
uniform mat4 MVP;

void main() {
  gl_Position = MVP * vec4(in_vert, 1);
  v_vert = in_vert;
  v_norm = in_norm;
}'''
    frag_source = '''
#version 330 core

in vec3 v_vert;
in vec3 v_norm;
out vec4 color;
uniform vec3 light;

void main() {
  vec3 norm = normalize(v_norm);
  vec3 light_dir = normalize(light - v_vert);

  float diff = max(dot(norm, light_dir), 0.0);
  vec3 diffuse = diff * vec3(1, 0, 0);
  color = vec4(diffuse, 1);
}'''
    prog = ctx.program(vertex_shader=vert_source, fragment_shader=frag_source)

    vbo = ctx.buffer(np.hstack((mesh.meshes[0].vertices, mesh.meshes[0].normals)))
    index_vbo = ctx.buffer(mesh.meshes[0].faces)
    vao = ctx.simple_vertex_array(prog, vbo, 'in_vert', 'in_norm', index_buffer=index_vbo)
    uni_mvp = prog['MVP']

    # fixed light
    uni_light = prog['light']
    uni_light.write(np.array([2, 2, 2], dtype=np.float32))
    
    width, height = glfw.get_window_size(window)
    mat_proj = Matrix44.perspective_projection(45, width / height, 0.1, 100.0)
    mat_view = Matrix44.look_at(np.array([4., 3., 3.]),
                                       np.array([0., 0., 0.]),
                                       np.array([0., 1., 0.]))
    mat_model = Matrix44.identity()

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

        imgui.begin("Stats")
        imgui.text("Framerate: {}".format(io.framerate))
        imgui.text("Vertices: {}".format(mesh.meshes[0].vertices.shape[0]))
        imgui.end()

        # TODO: decompose rotation?
        if io.keys_down[glfw.KEY_RIGHT]:
            mat_model = mat_model @ Matrix44.from_y_rotation(-io.delta_time * np.pi)
        if io.keys_down[glfw.KEY_LEFT]:
            mat_model = mat_model @ Matrix44.from_y_rotation(io.delta_time * np.pi)

        ctx.clear(0., 0., .4, 0.)
        ctx.enable(moderngl.DEPTH_TEST)

        # set model-view-projection matrix
        mat_mvp = mat_proj * mat_view * mat_model
        uni_mvp.write(mat_mvp.astype('f4'))
        vao.render()

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
