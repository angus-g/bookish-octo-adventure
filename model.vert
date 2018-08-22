#version 330 core

in vec3 in_vert;
in vec3 in_norm;
in vec2 in_texcoord;
out vec3 f_vert;
out vec3 f_norm;
out vec2 f_texcoord;

uniform mat4 u_model;
uniform mat4 u_normal;
uniform mat4 u_camera;
uniform float u_unwrap_frac;

void main() {
  vec3 lerp_vert = mix(in_vert, vec3(in_texcoord, 0), u_unwrap_frac);
  vec4 h_vert = u_model * vec4(lerp_vert, 1); // transformed vert
  f_vert = vec3(h_vert);
  gl_Position = u_camera * h_vert;
  f_norm = vec3(u_normal * vec4(in_norm, 0));
  f_texcoord = in_texcoord;
}
