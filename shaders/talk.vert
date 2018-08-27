#version 450 core

in vec3 aPos;
out VS_OUT {
  float depth;
} vs_out;

uniform mat4 m_mvp;
uniform float u_unwrap;

const float rad_min = 0.8;

void main() {
  vec4 vPos = vec4((aPos + vec3(100, 0, 0)) / vec3(180, 80, -6000 * 4), 1.0);

  // elevation and azimuth in spherical coords
  float phi = radians(aPos.x);
  float theta = radians(aPos.y);
  float rad = 1.0 - (1.0 - rad_min) * (aPos.z / 6000);
  vec4 sPos = vec4(rad * cos(theta) * cos(phi),
		   rad * sin(theta),
		   -rad * cos(theta) * sin(phi),
		   1);
  
  gl_Position = m_mvp * mix(sPos, vPos, u_unwrap);
  vs_out.depth = 1.0 - (aPos.z / 6000);
}
