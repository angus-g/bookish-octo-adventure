#version 330 core

in vec3 f_vert;
in vec3 f_norm;
out vec4 color;
uniform vec3 light;
uniform float u_ambient;
uniform float u_diffuse;

void main() {
  vec3 norm = normalize(f_norm);
  vec3 light_dir = normalize(light - f_vert);

  float diff = max(dot(norm, light_dir), 0.0);
  vec3 diffuse = diff * vec3(0, 0, 1);
  color = vec4(vec3(1, 1, 1) * u_ambient + diffuse * u_diffuse, 1);
}
