// Consume pending input on the old pose before the caller imposes an exact view.
export function clearPendingOrbit(controls) {
  const damping = controls.enableDamping;
  controls.enableDamping = false;
  try {
    controls.update();
  } finally {
    controls.enableDamping = damping;
  }
}
