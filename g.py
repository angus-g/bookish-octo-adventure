import glfw
import moderngl
from PIL import Image
from pyrr import Matrix44

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

        if not self.window:
            glfw.terminate()
            raise RuntimeError('could not create glfw window')

        self.gui_impl = None
        if gui:
            self.gui_impl = GlfwRenderer(self.window)

        self.ctx = moderngl.create_context()

    def init_camera(self, pos=[0, 0, 0]):
        self.camera = {
            'center': pos, 'look_at': [0, 0, 0], 'up': [0, 1, 0]
        }
        self.camera['proj'] = Matrix44.perspective_projection(45.0, self.width / self.height, 0.1, 1000.0)
        self.camera['view'] = Matrix44.look_at(self.camera['center'],
                                               self.camera['look_at'],
                                               self.camera['up'])
        self.update_camera()

    def update_camera(self):
        self.camera['mat'] = (self.camera['proj'] * self.camera['view']).astype('f4')

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
