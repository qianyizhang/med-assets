"""Authored late first-trimester geometry in maternal RAS millimetres.

The implicit boundaries are the editable source for both the scene surfaces and
the scan sections. They represent one simplified singleton at about 12 weeks.
"""

import numpy as np
from scipy.interpolate import CubicSpline, PchipInterpolator
from skimage.measure import marching_cubes

from geometry import VOXEL_MM

# Lower abdomen and upper thighs. Sections from inferior to superior define
# half-width, anteroposterior half-depth and centreline through the pelvis.
TORSO_PROFILE = PchipInterpolator(
    [-88, -63, -35, -7, 29, 72, 113, 145, 190],
    [[113, 61, -12], [122, 68, -12], [143, 82, -10], [156, 91, -9],
     [155, 92, -7], [140, 91, -5], [130, 94, -8], [133, 94, -10], [150, 97, -12]],
)

CORD_POINTS = CubicSpline(
    np.linspace(0, 1, 6),
    [[0, 10, 2], [3, 17, 3], [13, 16, 7], [18, 3, 9],
     [17, -6, 9], [13, -18, 9]],
    axis=0,
)(np.linspace(0, 1, 15))


def ellipsoid(xyz, centre, radii):
    """Signed ellipsoid field scaled by its shortest axis for blending."""
    x, y, z = xyz
    rx, ry, rz = radii
    cx, cy, cz = centre
    return (np.sqrt(((x - cx) / rx)**2 + ((y - cy) / ry)**2 + ((z - cz) / rz)**2) - 1) * min(radii)


def smooth_union(a, b, span):
    blend = np.maximum(span - np.abs(a - b), 0) / span
    return np.minimum(a, b) - span * .25 * blend**2


def tapered_segment(xyz, start, stop, start_radius, stop_radius):
    vx, vy, vz = np.subtract(stop, start)
    x, y, z = (component - origin for component, origin in zip(xyz, start, strict=True))
    t = np.clip((x * vx + y * vy + z * vz) / (vx*vx + vy*vy + vz*vz), 0, 1)
    return (np.sqrt((x - vx*t)**2 + (y - vy*t)**2 + (z - vz*t)**2)
            - (start_radius + t * (stop_radius - start_radius)))


def torso(xyz):
    x, y, z = xyz
    width, depth, centre = np.moveaxis(TORSO_PROFILE(np.clip(z, -88, 190)), -1, 0)
    front = y - centre
    # The navel and shallow grooves at the groins provide surface orientation.
    front = front + 4 * np.exp(-((x / 7)**2 + ((z - 132) / 5)**2)) * (y > 0)
    groin_z = .48 * np.abs(x) - 43
    front = front + 3.5 * np.exp(-((z - groin_z) / 10)**2 - ((np.abs(x) - 78) / 54)**2) * (y > 0)
    trunk = (np.sqrt((x / width)**2 + (front / depth)**2) - 1) * depth
    trunk = np.maximum(trunk, -z - 89 + 12 * np.exp(-(x / 47)**2))
    thighs = np.minimum(
        ellipsoid(xyz, (-75, -12, -49), (70, 71, 82)),
        ellipsoid(xyz, (75, -12, -49), (70, 71, 82)),
    )
    return np.maximum(smooth_union(trunk, thighs, 13), np.maximum(z - 178, -z - 117))


def uterine_coordinates(xyz):
    x, y, z = xyz
    y = y + 5
    z = z - 13
    return x, .974*y - .227*z, .227*y + .974*z


def sac_coordinates(xyz):
    x, y, z = uterine_coordinates(xyz)
    y, z = y - 12.5, z + 3
    return x, .909 * y + .417 * z, -.417 * y + .909 * z


def cavity(xyz):
    return ellipsoid(sac_coordinates(xyz), (0, 0, 0), (24, 24, 51))


def placental_disc(xyz, margin=0):
    radii = np.array((25, 13, 34)) + margin
    return ellipsoid(sac_coordinates(xyz), (2, -24, 2), radii)


def placenta(xyz):
    # The fetal surface follows the sac. The basal plate lies against myometrium.
    return np.maximum(placental_disc(xyz), -cavity(xyz))


def uterine_envelope(xyz):
    corpus = ellipsoid(sac_coordinates(xyz), (0, 0, 0), (30, 30, 57))
    outside = smooth_union(corpus, placental_disc(xyz, 4), 4)
    cervix = tapered_segment(xyz, (0, 10, -27), (0, -15, -53), 14, 10)
    return smooth_union(outside, cervix, 9)


def uterus(xyz):
    return np.maximum.reduce([uterine_envelope(xyz), -cavity(xyz), -placenta(xyz)])


def maternal_bladder(xyz):
    return np.maximum(ellipsoid(xyz, (0, 41, -31), (37, 18, 21)), 1.2 - uterine_envelope(xyz))


def cranium(xyz):
    # The calvarium has a fuller posterior vault and a narrower forehead.
    return smooth_union(
        ellipsoid(xyz, (0, -.1, 34.3), (11.6, 13.4, 14.1)),
        ellipsoid(xyz, (0, 5.3, 36.4), (10.8, 10, 11.3)), 2.4,
    )


def head(xyz):
    x, y, z = xyz
    vault = cranium(xyz) - .8
    jaw = ellipsoid(xyz, (0, 7.9, 25.6), (8, 9.0, 5.1))
    cheeks = ellipsoid(xyz, (0, 10.8, 28.5), (8.4, 5.4, 5.2))
    brow = ellipsoid(xyz, (0, 12.5, 33.5), (8.55, 4.0, 4.2))
    nose = tapered_segment(xyz, (0, 14.1, 32.2), (0, 18.25, 28.7), 1.9, 1.65)
    lips = ellipsoid(xyz, (0, 15.7, 25.8), (4.1, 2.5, 1.7))
    face = smooth_union(smooth_union(jaw, cheeks, 2), smooth_union(nose, lips, 1.6), 2)
    face = smooth_union(face, brow, 1.9)
    shape = smooth_union(vault, face, 2.3)
    orbit = ellipsoid((np.abs(x), y, z), (5.8, 16.2, 31.2), (3.8, 2.7, 2.25))
    mouth = ellipsoid(xyz, (0, 18.25, 25), (3.8, 1.55, .55))
    shape = np.maximum(shape, -np.minimum(orbit, mouth))
    ear = ellipsoid((np.abs(x), y, z), (10.5, -.3, 28.4), (2.25, 2.6, 3.25))
    return smooth_union(shape, ear, 1.5)


def body(xyz):
    back = tapered_segment(xyz, (0, -5.9, 16.5), (0, -1.1, -8), 7.15, 8.7)
    thorax = ellipsoid(xyz, (0, -1.3, 11.7), (10.1, 7.6, 10.3))
    abdomen = ellipsoid(xyz, (0, 2.6, -3.7), (10.1, 9.2, 10.9))
    neck = tapered_segment(xyz, (0, -5, 17), (0, -4.7, 24), 5.2, 5.2)
    return smooth_union(smooth_union(back, thorax, 2.4),
                        smooth_union(abdomen, neck, 2), 2.6)


# Slightly unequal resting limb poses keep the two sides identifiable.
ARMS = (
    ((8, 0, 14), (14, 2, 5), (15, 12, 11), (13, 15, 15)),
    ((-8, 0, 14), (-14, 5, 7), (-13, 14, 12), (-10, 17, 16)),
)
LEGS = (
    ((6, 1, -7), (10, 10, -13), (12, 14, -18), (10, 18, -15)),
    ((-6, 0, -7), (-10, 9, -12), (-14, 13, -17), (-13, 18, -15)),
)
LIMB_COORDS = ARMS + LEGS
LIMB_RADII = ((3.4, 3, 2.1, 2.5),) * 2 + ((4.6, 4.0, 2.4, 2.5),) * 2


def fetus(xyz):
    shape = smooth_union(head(xyz), body(xyz), 2.6)
    for coords, radii in zip(LIMB_COORDS, LIMB_RADII, strict=True):
        for start, stop, r1, r2 in zip(coords[:-1], coords[1:], radii[:-1], radii[1:], strict=True):
            shape = smooth_union(shape, tapered_segment(xyz, start, stop, r1, r2), 1.5)
    return shape


def fetal_bladder(xyz):
    return ellipsoid(xyz, (0, 4, -5.1), (2, 2.6, 3.0))


def nasal_bone(xyz):
    return tapered_segment(xyz, (0, 16.55, 31.6), (0, 18.45, 29.2), .48, .34)


def nuchal_space(xyz):
    """Thin subcutaneous fluid layer along the posterior neck in the sagittal profile."""
    x, y, z = xyz
    skin = smooth_union(head(xyz), body(xyz), 2.6)
    patch = ellipsoid(xyz, (0, -13, 21.5), (5.2, 6.4, 8.0))
    return np.maximum(patch, np.abs(skin + 1.35) - .78)


def spinal_echoes(xyz):
    # Separate ossification echoes along the posterior aspect of the trunk.
    x, y, z = xyz
    offset = np.mod(z + 10, 3.5) - 1.75
    curve = -9.75 - 2.35 * np.exp(-((z - 10) / 12)**2)
    centres = np.abs(x) - 1.1
    vertebrae = np.sqrt((centres / 1.4)**2 + ((y - curve) / 1.5)**2 + (offset / 1.0)**2) - 1
    return np.maximum(np.maximum(vertebrae, np.maximum(z - 22, -z - 9)), body(xyz) + .65)


def calvarium(xyz):
    _, y, z = xyz
    vault = cranium(xyz)
    return np.maximum(np.maximum(vault + .09, -vault - 1.35), 27.5 - z + .13*y)


def falx(xyz):
    return ellipsoid(xyz, (0, -.5, 36), (.42, 11.1, 8.5))


def choroid_plexus(xyz):
    x, y, z = xyz
    mirrored = np.abs(x), y, z
    horn = tapered_segment(mirrored, (2.15, 5.3, 35.4), (5.25, .8, 35.4), 1.12, 1.9)
    wing = tapered_segment(mirrored, (5.25, .8, 35.4), (4.9, -6.25, 35), 1.9, 3.45)
    return smooth_union(horn, wing, 1.05)


def cord(xyz):
    field = np.inf
    for a, b in zip(CORD_POINTS[:-1], CORD_POINTS[1:], strict=True):
        field = np.minimum(field, tapered_segment(xyz, a, b, 1.75, 1.75))
    return field


def amniotic_fluid(xyz):
    # The cavity is exported as a translucent boundary. Echoes inside it
    # exclude the independently authored fetal, cord and placental regions.
    return cavity(xyz)


# Spacing is finer for the smaller fetal structures. Values are physical mm;
# convert to the legacy 1.5-mm scene unit only when writing a scene mesh.
FIELDS = {
    'torso': (torso, (-172, -108, -121), (172, 105, 181), 2.0),
    'uterus': (uterus, (-42, -57, -72), (42, 60, 77), 1.0),
    'amniotic_fluid': (amniotic_fluid, (-27, -47, -55), (27, 50, 69), 1.2),
    'placenta': (placenta, (-32, -55, -36), (35, 22, 57), .65),
    'maternal_bladder': (maternal_bladder, (-39, 20, -56), (39, 62, -5), .9),
    'fetus': (fetus, (-22, -18, -27), (22, 27, 52), .42),
    'nasal_bone': (nasal_bone, (-1, 15, 28), (1, 20, 33), .12),
    'nuchal_space': (nuchal_space, (-6, -21, 13), (6, -6, 30), .18),
    'fetal_bladder': (fetal_bladder, (-4, -.2, -9), (4, 9, -1), .4),
    'umbilical_cord': (cord, (-5, -33, -2), (28, 22, 13), .53),
    'calvarium': (calvarium, (-14, -16, 24), (14, 18, 51), .35),
    'falx': (falx, (-2, -13, 26), (2, 12, 46), .28),
    'choroid_plexus': (choroid_plexus, (-10, -11, 30), (10, 8, 40), .35),
    # The midsagittal cut grazes the paired vertebral echoes. Keep a fine grid
    # whose lateral samples include the fetal midline at x = 0.
    'spinal_echoes': (spinal_echoes, (-6, -16, -11), (6, -8, 24), .15),
}


def mesh_for(name):
    field, lo, hi, step = FIELDS[name]
    axes = [np.arange(a, b + step, step, dtype=np.float32) for a, b in zip(lo, hi, strict=True)]
    values = field(np.meshgrid(*axes, indexing='ij', sparse=True))
    if any(np.min(np.take(values, [0, -1], axis=axis)) <= 0 for axis in range(3)):
        raise ValueError(f'{name} surface crosses its configured bounds')
    vertices, faces, _, _ = marching_cubes(values, 0, spacing=(step,) * 3, gradient_direction='descent')
    return (vertices + lo) / VOXEL_MM, faces
