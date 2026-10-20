"""
Hirourk
not.nice.primer@gmail.com

Created by Hirourk

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

bl_info = {
    "name": "HAS Paint Layers V1",
    "blender": (5, 2, 0),
    "category": "Paint",
    "version": (0, 9, 1),
    "description": "Layers for texture painting",
    "author": "Hirourk",
    "location": "View3D > Tool Shelf > Paint Layers",
    "warning": "Add-on is still in development",
    "doc_url": "https://hirourk.github.io/HASPaintLayersWiki/index.html",
}

import bpy
from bpy.app.handlers import persistent, save_pre
from . import operators, ui, properties, has_enum, utils, bake, presets, tools

modules = [operators, ui, properties, has_enum, utils, bake, presets, tools]


@bpy.app.handlers.persistent
def save_modified_images(dummy):
    # Autosave for images
    if bpy.context.scene.other_props.toggle_save:
        for image in bpy.data.images:
            if image.is_dirty:
                bpy.ops.image.save_all_modified()
                return


def register():
    for module in modules:
        if hasattr(module, "register"):
            module.register()
    if save_modified_images not in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(save_modified_images)

    bpy.types.Scene.selected_texture = bpy.props.StringProperty(name="Selected Texture")


def unregister():

    for module in reversed(modules):
        if hasattr(module, "unregister"):
            module.unregister()
    if save_modified_images in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(save_modified_images)

    try:
        del bpy.types.Scene.selected_texture
    except Exception:
        pass


if __name__ == "__main__":
    register()
