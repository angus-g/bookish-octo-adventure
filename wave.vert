#version 330 core

in vec2 in_vert;
out vec3 v_vert;
out vec3 v_norm;

const int num_waves = 4;

uniform mat4 u_camera;
uniform float u_time;
uniform float u_radius;
uniform float u_blend;
uniform float u_amplitude[num_waves];
uniform vec2 u_direction[num_waves];
uniform float u_frequency[num_waves];
uniform float u_speed[num_waves];
uniform float u_steepness[num_waves];

void main() {
  v_vert.xy = in_vert.xy;
  v_vert.z = 0;
  v_norm = vec3(0, 0, 1);
  for (int i = 0; i < num_waves; i++) {
    float dir = dot(u_direction[i], in_vert.xy);
    float steepness = u_steepness[i] / (u_frequency[i] * u_amplitude[i] * num_waves);
    v_vert.x += steepness * u_amplitude[i] * u_direction[i].x * in_vert.x
              * cos(dir * u_frequency[i] + u_time * u_speed[i]);
    v_vert.y += steepness * u_amplitude[i] * u_direction[i].y * in_vert.y
              * cos(dir * u_frequency[i] + u_time * u_speed[i]);
    v_vert.z += u_amplitude[i] * sin(dir * u_frequency[i] + u_time * u_speed[i]);

    v_norm.x += -u_frequency[i] * u_direction[i].x * in_vert.x * u_amplitude[i]
              * cos(dir * u_frequency[i] + u_time * u_speed[i]);
    v_norm.y += -u_frequency[i] * u_direction[i].y * in_vert.y * u_amplitude[i]
              * cos(dir * u_frequency[i] + u_time * u_speed[i]);
    v_norm.z += -steepness * u_frequency[i] * u_amplitude[i]
              * sin(dir * u_frequency[i] + u_time * u_speed[i]);
  }

  float phi = radians(180) * v_vert.x / 10;
  //float theta = sign(v_vert.y) * 2 * atan(exp(abs(v_vert.y / 10)));
  float theta = radians(90) * v_vert.y / 10;

  float radius = u_radius + v_vert.z;

  vec3 vert_spherical, norm_spherical;
  vert_spherical.x = radius * cos(theta) * cos(phi);
  vert_spherical.y = radius * cos(theta) * sin(phi);
  vert_spherical.z = radius * sin(theta);

  // NB: matrices are constructed by column
  mat3 rotx = mat3(1, 0, 0, 0, 0, 1, 0, -1, 0);
  mat3 roty = mat3(cos(phi), 0, -sin(phi), 0, 1, 0, sin(phi), 0, cos(phi));
  mat3 rotz = mat3(cos(theta), sin(theta), 0, -sin(theta), cos(theta), 0, 0, 0, 1);

  norm_spherical = rotx * roty * rotz * v_norm;

  v_vert = mix(v_vert, vert_spherical, u_blend);
  v_norm = mix(v_norm, norm_spherical, u_blend);

  gl_Position = u_camera * vec4(v_vert, 1);
}
