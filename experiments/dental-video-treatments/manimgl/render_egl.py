"""Select supported ModernGL EGL backend for headless original ManimGL.
No alternate renderer is used; no upstream package files are modified.
"""
import os
os.environ.setdefault('PYGLET_HEADLESS','true')
import moderngl
_original=moderngl.create_standalone_context
def egl_context(**kwargs):
    kwargs.setdefault('backend','egl')
    ctx=_original(**kwargs)
    print('OPENGL_RENDERER:',ctx.info.get('GL_RENDERER'))
    return ctx
moderngl.create_standalone_context=egl_context
from manimlib.__main__ import main
main()
