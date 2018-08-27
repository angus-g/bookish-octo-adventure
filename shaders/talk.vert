#version 450 core

in vec2 aPos;

uniform mat4 m_mvp;
uniform float u_unwrap;

void main() {
  vec4 vPos = vec4((aPos + vec2(100, 0)) / vec2(180, 80), 0.0, 1.0);

  // elevation and azimuth in spherical coords
  float phi = radians(aPos.x);
  float theta = radians(aPos.y);
  vec4 sPos = vec4(cos(theta) * cos(phi),
		   cos(theta) * sin(phi),
		   sin(theta),
		   1);
  
  gl_Position = m_mvp * mix(sPos, vPos, u_unwrap);
}
