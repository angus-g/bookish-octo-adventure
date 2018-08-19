#version 330 core

in vec3 in_vert;
in vec3 in_norm;
out vec3 f_vert;
out vec3 f_norm;

uniform mat4 u_model;
uniform mat4 u_camera;

void main() {
  vec4 h_vert = u_model * vec4(in_vert, 1); // transformed vert
  f_vert = vec3(h_vert);
  gl_Position = u_camera * h_vert;
  f_norm = mat3(transpose(inverse(u_model))) * in_norm;
}
