#version 450 core

in GS_OUT {
  vec4 color;
  vec3 texCoord;
  vec2 quad;
} fs_in;

out vec4 color;

uniform sampler2DArray tex;
uniform bool use_tex;

void main() {
  if (abs(round(fs_in.quad.y) - fs_in.quad.y) <= 0.1) {
    // if we're at the edge of a quad
    color = vec4(1.0, 1.0, 1.0, 1.0);
  } else if (use_tex) {
    color = vec4(texture(tex, fs_in.texCoord).rgb, 0.8);
  } else {
    color = fs_in.color;
  }
}
