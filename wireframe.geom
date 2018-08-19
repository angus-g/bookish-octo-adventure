#version 330 core

layout (triangles) in;
layout (line_strip, max_vertices=3) out;

in vec3 v_vert[];
in vec3 v_norm[];
out vec3 f_vert;
out vec3 f_norm;

void main() {
  for (int i = 0; i < gl_in.length(); i++) {
    f_vert = v_vert[i];
    f_norm = v_norm[i];
    gl_Position = gl_in[i].gl_Position;
    EmitVertex();
  }
  EndPrimitive();
}
