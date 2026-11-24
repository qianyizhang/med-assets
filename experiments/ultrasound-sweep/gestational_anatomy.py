"""Original 20- and 32-week teaching models in maternal RAS millimetres.

Organ fields use fetal right, anterior and superior directions. Shared shapes
are rescaled by region, while the stage-specific limbs and maternal positions
are authored directly. The same zero surfaces define the meshes and rasters.
"""

from dataclasses import dataclass

import numpy as np
from scipy.interpolate import CubicSpline, PchipInterpolator
from scipy.optimize import brentq
from scipy.spatial.transform import Rotation
from skimage.measure import marching_cubes

from geometry import VOXEL_MM
from pregnancy_anatomy import ellipsoid, smooth_union, tapered_segment


def tube(xyz, points, radii):
    field = np.inf
    for start, stop, r1, r2 in zip(points[:-1], points[1:], radii[:-1], radii[1:], strict=True):
        field = np.minimum(field, tapered_segment(xyz, start, stop, r1, r2))
    return field


def reflected(xyz):
    x, y, z = xyz
    return np.abs(x), y, z


def upper_lip(xyz):
    x, y, z = xyz
    # Continuous lip with a shallow midline bow and taper at the corners.
    forward = .024*x**2
    bow = .42*np.exp(-((np.abs(x)-2.5)/1.15)**2)
    return ellipsoid((x, y+forward, z-bow), (0, 28.8, 92.2), (8.5, 2.6, 1.55))


def nares(xyz):
    return ellipsoid(reflected(xyz), (3.25, 32.8, 96.7), (1.6, 2.0, 1.30))


def scalp(xyz):
    vault = ellipsoid(xyz, (0, -1, 108), (23.6, 29.5, 30.5))
    jaw = ellipsoid(xyz, (0, 10, 87), (16, 16.3, 13))
    brow = ellipsoid(xyz, (0, 21, 111), (18, 9, 13))
    cheek = ellipsoid(xyz, (0, 21.5, 96), (17, 7.6, 8.8))
    nose = tapered_segment(xyz, (0, 26, 106), (0, 33, 99), 3.5, 3.2)
    alae = ellipsoid(reflected(xyz), (3.55, 30.9, 97.6), (2.9, 3.9, 2.55))
    nose = smooth_union(nose, alae, 1.3)
    face = smooth_union(smooth_union(jaw, cheek, 4), smooth_union(brow, nose, 2.8), 3.2)
    face = smooth_union(smooth_union(vault, face, 4.0), upper_lip(xyz), 2.8)
    orbit = ellipsoid(reflected(xyz), (9, 29, 104.5), (5.8, 4.3, 4.6))
    mouth = ellipsoid(xyz, (0, 30, 90.5), (6.3, 2.2, .85))
    ear = ellipsoid(reflected(xyz), (21.7, -4.7, 95), (3.5, 6.2, 6.5))
    cutouts = np.minimum(np.minimum(orbit, mouth), nares(xyz))
    return smooth_union(np.maximum(face, -cutouts), ear, 2)


def trunk(xyz):
    neck = tapered_segment(xyz, (0, -5, 59), (0, -8, 87), 10, 12)
    chest = ellipsoid(xyz, (0, .0, 44), (23.8, 20.2, 30.0))
    belly = ellipsoid(xyz, (0, 2.4, 16), (22.8, 22.7, 28.7))
    rump = ellipsoid(xyz, (0, -2.0, -13), (20.2, 18.2, 18.0))
    torso = smooth_union(smooth_union(chest, belly, 5), rump, 6)
    return smooth_union(torso, neck, 4.8)


def calvarium(xyz):
    x, y, z = xyz
    vault = ellipsoid(xyz, (0, -1.6, 108), (22.7, 28.5, 29.6))
    band = np.maximum(np.maximum(vault, -vault - 1.7), 84 + .28*y - z)
    return np.maximum(band, -orbits(xyz)+.7)


def falx(xyz):
    return ellipsoid(xyz, (0, -3, 112), (.72, 23.5, 23))


def ventricles(xyz):
    return tube(reflected(xyz), [(3.5, 13, 111), (6, 6, 113), (10, -5, 113),
                                  (13.5, -15, 111), (11.2, -20, 107)],
                [2.2, 2.9, 3.7, 5.2, 2.4])


def choroid(xyz):
    return tube(reflected(xyz), [(7, -4, 112.7), (11.5, -13, 111), (12, -16.2, 110)],
                [1.4, 3.15, 2.6])


def csp(xyz):
    x, y, z = xyz
    xy = (np.abs(x)/2.4)**3 + (np.abs(y-6.0)/4.2)**3
    return (np.cbrt(xy + (np.abs(z-107.0)/3.1)**3) - 1) * 2.4


def thalami(xyz):
    return ellipsoid(reflected(xyz), (5.2, -.8, 104), (5, 6.0, 5.3))


def cerebellum(xyz):
    lobe = ellipsoid(reflected(xyz), (5.3, -17, 98.4), (6.8, 5.5, 4.8))
    vermis = ellipsoid(xyz, (0, -17.7, 99), (4, 4, 3))
    return smooth_union(lobe, vermis, 1.7)


def cisterna_magna(xyz):
    space = ellipsoid(xyz, (0, -23.7, 97), (10.4, 4, 4.8))
    return np.maximum(space, -cerebellum(xyz))


def orbits(xyz):
    return ellipsoid(reflected(xyz), (9, 21.8, 102), (6.2, 6, 6.2))


def nasal_bone(xyz):
    return tapered_segment(xyz, (0, 27.5, 106.9), (0, 30.8, 101.9), 1.1, .95)


def spine(xyz):
    x, y, z = xyz
    # The axis curves anteriorly at the head and sacrum. A short gap between
    # neighbouring ossification centres preserves the segmented landmark.
    curve = -15 - 4 * np.exp(-((z-27)/34)**2) + 4.4*np.exp(-((z+19)/14)**2)
    nearest = np.mod(z + 24., 5.5) - 2.75
    centrum = np.sqrt((x/3.1)**2 + ((y-curve)/2.65)**2 + (nearest/1.95)**2) - 1
    arch = np.sqrt(((np.abs(x)-3.9)/1.8)**2 + ((y-curve+3.1)/1.7)**2 + (nearest/1.48)**2) - 1
    return np.maximum(np.maximum(np.minimum(centrum, arch), np.maximum(z-78, -z-22)), trunk(xyz) + .8)


def diaphragm(xyz):
    x, y, z = xyz
    dome = 30.6+8.7*np.exp(-((np.abs(x)-12.5)/8)**2-((y+3)/16)**2)
    layer = np.abs(z-dome)-.72
    return np.maximum(layer, trunk(xyz)+.7)


def heart(xyz):
    x, y, z = xyz
    # Fetal left is negative X. The ventricular apex faces left and anterior.
    mid = (-5.0, 1.7, 43.0)
    scale = np.sqrt(((x-mid[0] + .31*(y-mid[1]))/14)**2 + ((y-mid[1])/13.2)**2 + ((z-mid[2])/14.5)**2)
    return (scale-1)*12


def lungs(xyz):
    left = ellipsoid(xyz, (-12.6, -6.5, 47), (9.3, 10.1, 14.6))
    right = ellipsoid(xyz, (12, -4, 47), (9.6, 12.4, 15.4))
    return np.maximum(np.maximum(np.minimum(left, right), -heart(xyz)-.3), trunk(xyz) + .7)


CHAMBERS = {
    'right_atrium': ((3.3, -4.2, 42), (4.95, 4.35, 6.3)),
    'left_atrium': ((-7.5, -5.2, 42.2), (4.7, 4.3, 5.5)),
}
# Centre, unit direction in the four-chamber plane, half-length, basal
# breadth, apical taper and through-plane half-depth.
VENTRICULAR_SHAPES = {
    'left_ventricle': ((-9.65, 6.1, 43.35), (-.66, .7513), 7.65, 4.0, .30, 8.7),
    'right_ventricle': ((.75, 7.0, 43.5), (-.49, .8717), 6.45, 4.45, .49, 7.8),
}

VESSELS = {
    'aortic_outflow': ([(-9.7, 5.2, 46), (-7.7, 5.4, 51), (-3.4, 5.8, 56),
                       (-1.5, 5.7, 63.6), (-2.1, 1.4, 64.3), (-6.5, -6.7, 64.35),
                       (-5.0, -10.5, 64.1), (-3.8, -12.6, 55), (-3.6, -12.8, 39)],
                      [2.1, 2.4, 2.4, 2.25, 2.05, 1.95, 1.9, 1.9, 1.9]),
    'pulmonary_outflow': ([(1.4, 6.6, 46.9), (2.2, 9.0, 52), (-1.2, 10.8, 56.6),
                           (-6.1, 10.2, 59), (-9.5, 6.8, 63.7), (-9.2, 1.2, 64.25),
                           (-6.5, -6.7, 64.35)],
                          [2.25, 2.55, 2.8, 2.8, 2.45, 2.04, 1.8]),
    'superior_vena_cava': ([(7.4, 2.9, 69), (7.7, 1.8, 59), (7.5, -1.6, 50),
                            (5.4, -3.1, 43)],
                           [1.7, 1.9, 2.0, 2.15]),
    'trachea': ([(0, -8.4, 76), (0, -8.8, 63), (-.15, -9.1, 55.8)], [2, 1.45, 1.25]),
    'umbilical_vein': ([(0, 24, 11.5), (.6, 13.1, 13.9), (2.1, 5.2, 16), (6.1, 1.2, 17.2),
                        (8.8, 1.4, 17.3), (11.9, 3.1, 16)], [2.05, 2.05, 2.2, 2.3, 2.1, 1.6]),
}


def stomach(xyz):
    return ellipsoid(xyz, (-10.2, 3, 16.8), (7.6, 6, 7.2))


def kidneys(xyz):
    return ellipsoid(reflected(xyz), (10.8, -8.5, 5.7), (5.0, 4.5, 10.2))


def renal_pelves(xyz):
    return ellipsoid(reflected(xyz), (8.9, -7.0, 5.7), (1.6, 1.4, 2.5))


def fetal_bladder(xyz):
    return ellipsoid(xyz, (0, 6.0, -13), (4.65, 5.3, 7))


def umbilical_arteries(xyz):
    return tube(reflected(xyz), [(6.8, -.3, -21), (6.0, 2.3, -15),
                (6.3, 7.5, -12), (7.6, 11.4, -7), (4.6, 18.2, 5), (1.4, 22.3, 11)],
                [1.25, 1.25, 1.38, 1.5, 1.2, 1.05])


def chamber_field(name):
    def field(xyz):
        return np.maximum(ellipsoid(xyz, *CHAMBERS[name]), heart(xyz)+.4)
    return field


def ventricular_field(name):
    centre, direction, length, breadth, taper, depth = VENTRICULAR_SHAPES[name]
    left, front = direction
    def field(xyz):
        x, y, z = (p-c for p,c in zip(xyz,centre,strict=True))
        axial = (left*x+front*y)/length
        across = front*x-left*y
        width = breadth*(1-taper*np.clip(axial, -.35, 1))
        shape = (np.sqrt(axial**2+(across/width)**2+(z/depth)**2)-1)*breadth
        return np.maximum(shape, heart(xyz)+.4)
    return field


def vessel_field(name):
    def field(xyz):
        return tube(xyz, *VESSELS[name])
    return field


# Bounds are in the shared fetal template frame. Analytic sampling uses the
# inverse of the same deformation applied to every mesh vertex.
TEMPLATE_FIELDS = {
    'calvarium': (calvarium, (-26, -34, 72), (26, 31, 142), .6),
    'falx': (falx, (-2, -29, 86), (2, 25, 138), .32),
    'ventricles': (ventricles, (-20, -26, 101), (20, 17, 120), .45),
    'choroid': (choroid, (-17, -22, 104), (17, -.5, 118), .42),
    'cavum': (csp, (-4, 0, 102), (4, 12, 112), .4),
    'thalami': (thalami, (-12, -9, 97), (12, 7, 111), .5),
    'cerebellum': (cerebellum, (-14, -24, 92), (14, -10, 105), .48),
    'cisterna_magna': (cisterna_magna, (-12, -29, 91), (12, -18, 103), .42),
    'orbits': (orbits, (-17, 14, 94), (17, 30, 110), .5),
    'nasal_bone': (nasal_bone, (-3, 25, 98), (3, 34, 110), .38),
    'upper_lip': (upper_lip, (-10, 23, 89), (10, 33, 96), .34),
    'nares': (nares, (-6, 29, 94), (6, 36, 99), .32),
    'spine': (spine, (-8, -27, -24), (8, -8, 80), .43),
    'diaphragm': (diaphragm, (-27, -25, 28), (27, 31, 42), .46),
    'heart': (heart, (-26, -15, 25), (16, 17, 61), .5),
    'lungs': (lungs, (-25, -21, 29), (25, 12, 64), .67),
    'stomach': (stomach, (-19, -4, 8), (0, 10, 26), .55),
    'kidneys': (kidneys, (-18, -15, -6), (18, -2, 18), .53),
    'renal_pelves': (renal_pelves, (-12, -10, 2), (12, -4, 10), .31),
    'fetal_bladder': (fetal_bladder, (-6, -1, -22), (6, 13, -4), .5),
    'umbilical_arteries': (umbilical_arteries, (-11, -3, -24), (11, 25, 15), .42),
}
for name, (center, radii) in CHAMBERS.items():
    TEMPLATE_FIELDS[name] = (chamber_field(name), np.subtract(center, radii)-1,
                             np.add(center, radii)+1, .38)
for name, (center, _, length, breadth, _, depth) in VENTRICULAR_SHAPES.items():
    pad = (length+breadth, length+breadth, depth+1)
    TEMPLATE_FIELDS[name] = (ventricular_field(name), np.subtract(center,pad),
                             np.add(center,pad), .38)
for name, (points, radii) in VESSELS.items():
    bound = max(radii)+1
    TEMPLATE_FIELDS[name] = (vessel_field(name), np.min(points, axis=0)-bound,
                             np.max(points, axis=0)+bound, .45)


@dataclass(frozen=True)
class Stage:
    centre: tuple
    orientation_deg: tuple
    cervix: tuple
    placenta_site_xz: tuple
    placenta_side: int
    placental_extent: tuple
    placenta_cord_join_xz: tuple
    cord_turns: tuple
    bladder: tuple
    bump: tuple
    skin_z: tuple
    limb_nodes: tuple


MID_LIMBS = (
    ((20, 0, 54), (28, 12, 30), (28, 27, 45), (26, 34, 53)),
    ((-19, -1, 54), (-28, 14, 31), (-29, 27, 46), (-29, 34, 55)),
    ((12, 2, -14), (22, 20, -38), (20, 33, -17), (20, 27, 1)),
    ((-12, 2, -14), (-23, 20, -38), (-21, 31, -17), (-21, 26, 2)),
)
LATE_LIMBS = (
    ((36, -2, 93), (44, 23, 51), (38, 30, 76), (34, 33, 90)),
    ((-34, 1, 94), (-45, 21, 57), (-36, 30, 80), (-30, 32, 90)),
    ((20, 0, -28), (31, 22, -79), (32, 31, -52), (33, 26, -24)),
    ((-22, 3, -28), (-34, 24, -78), (-34, 30, -50), (-35, 24, -22)),
)
STAGES = {
    'mid': Stage((-31, 35, 94), (0, 73, 0), ((0, 29, 67), (0, 7, 31)),
                 (-16, 40), -1, (35, 17, 44), (-10, 37),
                 ((12, 33, 18), (27, 30, 23), (36, 12, 31), (32, -10, 35), (18, -21, 38), (-10, -20, 37)),
                 ((0, 54, -2), (32, 20, 31)), (36, 108, 113), (-122, 294), MID_LIMBS),
    'late': Stage((0, 39, 135), (0, 176, -13), ((0, 31, -64), (0, 20, -98)),
                  (0, -48), 1, (42, 20.2, 49), (7, -38),
                  ((-12, 48, 15), (-25, 44, 7), (-22, 47, -8), (-5, 48, -24)),
                  ((0, 63, -82), (34, 12, 16)), (83, 155, 159), (-151, 374), LATE_LIMBS),
}

# Inner uterine dimensions follow the flexed fetus longitudinally. Each entry
# gives local superior level, half-width, half-depth and AP centre offset.
# The late contour is shaped around the presenting head and a compact flexed
# trunk and limbs, with room anteriorly for a free cord loop.
UTERINE_PROFILES = {
    'mid': PchipInterpolator(
        [-59, -44, -28, -10, 12, 34, 54, 74, 94, 117, 138, 151],
        [[0, 0, 18], [32, 25, 18], [38, 33, 15], [39, 39, 9], [45, 46, 5],
         [48, 48, 6], [54, 45, 9], [45, 37, 10], [35, 39, 3], [31, 36, 0],
         [21, 25, -1], [0, 0, -1]],
    ),
    'late': PchipInterpolator(
        [-110, -91, -74, -56, -34, -12, 13, 42, 72, 101, 126, 150, 175, 198, 214, 223],
        [[0, 0, 23], [44, 32, 23], [53, 39, 22], [58, 44, 17],
         [63, 50, 13], [59, 50, 8], [56, 49, 6], [62, 49, 8],
         [62, 49, 10], [59, 44, 8], [46, 45, 2], [53, 61, 4],
         [50, 56.5, -2], [41, 49, -4], [26, 33, -3], [0, 0, -3]],
    ),
}

MID_Z = np.array([-45, -30, 0, 18, 45, 72, 108, 144])
LATE_Z = np.array([-77, -54, 0, 33, 76, 119, 160, 210])
LATE_X = np.array([1.75, 1.77, 1.94, 1.93, 1.80, 1.65, 1.72, 1.73])
LATE_Y = np.array([1.73, 1.81, 1.96, 1.94, 1.79, 1.64, 1.73, 1.75])
TORSO_PROFILE = PchipInterpolator(
    [-151, -104, -68, -30, 23, 78, 135, 193, 255, 312, 374],
    [[119, 69, -13], [132, 75, -13], [148, 84, -12], [159, 89, -10],
     [166, 94, -9], [160, 96, -9], [150, 95, -9], [146, 95, -11],
     [149, 101, -9], [154, 100, -12], [154, 100, -12]],
)

MATERNAL_PARTS = {'torso', 'uterus', 'amniotic_cavity', 'placenta', 'maternal_bladder', 'cord', 'fluid_span', 'cervical_canal'}
LIMB_PARTS = {'fetus', 'femur', 'hands', 'feet'}
BONES = {'calvarium', 'spine', 'nasal_bone', 'femur', 'hands', 'feet'}


class Gestation:
    def __init__(self, stage):
        self.name = stage
        self.stage = STAGES[stage]
        self.rotation = Rotation.from_euler('xyz', self.stage.orientation_deg, degrees=True).as_matrix()
        self.model_z = MID_Z if stage == 'mid' else LATE_Z
        self.model_sx = np.ones(len(MID_Z)) if stage == 'mid' else LATE_X
        self.model_sy = np.ones(len(MID_Z)) if stage == 'mid' else LATE_Y
        self.scale = 1 if stage == 'mid' else 1.65
        self.cord_radius = 3.65 if stage == 'mid' else 5.0
        start = self.point((0, 23.8, 11.6), 'template')
        x, z = self.stage.placenta_cord_join_xz
        outer_y, side, thickness, _ = self.placental_patch(x, z)
        join = (x, outer_y-side*thickness*.78, z)
        cord_controls = np.array(
            [start, *(self.point(p, 'local') for p in (*self.stage.cord_turns, join))]
        )
        self.cord_path = CubicSpline(np.arange(len(cord_controls)), cord_controls, axis=0)(
            np.linspace(0, len(cord_controls)-1, 18))
        self.cord_radii = np.full(len(self.cord_path), self.cord_radius)
        start, stop = np.array(self.stage.cervix, dtype=float)
        position = brentq(lambda t: self.cavity(start+(stop-start)*t), 0, 1)
        self.cervical_opening = start+(stop-start)*position
        self.fluid_span_endpoints = self.find_fluid_span() if self.name == 'late' else None
        self.extra_fields = {
            'torso': self.torso, 'uterus': self.uterus, 'amniotic_cavity': self.cavity,
            'placenta': self.placenta, 'maternal_bladder': self.bladder,
            'cervical_canal': self.cervical_canal,
            'cord': self.cord, 'fluid_span': self.fluid_span,
            'fetus': self.fetus, 'femur': self.femur, 'hands': self.hands, 'feet': self.feet,
        }

    def forward_template(self, xyz):
        x, y, z = xyz
        return (x*np.interp(z, MID_Z, self.model_sx), y*np.interp(z, MID_Z, self.model_sy),
                np.interp(z, MID_Z, self.model_z))

    def inverse_template(self, xyz):
        x, y, z = xyz
        return (x/np.interp(z, self.model_z, self.model_sx), y/np.interp(z, self.model_z, self.model_sy),
                np.interp(z, self.model_z, MID_Z))

    def point(self, coord, space):
        if space == 'maternal':
            return np.asarray(coord, dtype=float)
        if space == 'template':
            coord = self.forward_template(coord)
        return np.dot(self.rotation, coord) + self.stage.centre

    def direction(self, direction, space, point):
        if space == 'maternal':
            return np.asarray(direction, dtype=float)
        # Use the local Jacobian of the authored deformation for a template
        # orientation, preserving the acquisition plane through its landmark.
        return self.point(np.asarray(point)+np.asarray(direction)*.01, space) - self.point(point, space)

    def local_coordinates(self, world):
        delta = tuple(axis-centre for axis, centre in zip(world, self.stage.centre, strict=True))
        return tuple(sum(component * basis for component, basis in zip(delta, axis, strict=True))
                     for axis in self.rotation.T)

    def torso(self, xyz):
        x, y, z = xyz
        width, depth, centre = np.moveaxis(TORSO_PROFILE(np.clip(z, -151, 374)), -1, 0)
        bulge, ridge, spread = self.stage.bump
        swell = np.exp(-((z-ridge)/spread)**2)
        width = width + (.29*bulge)*swell
        low_bump = 15*np.exp(-((z+54)/63)**2) if self.name == 'late' else 0
        bump = (bulge*swell+low_bump)*np.maximum(1-(x/(.97*width))**2, 0)
        anterior = (y-centre) / np.where(y >= centre, depth+bump, depth)
        anterior += .035*np.exp(-((x/7.5)**2+((z-(ridge+31))/6)**2))*(y>0)
        base = (np.sqrt((x/(width + .12*bump))**2 + anterior**2)-1)*depth
        base = np.maximum(base, -z - 132 + 9*np.exp(-(x/44)**2))
        thighs = np.minimum(ellipsoid(xyz, (75, -10, -99), (75, 75, 77)),
                            ellipsoid(xyz, (-75, -10, -99), (75, 75, 77)))
        lo, hi = self.stage.skin_z
        return np.maximum(smooth_union(base, thighs, 9), np.maximum(z-hi, lo-z))

    def uterine_contour(self, xyz, margin=0):
        x, y, z = self.local_coordinates(xyz)
        profile = UTERINE_PROFILES[self.name]
        lo, hi = profile.x[0], profile.x[-1]
        width, depth, centre = np.moveaxis(profile(np.clip(z, lo, hi)), -1, 0)
        width = np.maximum(width+margin, .2)
        depth = np.maximum(depth+margin, .2)
        egg = (np.sqrt((x/width)**2+((y-centre)/depth)**2)-1)*np.minimum(width,depth)
        # Round the poles without flattening the section where it joins the wall.
        pole = np.maximum(lo-z, z-hi)
        return np.maximum(egg, pole-margin)

    def cavity(self, xyz):
        return self.uterine_contour(xyz)

    def placental_patch(self, x, z):
        cx, cz = self.stage.placenta_site_xz
        side = self.stage.placenta_side
        rx, depth, rz = self.stage.placental_extent
        profile = UTERINE_PROFILES[self.name]
        width, half_depth, centre = np.moveaxis(profile(np.clip(z, *profile.x[[0,-1]])), -1, 0)
        wall = half_depth*np.sqrt(np.maximum(1-(x/np.maximum(width,.2))**2,0))
        radius = ((x-cx)/rx)**2+((z-cz)/rz)**2
        thickness = depth*np.sqrt(np.maximum(1-radius,0))
        return centre+side*wall, side, thickness, (np.sqrt(radius)-1)*min(rx,rz)

    def placenta(self, xyz):
        x, y, z = self.local_coordinates(xyz)
        outer_y, side, thickness, outline = self.placental_patch(x,z)
        depth = side*(outer_y-y)
        lens = np.maximum(np.maximum(depth-thickness, -depth-2.6), outline)
        return np.maximum(lens, self.uterine_contour(xyz, 3.5))

    def uterus(self, xyz):
        start, end = self.stage.cervix
        cervix = tapered_segment(xyz, start, end, 14, 11)
        wall = smooth_union(self.uterine_contour(xyz, 6.0), cervix, 7.0)
        return np.maximum(np.maximum(wall, -self.cavity(xyz)), -self.placenta(xyz))

    def cervical_canal(self, xyz):
        _, stop = self.stage.cervix
        canal = tapered_segment(xyz, self.cervical_opening, stop, 1.6, 1.8)
        return np.maximum(canal, -self.cavity(xyz))

    def bladder(self, xyz):
        return ellipsoid(xyz, *self.stage.bladder)

    def cord(self, xyz):
        return tube(xyz, self.cord_path, self.cord_radii)

    def fluid_constraint(self, xyz):
        inside = self.cavity(xyz)
        empty = np.maximum(-self.fetus(self.local_coordinates(xyz)), -self.placenta(xyz))
        return np.maximum(np.maximum(inside, empty), -self.cord(xyz))

    def find_fluid_span(self):
        # A transabdominal depth line in a supine maternal frame. The
        # endpoints are intersections with the actual fluid boundaries.
        x, z, seed = 44, 95, 67
        y = np.arange(0,145,dtype=float)
        inside = self.fluid_constraint((x,y,z)) < 0
        i = int(seed-y[0])
        if not inside[i] or inside[0] or inside[-1]:
            raise ValueError('The fluid window must begin inside a bounded clear pocket')
        lo = np.flatnonzero(~inside[:i])[-1]
        hi = i+np.flatnonzero(~inside[i:])[0]
        lower = brentq(lambda d:self.fluid_constraint((x,d,z)), y[lo], y[lo+1])
        upper = brentq(lambda d:self.fluid_constraint((x,d,z)), y[hi-1], y[hi])
        return np.array([(x,lower,z), (x,upper,z)])

    def fluid_span(self, xyz):
        lower, upper = self.fluid_span_endpoints
        radius = .7
        inset = np.array([0,radius,0])
        return tapered_segment(xyz, lower+inset, upper-inset, radius, radius)

    def digit_guides(self, limb_index):
        nodes = self.stage.limb_nodes[limb_index]
        start = np.array(nodes[2], dtype=float)
        end = np.array(nodes[3], dtype=float)
        direction = (end-start)/np.linalg.norm(end-start)
        lateral = np.cross(direction, (0, 1, 0))
        lateral /= np.linalg.norm(lateral)
        hand = limb_index < 2
        layout = ([-5.5, -3.2, -.7, 2.1, 4.6], [5.6, 7.5, 8.9, 7.9, 6.0]) if hand else (
                  [-5.7, -3.1, -.8, 1.4, 3.7], [6.6, 5.6, 5.2, 4.4, 3.8])
        offsets, lengths = np.array(layout)*self.scale
        sign = 1 if limb_index in (0, 3) else -1
        for i, (offset, length) in enumerate(zip(offsets, lengths, strict=True)):
            root = end + lateral*offset*sign
            tip = root + direction*length + lateral*offset*.31*sign
            yield root, tip, (1.7 if i in (0, 2) else 1.33)*self.scale

    def limb_skin(self, local):
        field = np.inf
        for i, nodes in enumerate(self.stage.limb_nodes):
            radii = np.array((8.1, 7, 4.7, 4.8) if i < 2 else (11.5, 8.7, 4.9, 6.6))*self.scale
            field = smooth_union(field, tube(local, nodes, radii), 2*self.scale)
            if i >= 2:
                ankle, forefoot = np.array(nodes[2:])
                axis = (forefoot-ankle)/np.linalg.norm(forefoot-ankle)
                heel = ankle-axis*2.8*self.scale
                sole = tapered_segment(local, heel, forefoot, 5.1*self.scale, 6.4*self.scale)
                field = smooth_union(field, sole, 2.0*self.scale)
            for root, tip, radius in self.digit_guides(i):
                field = smooth_union(field, tapered_segment(local, root, tip, radius, radius*.68), self.scale)
        return field

    def fetus(self, local):
        template = self.inverse_template(local)
        core = smooth_union(scalp(template), trunk(template), 3.7)*self.scale
        return smooth_union(core, self.limb_skin(local), 4.2*self.scale)

    def femur(self, local):
        field = np.inf
        for hip, knee, *_ in self.stage.limb_nodes[2:]:
            radius = 2.55*self.scale
            field = np.minimum(field, tapered_segment(local, hip, knee, radius, radius*.81))
        return field

    def digital_bones(self, local, indexes):
        field = np.inf
        for i in indexes:
            wrist, palm = (np.asarray(p, dtype=float) for p in self.stage.limb_nodes[i][2:])
            along = palm-wrist
            for j, (root, tip, radius) in enumerate(self.digit_guides(i)):
                if i < 2:
                    origin, end = root-along*.57, root
                    join = root+(tip-root)*.26
                    field = np.minimum(field, tapered_segment(local, origin, end, radius*.54, radius*.48))
                    field = np.minimum(field, tapered_segment(local, join, tip-(tip-root)*.16, radius*.48, radius*.41))
                else:
                    # A short fan of metatarsals, calcaneal echo and toe
                    # phalanges aligned with the curved plantar outline.
                    spread = root-palm
                    origin = wrist+along*(.27+.07*j)+spread*.24
                    end = root-along*.10
                    field = np.minimum(field, tapered_segment(local, origin, end, radius*.61, radius*.48))
                    first, last = root+(tip-root)*.14, tip-(tip-root)*.13
                    field = np.minimum(field, tapered_segment(local, first, last, radius*.55, radius*.40))
            if i >= 2:
                heel = wrist-along*.035
                field = np.minimum(field, ellipsoid(local, heel, np.array([2.9,3.7,3.4])*self.scale))
        return field

    def hands(self, local):
        return self.digital_bones(local, (0, 1))

    def feet(self, local):
        return self.digital_bones(local, (2, 3))

    def sample(self, world, names):
        local = self.local_coordinates(world)
        template = self.inverse_template(local)
        return {name: (TEMPLATE_FIELDS[name][0](template)*self.scale if name in TEMPLATE_FIELDS
                       else self.extra_fields[name](world if name in MATERNAL_PARTS else local))
                for name in names}

    def native_bounds(self, name):
        if name in TEMPLATE_FIELDS:
            field, lo, hi, step = TEMPLATE_FIELDS[name]
            return field, lo, hi, step
        s = self.stage
        if name == 'torso':
            lo, hi, step = (-214, -119, s.skin_z[0]-4), (214, 210, s.skin_z[1]+4), 3.0
        elif name in {'uterus', 'amniotic_cavity', 'placenta'}:
            # Rotate a bounding box for the true local profile into maternal
            # coordinates. Include the separately placed maternal cervix.
            dimensions = [(-82, 82), (-68, 82), (-66, 161)] if self.name == 'mid' else [
                (-94, 94), (-81, 96), (-115, 233)]
            x, y, z = dimensions
            corners = np.array([self.point((a,b,c), 'local') for a in x for b in y for c in z])
            corners = np.vstack([corners, self.stage.cervix])
            lo, hi, step = corners.min(axis=0)-17, corners.max(axis=0)+17, 1.9
        elif name == 'cervical_canal':
            endpoints = np.array([self.cervical_opening, self.stage.cervix[1]])
            lo, hi, step = endpoints.min(axis=0)-3, endpoints.max(axis=0)+3, .51
        elif name == 'maternal_bladder':
            centre, radii = s.bladder
            lo, hi, step = np.subtract(centre, radii)-5, np.add(centre, radii)+5, 1.45
        elif name == 'fluid_span':
            lo, hi, step = self.fluid_span_endpoints[0]-2, self.fluid_span_endpoints[1]+2, .33
        elif name == 'cord':
            lo, hi, step = self.cord_path.min(axis=0)-8, self.cord_path.max(axis=0)+8, .9
        else:
            if name == 'fetus':
                lo, hi, step = (-51, -37, -47), (51, 76, 145), 1.2
                if self.name == 'late':
                    lo, hi, step = (-83, -61, -98), (83, 110, 216), 1.7
            else:
                indexes = range(2) if name == 'hands' else range(2, 4)
                # Fine phalangeal shafts need a smaller sampling step than the femur.
                ends = slice(0, 2) if name == 'femur' else slice(2, None)
                nodes = np.array([p for i in indexes for p in s.limb_nodes[i][ends]])
                pad = (6 if name == 'femur' else 18) * self.scale
                step = (.55 if name == 'femur' else .30) * self.scale
                lo, hi = nodes.min(axis=0) - pad, nodes.max(axis=0) + pad
        return self.extra_fields[name], lo, hi, step

    def mesh(self, name):
        field, lo, hi, step = self.native_bounds(name)
        axes = [np.arange(a, b+step, step, dtype=np.float32) for a, b in zip(lo, hi, strict=True)]
        values = field(np.meshgrid(*axes, indexing='ij', sparse=True))
        if any(np.min(np.take(values, [0, -1], axis=axis)) <= 0 for axis in range(3)):
            raise ValueError(f'{self.name} {name} crosses its configured mesh bounds')
        vertices, faces, _, _ = marching_cubes(values, 0, spacing=(step,)*3, gradient_direction='descent')
        vertices += lo
        if name in TEMPLATE_FIELDS:
            vertices = np.column_stack(self.forward_template(vertices.T))
        if name not in MATERNAL_PARTS:
            vertices = np.einsum('ij,vj->vi', self.rotation, vertices) + self.stage.centre
        return vertices / VOXEL_MM, faces
