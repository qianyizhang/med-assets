// Coordinates are millimetres in the BodyParts3D glTF frame (+left, +cranial,
// +anterior). The columns express the three axes of the authored cardiac frame.
// Reversing handedness maps posterior-positive heart coordinates into this frame.
export const heartOrigin = [92.0, 1155.0, 210.14679696];
export const heartAxes = [
  [0.86151898, 0.47671067, -0.17473404],
  [-0.44142615, 0.53323036, -0.72167052],
  [0.25085454, -0.69886503, -0.66982062],
];

export function bodyDirection([x, y, z]) {
  return heartOrigin.map((_, i) => x * heartAxes[0][i] + y * heartAxes[1][i] + z * heartAxes[2][i]);
}

export function bodyPoint(local) {
  return bodyDirection(local).map((v, i) => v + heartOrigin[i]);
}
