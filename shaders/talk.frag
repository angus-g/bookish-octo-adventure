#version 450 core

in GS_OUT {
  float depth;
} fs_in;

out vec3 color;

uniform vec3 u_land_color;

void main() {
  if (fs_in.depth >= 0.95) {
    color = u_land_color;
  } else {
    color = vec3(fs_in.depth);
  }
}
