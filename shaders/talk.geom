#version 450 core

layout (triangles) in;
layout (triangle_strip, max_vertices=4) out;
//layout (points, max_vertices=3) out;

in VS_OUT {
  float depth;
} gs_in[];

out GS_OUT {
  float depth;
} gs_out;

void main() {
  for (int i = 0; i < gl_in.length(); i++) {
    gl_Position = gl_in[i].gl_Position;
    gs_out.depth = gs_in[i].depth;

    EmitVertex();
  }
  gl_Position = gl_in[0].gl_Position;
  gs_out.depth = gs_in[0].depth;
  EmitVertex();
  EndPrimitive();
}
