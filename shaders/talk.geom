#version 450 core

layout (triangles) in;
layout (line_strip, max_vertices=4) out;
//layout (points, max_vertices=3) out;

void main() {
  for (int i = 0; i < gl_in.length(); i++) {
    gl_Position = gl_in[i].gl_Position;
    EmitVertex();
  }
  gl_Position = gl_in[0].gl_Position;
  EmitVertex();
  EndPrimitive();
}
