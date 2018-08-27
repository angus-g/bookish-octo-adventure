#version 450 core

layout (triangles) in;
layout (triangle_strip, max_vertices=4) out;
//layout (points, max_vertices=3) out;

in VS_OUT {
  vec4 color;
} gs_in[];

out GS_OUT {
  vec4 color;
} gs_out;

void main() {
  for (int i = 0; i < gl_in.length(); i++) {
    gl_Position = gl_in[i].gl_Position;
    gs_out.color = gs_in[i].color;

    EmitVertex();
  }
  gl_Position = gl_in[0].gl_Position;
  gs_out.color = gs_in[0].color;
  EmitVertex();
  EndPrimitive();
}
