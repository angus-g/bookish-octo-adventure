#version 450 core

layout (triangles) in;
layout (triangle_strip, max_vertices=4) out;
//layout (line_strip, max_vertices=4) out;

in VS_OUT {
  vec4 color;
  vec3 texCoord;
  vec2 quad;
} gs_in[];

out GS_OUT {
  vec4 color;
  vec3 texCoord;
  vec2 quad;
} gs_out;

void main() {
  for (int i = 0; i < gl_in.length(); i++) {
    gl_Position = gl_in[i].gl_Position;
    gs_out.color = gs_in[i].color;
    gs_out.texCoord = gs_in[i].texCoord;
    gs_out.quad = gs_in[i].quad;

    EmitVertex();
  }
  gl_Position = gl_in[0].gl_Position;
  gs_out.color = gs_in[0].color;
  gs_out.texCoord = gs_in[0].texCoord;
  gs_out.quad = gs_in[0].quad;
  EmitVertex();
  EndPrimitive();
}
