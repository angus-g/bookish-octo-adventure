import glfw
import moderngl
import numpy as np
from PIL import Image
from pyrr import Matrix44, Matrix33, Vector3

import warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='imgui.integrations')

import imgui
from imgui.integrations.glfw import GlfwRenderer

class App(object):
    def __init__(self, gui=False, width=800, height=600, window_name='opengl'):
        self.width = width
        self.height = height

        if not glfw.init():
            raise RuntimeError('could not init glfw')

        hints = ((glfw.CONTEXT_VERSION_MAJOR, 4),
                 (glfw.CONTEXT_VERSION_MINOR, 5),
                 (glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE))
        for hint in hints:
            glfw.window_hint(*hint)

        self.window = glfw.create_window(int(self.width), int(self.height),
                                         window_name, None, None)
        glfw.make_context_current(self.window)
        def viewport_func(window, width, height):
            self.width = width
            self.height = height
            self.update_camera(update_proj=True)
            self.ctx.viewport = (0, 0, self.width, self.height)
        glfw.set_framebuffer_size_callback(self.window, viewport_func)

        if not self.window:
            glfw.terminate()
            raise RuntimeError('could not create glfw window')

        self.gui_impl = None
        if gui:
            self.gui_impl = GlfwRenderer(self.window)

        self.ctx = moderngl.create_context()
        self.ctx.viewport = (0, 0, self.width, self.height)

    def init_camera(self, pos=[0, 0, 0]):
        self.camera = {
            'center': Vector3(pos),
            'saved_center': Vector3(pos),
            'look_at': Vector3(),
            'up': Vector3([0, 1, 0]),
            'rot_speed': np.pi,
            'mouse_down': False,
        }
        self.update_camera(update_proj=True)

    def update_camera(self, update_proj=False):
        if update_proj:
            self.camera['proj'] = Matrix44.perspective_projection(45.0, self.width / self.height, 0.1, 1000.0)

        self.camera['view'] = Matrix44.look_at(self.camera['center'],
                                               self.camera['look_at'],
                                               self.camera['up'])

        self.camera['mat'] = (self.camera['proj'] * self.camera['view']).astype('f4')

    def drag_camera(self):
        if not imgui.is_any_item_active():
            mx, my = imgui.get_mouse_drag_delta()
        else:
            mx, my = 0, 0

        # if we just released the mouse, save the new camera position
        if self.camera['mouse_down'] and not self.io.mouse_down[0]:
            self.camera['saved_center'] = self.camera['center']
        self.camera['mouse_down'] = self.io.mouse_down[0]

        # no drag, don't do anything
        if mx == 0 and my == 0:
            return False

        # calculate the camera position according to the current drag
        # this is a rotation relative to the saved position
        self.camera['center'] = Matrix33.from_y_rotation(self.camera['rot_speed'] * mx / self.width) \
            * Matrix33.from_x_rotation(self.camera['rot_speed'] * my / self.height) \
            * self.camera['saved_center']
        self.update_camera()

        # camera has changed
        return True

    def texture(self, filename):
        img = Image.open(filename).convert('RGB')
        tex = self.ctx.texture(img.size, 3, img.tobytes())

        return tex

    def time(self):
        return glfw.get_time()

    def run(self):
        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            if self.gui_impl is not None:
                self.gui_impl.process_inputs()
                self.io = imgui.get_io()
                imgui.new_frame()

            if glfw.get_key(self.window, glfw.KEY_ESCAPE) == glfw.PRESS:
                glfw.set_window_should_close(self.window, True)

            self.render()

            if self.gui_impl is not None:
                imgui.render()
                self.gui_impl.render(imgui.get_draw_data())

            glfw.swap_buffers(self.window)

        if self.gui_impl is not None:
            self.gui_impl.shutdown()
            imgui.shutdown()
        glfw.terminate()
