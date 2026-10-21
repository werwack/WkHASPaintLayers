import bpy
from bpy.utils import register_class, unregister_class
import os
import re
from bl_operators.presets import AddPresetBase
from bpy.props import StringProperty
from bpy.types import Operator, Menu
from .has_enum import *
from .utils.utils import get_presets_folder


class LoadPresetsOperator(Operator):
    bl_idname = "paint.load_presets"
    bl_label = "Load Presets"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        preset_folder = get_presets_folder()
        if not os.path.exists(preset_folder):
            os.makedirs(preset_folder)
        initial_file = os.path.join(preset_folder, "Packed.py")
        try:
            if not os.path.isfile(initial_file):
                with open(initial_file, "w") as f:
                    f.write("import bpy\n")
                    f.write("scene = bpy.context.scene\n")
                    f.write("op = bpy.context.scene.other_props.exportprops\n")

                    f.write("scene.other_props.height_to_normal = True\n")
                    f.write("scene.other_props.invert_green_n = False\n")
                    f.write("op[0].type = 'RGB_A'\n")
                    f.write("op[0].RGB = 'DIFFUSE'\n")
                    f.write("op[0].R = 'METALLIC'\n")
                    f.write("op[0].G = 'ROUGHNESS'\n")
                    f.write("op[0].B = 'HEIGHT'\n")
                    f.write("op[0].A = 'ALPHA'\n")
                    f.write("op[0].save_name = '(mtl)_Diffuse'\n")
                    f.write("op[1].type = 'R_G_B_A'\n")
                    f.write("op[1].RGB = 'ROUGHNESS'\n")
                    f.write("op[1].R = 'ROUGHNESS'\n")
                    f.write("op[1].G = 'METALLIC'\n")
                    f.write("op[1].B = 'AO'\n")
                    f.write("op[1].A = 'EMPTY'\n")
                    f.write("op[1].save_name = '(mtl)_RMO'\n")
                    f.write("op[2].type = 'RGB'\n")
                    f.write("op[2].RGB = 'NORMAL'\n")
                    f.write("op[2].R = 'EMPTY'\n")
                    f.write("op[2].G = 'EMPTY'\n")
                    f.write("op[2].B = 'EMPTY'\n")
                    f.write("op[2].A = 'EMPTY'\n")
                    f.write("op[2].save_name = '(mtl)_Normal'\n")
        except (OSError, PermissionError) as e:
            print(f"Failed to create or write to the file: {e}")
        initial_file = os.path.join(preset_folder, "PBR.py")
        try:
            if not os.path.isfile(initial_file):
                with open(initial_file, "w") as f:
                    f.write("import bpy\n")
                    f.write("scene = bpy.context.scene\n")
                    f.write("op = bpy.context.scene.other_props.exportprops\n")

                    f.write("scene.other_props.height_to_normal = True\n")
                    f.write("scene.other_props.invert_green_n = False\n")
                    f.write("op[0].type = 'RGB'\n")
                    f.write("op[0].RGB = 'DIFFUSE'\n")
                    f.write("op[0].R = 'METALLIC'\n")
                    f.write("op[0].G = 'ROUGHNESS'\n")
                    f.write("op[0].B = 'HEIGHT'\n")
                    f.write("op[0].A = 'DIFFUSE'\n")
                    f.write("op[0].save_name = '(mtl)_Diffuse'\n")
                    f.write("op[1].type = 'R'\n")
                    f.write("op[1].RGB = 'ROUGHNESS'\n")
                    f.write("op[1].R = 'METALLIC'\n")
                    f.write("op[1].G = 'ROUGHNESS'\n")
                    f.write("op[1].B = 'EMPTY'\n")
                    f.write("op[1].A = 'EMPTY'\n")
                    f.write("op[1].save_name = '(mtl)_Roughness'\n")
                    f.write("op[2].type = 'R'\n")
                    f.write("op[2].RGB = 'METALLIC'\n")
                    f.write("op[2].R = 'EMPTY'\n")
                    f.write("op[2].G = 'EMPTY'\n")
                    f.write("op[2].B = 'EMPTY'\n")
                    f.write("op[2].A = 'EMPTY'\n")
                    f.write("op[2].save_name = '(mtl)_Metallic'\n")
                    f.write("op[3].type = 'RGB'\n")
                    f.write("op[3].RGB = 'NORMAL'\n")
                    f.write("op[3].R = 'EMPTY'\n")
                    f.write("op[3].G = 'EMPTY'\n")
                    f.write("op[3].B = 'EMPTY'\n")
                    f.write("op[3].A = 'EMPTY'\n")
                    f.write("op[3].save_name = '(mtl)_Normal'\n")
        except (OSError, PermissionError) as e:
            print(f"Failed to create or write to the file: {e}")
        initial_file = os.path.join(preset_folder, "ColorOnly.py")
        try:
            if not os.path.isfile(initial_file):
                with open(initial_file, "w") as f:
                    f.write("import bpy\n")
                    f.write("scene = bpy.context.scene\n")
                    f.write("op = bpy.context.scene.other_props.exportprops\n")

                    f.write("scene.other_props.height_to_normal = True\n")
                    f.write("scene.other_props.invert_green_n = False\n")
                    f.write("op[0].type = 'RGB'\n")
                    f.write("op[0].RGB = 'DIFFUSE'\n")
                    f.write("op[0].R = 'EMPTY'\n")
                    f.write("op[0].G = 'EMPTY'\n")
                    f.write("op[0].B = 'EMPTY'\n")
                    f.write("op[0].A = 'EMPTY'\n")
                    f.write("op[0].save_name = '(mtl)_Color'\n")
        except (OSError, PermissionError) as e:
            print(f"Failed to create or write to the file: {e}")
        return {"FINISHED"}


class OT_AddMyPreset(AddPresetBase, Operator):
    bl_idname = "paint.add_preset"
    bl_label = "Add a preset"
    preset_menu = "PR_MT_HASPresets"
    bl_options = {"REGISTER", "UNDO"}

    preset_defines = [
        "scene = bpy.context.scene",
        "op = bpy.context.scene.other_props.exportprops",
    ]

    preset_values = [
        "scene.other_props.height_to_normal",
        "scene.other_props.invert_green_n",
    ]
    preset_subdir = "haspresets/savedpresets"

    def execute(self, context):
        self.preset_values = [
            "scene.other_props.height_to_normal",
            "scene.other_props.invert_green_n",
        ]

        for idx, item in enumerate(context.scene.other_props.exportprops):
            self.preset_values.extend(
                [
                    f"op[{idx}].type",
                    f"op[{idx}].RGB",
                    f"op[{idx}].R",
                    f"op[{idx}].G",
                    f"op[{idx}].B",
                    f"op[{idx}].A",
                    f"op[{idx}].save_name",
                ]
            )
        return super().execute(context)


class OT_RemovePreset(Operator):
    bl_idname = "paint.remove_preset"
    bl_label = "Remove a preset"
    preset_menu = "PR_MT_HASPresets"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        current_preset = f"{context.scene.other_props.current_preset}.py"
        preset_folder = get_presets_folder()

        preset_path = os.path.join(preset_folder, current_preset)
        if os.path.exists(preset_path):
            try:
                os.remove(preset_path)
                self.report({"INFO"}, f"Preset '{current_preset}' removed successfully.")
            except Exception as e:
                self.report({"ERROR"}, f"Failed to remove preset: {str(e)}")
        else:
            self.report({"ERROR"}, f"Preset '{current_preset}' not found.")
        context.scene.other_props.current_preset = ""
        return {"FINISHED"}


class PR_MT_HASPresets(Menu):
    bl_idname = "PR_MT_HASPresets"
    bl_label = "My Presets"
    preset_subdir = "haspresets/savedpresets"
    preset_operator = "paint.execute_preset_has"
    draw = Menu.draw_preset


class ExecutePreset(Operator):
    """Execute a preset"""

    bl_idname = "paint.execute_preset_has"
    bl_label = "Execute a Python Preset"
    bl_options = {"REGISTER", "UNDO"}
    filepath: StringProperty(
        subtype="FILE_PATH",
        options={"SKIP_SAVE"},
    )
    menu_idname: StringProperty(
        name="Menu ID Name",
        description="ID name of the menu this was called from",
        options={"SKIP_SAVE"},
    )

    def execute(self, context):
        filepath = self.filepath
        bpy.context.scene.other_props.current_preset = os.path.splitext(os.path.basename(filepath))[0]
        # Read the preset file
        with open(filepath, "r") as file:
            lines = file.readlines()
        while len(context.scene.other_props.exportprops) > 0:
            context.scene.other_props.exportprops.remove(0)
        # Parse the file and assign values to the properties
        for line in lines:
            # Check if the line contains a property assignment for scene.other_props
            if "scene.other_props" in line:
                self.assign_scene_property(line, context)

            # Check if the line contains a property assignment for op[n]
            elif "op[" in line:
                self.assign_op_property(line, context)

        return {"FINISHED"}

    def assign_scene_property(self, line, context):
        # Handle scene.other_props assignments (e.g. scene.other_props.height_to_normal = True)
        match = re.search(r"scene\.other_props\.(\w+)\s*=\s*(\w+)", line)
        if match:
            prop_name = match.group(1)
            prop_value = match.group(2)

            # Convert string values to Python types (True/False, integers, etc.)
            if prop_value.lower() == "true":
                prop_value = True
            elif prop_value.lower() == "false":
                prop_value = False
            elif prop_value.isdigit():
                prop_value = int(prop_value)

            # Assign the value to the corresponding property
            setattr(context.scene.other_props, prop_name, prop_value)

    def assign_op_property(self, line, context):
        # Handle op[n] assignments (e.g. op[0].type = 'RGB')
        match = re.search(r"op\[(\d+)\]\.(\w+)\s*=\s*\'([^\']+)\'", line)
        if match:
            index = int(match.group(1))  # Extract the index from op[n]
            prop_name = match.group(2)  # Extract the property name (e.g. type, RGB)
            prop_value = match.group(3)  # Extract the assigned value (e.g. 'RGB')

            # Ensure the list is large enough to accommodate the index
            while len(context.scene.other_props.exportprops) <= index:
                context.scene.other_props.exportprops.add()

            # Assign the value to the property
            setattr(context.scene.other_props.exportprops[index], prop_name, prop_value)


class AddTextureTypeProp(Operator):
    bl_idname = "paint.add_texture_type_prop"
    bl_label = "Add Texture Type"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        context.scene.other_props.exportprops.add()
        return {"FINISHED"}


class TEXTURE_PT_file_browser_panel(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "HAS Export Textures"

    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        return (
            space_data.type == "FILE_BROWSER"
            and space_data.params is not None
            and space_data.active_operator
            and space_data.active_operator.bl_idname == "PAINT_OT_export_textures"
        )

    def draw(self, context):
        layout = self.layout
        other_props = context.scene.other_props

        box = layout.box()

        row = box.row(align=True)
        row.menu(
            "PR_MT_HASPresets",
            text="Template Presets" if not bpy.context.scene.other_props.current_preset else bpy.context.scene.other_props.current_preset,
            icon="COLLAPSEMENU",
        )
        row.operator("paint.add_preset", text="", icon="ADD")
        row.operator("paint.remove_preset", text="", icon="REMOVE")
        row = box.row(align=True)
        row.operator("paint.load_presets", text="Load Default HAS Presets", icon="PRESET_NEW")

        boxd = box.box()
        boxd.prop(other_props, "height_to_normal", text="Height to Normal")
        boxd.prop(other_props, "invert_green_n", text="Normal Invert G Channel")

        boxd = box.box()
        boxd.label(text="Allowed properties: (obj), (mtl), (file), (set)")
        row = boxd.row(align=True)
        row.label(text="Pack Images")
        for idx, item in enumerate(context.scene.other_props.exportprops):
            boxq = boxd.box()
            row = boxq.row(align=True)
            row.prop(item, "expand", text="", toggle=True, icon="TRIA_DOWN" if item.expand else "TRIA_RIGHT")
            row.prop(item, "save_name", text="")
            row.operator("paint.remove_texture_type_prop", text="", icon="X").index = idx
            if item.expand:
                row = boxq.column(align=True)
                row.prop(item, "type", text="")
                if item.type == "RGB":
                    row.prop(item, "RGB", text="RGB")
                elif item.type == "RGBA":
                    row.prop(item, "RGBA", text="RGBA")
                elif item.type == "RGB_A":
                    row.prop(item, "RGB", text="RGB")
                    row.prop(item, "A", text="A")
                elif item.type == "R_G_B_A":
                    row.prop(item, "R", text="R")
                    row.prop(item, "G", text="G")
                    row.prop(item, "B", text="B")
                    row.prop(item, "A", text="A")
                elif item.type == "R":
                    row.prop(item, "R", text="R")
        box.operator("paint.add_texture_type_prop", text="Add Texture Type")


classes = [
    OT_AddMyPreset,
    OT_RemovePreset,
    PR_MT_HASPresets,
    ExecutePreset,
    AddTextureTypeProp,
    TEXTURE_PT_file_browser_panel,
    LoadPresetsOperator,
]


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
