#version 450 core

in vec3 aPos;
out VS_OUT {
  vec4 color;
} vs_out;

uniform mat4 m_mvp;
uniform float u_unwrap;
uniform float u_z_offset;
uniform vec4 u_color;

const float rad_min = 0.8;

void main() {
  vec4 vPos = vec4(aPos, 1.0);
  // for drawing a flat sphere (water)
  if (u_z_offset == 0)
    vPos.z /= -6000 * 4;
  else
    vPos.z = -u_z_offset;

  // elevation and azimuth in spherical coords
  float phi = radians(aPos.x * 180 - 100);
  float theta = radians(aPos.y * 80);
  float rad = 1.0 - u_z_offset - (1.0 - rad_min) * (aPos.z / 6000);
  vec4 sPos = vec4(rad * cos(theta) * cos(phi),
		   rad * sin(theta),
		   -rad * cos(theta) * sin(phi),
		   1);
  
  gl_Position = m_mvp * mix(sPos, vPos, u_unwrap);
  float depth = 1.0 - (aPos.z / 6000);
  if (depth >= 0.95) {
    vs_out.color = u_color;
  } else {
    vs_out.color = vec4(vec3(depth), 1.0);
  }
}
