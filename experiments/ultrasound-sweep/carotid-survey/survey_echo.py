"""Illustrative B-mode echoes from registered neck tissue sections."""

import numpy as np
from scipy import ndimage as nd

from build_study import fine_scatter
from reconstruction import raster_grid, plane_to_world


def acoustic_sample(view, masks, contexts):
    """Render coherent echoes. Masks and the world-space pose retain measurement authority."""
    _, depth = raster_grid(view)
    shape = (view['heightPx'], view['widthPx'])
    row, col = np.indices(shape)
    xyz = np.moveaxis(plane_to_world(view, np.stack((col, row), axis=-1)), -1, 0)
    pitch = view['mmPerPx']
    skin = contexts['skin']
    below = np.maximum(0, (row - np.argmax(skin, axis=0)) * pitch)
    # Keep speckle tied to tissue coordinates through changing poses. Scatter
    # amplitude depends on tissue, with a slower-varying lobular component.
    speckle = fine_scatter(xyz / 1.5)
    lobules = fine_scatter(xyz * .075)
    base = 54 + 35 * lobules
    strength = np.full(shape, 47.)
    interfaces = np.zeros(shape)
    bone = np.zeros(shape, dtype=bool)
    vessels = np.logical_or.reduce(list(masks.values()))
    fluid = vessels.copy()
    for name, mask in contexts.items():
        if name == 'skin':
            continue
        if name == 'jugular':
            fluid |= mask
            continue
        if name in ('clavicle', 'mandible', 'temporal-bone', 'first-rib', 'c3', 'c4', 'c5', 'c6', 'c7'):
            bone |= mask
            continue
        part = nd.gaussian_filter(mask.astype('f4'), .23 / pitch)
        # Atlas muscle bellies stay relatively dark, with sparse oblique echogenic
        # strands. Their outer interfaces persist in either scan orientation.
        if name in ('scm', 'scalene', 'omohyoid', 'sternohyoid'):
            across = (.90 * xyz[1] + .15 * np.abs(xyz[0]) + .12 * xyz[2])
            fiber = np.exp(-(np.sin(across * .84 + .75*np.sin(xyz[2]*.078) + .6*lobules) / .22)**2)
            base = (1-part)*base + part*(25 + 13*lobules + 39*fiber)
            strength = strength*(1-.38*part)
        elif name == 'thyroid':
            base = base*(1-part) + part*(78+15*lobules)
        interfaces += 130 * pitch * abs(np.gradient(part, pitch, axis=0))
    # The atlas has a skin surface but no separate subcutaneous fat mask. Give
    # the near field an illustrative dermal echo and curved septa in shallow fat.
    shallow = np.exp(-(below/6)**2)
    septa = np.exp(-(np.sin(.98*below + .28*np.sin(xyz[2]*.19) + .20*np.sin(xyz[0]*.25) + .6*lobules) / .27)**2)
    base += shallow * (40*septa - 9)
    interfaces += 102*np.exp(-((below-.35)/.30)**2) + 44*np.exp(-((below-1.2)/.30)**2)
    # A directional return from an interface is strongest on the near and far
    # walls. This single band makes no claim about intima-media thickness.
    vessel_field = nd.gaussian_filter(vessels.astype('f4'), .29/pitch)
    vein_field = nd.gaussian_filter((fluid & ~vessels).astype('f4'), .29/pitch)
    outer = np.maximum(vessel_field, vein_field)
    interfaces *= (1 - outer)
    interfaces += (85*np.abs(np.gradient(vessel_field, pitch, axis=0)) +
                   48*np.abs(np.gradient(vein_field, pitch, axis=0)))
    image = (base + strength*speckle)*(1-.94*outer) + 3*outer + interfaces*(.86+.24*speckle)
    bone_face = np.maximum(0, np.gradient(nd.gaussian_filter(bone.astype('f4'), .22/pitch), pitch, axis=0))
    image += 140*bone_face
    image *= np.exp(-np.maximum(depth[:, None], 0)/150)
    field = skin & (depth[:, None] >= 0)
    return np.where(field, np.clip(image, 0, 250), 0).astype('u1'), vessels & field
