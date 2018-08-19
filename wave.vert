#version 330 core

in vec2 in_vert;
out vec3 v_vert;
out vec3 v_norm;

const int num_waves = 4;

uniform mat4 u_camera;
uniform float u_time;
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

  gl_Position = u_camera * vec4(v_vert, 1);
}
