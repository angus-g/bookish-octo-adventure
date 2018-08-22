#version 330 core

in vec3 f_vert;
in vec3 f_norm;
in vec2 f_texcoord;
out vec4 color;
uniform vec3 light;
uniform float u_ambient;
uniform float u_diffuse;
//uniform bool u_texcolor;

void main() {
  vec3 norm = normalize(f_norm);
  vec3 light_dir = normalize(light - f_vert);

  float diff = max(dot(norm, light_dir), 0.0);
  vec3 diffuse = diff * vec3(.1, .1, 1);
  color = vec4(vec3(1, 1, 1) * u_ambient + diffuse * u_diffuse, 1);
  /*
  if (u_texcolor) {
    color = vec4(f_texcoord, 1, 1);
  } else {
    color = vec4(vec3(1, 1, 1) * u_ambient + diffuse * u_diffuse, 1);
  }
  */
}
