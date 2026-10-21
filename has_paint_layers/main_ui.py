import bpy
from bpy.utils import register_class, unregister_class
from bpy.props import StringProperty, IntProperty
from bpy.types import Panel, Operator, Menu, Scene
from .utils.utils import *
from .operators import *
from .has_enum import *
from .tools import *

from .ui.layer_properties_ui import drawcompactlinelayerbox, drawlayerbox, drawfolderbox


class HAS_PT_LayersPanel(bpy.types.Panel):
    bl_label = "WkHAS Paint Layers 122"
    bl_idname = "HAS_PT_LayersPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    bl_category = "HAS Paint Layers"

    def draw(self, context):

        layout = self.layout

        butcol = layout.row()
        butcol.prop(context.scene.other_props, "expand_area_butfile", text="", icon="FILE_BLEND")
        butcol.prop(context.scene.other_props, "expand_area_butmtl", text="", icon="NODE_MATERIAL")
        butcol.prop(context.scene.other_props, "expand_area_buttools", text="", icon="TOOL_SETTINGS")
        butcol.prop(context.scene.other_props, "expand_area_butlayers", text="", icon="RENDERLAYERS")
        butcol.label(text="")

        op = butcol.operator("paint.open_website", text="", icon="QUESTION")
        op.link = "https://hirourk.github.io/HASPaintLayersWiki/index.html"
        boxw = layout
        if bpy.context.active_object:
            if not bpy.context.active_object or not bpy.context.active_object.type == "MESH":
                return
            part = get_material_collection()
            if not part:
                if not bpy.context.active_object.data.materials or not check_mtl_used():
                    box = layout.box()
                    box.operator("paint.setup_material", text="Setup material", icon="ADD", emboss=False)
                    return
            if context.scene.other_props.expand_area_butfile:
                box = boxw.box()
                box.prop(context.scene.other_props, "expand_area_Actions", text="File", icon="FILE_BLEND", emboss=False)

                if context.scene.other_props.expand_area_Actions:
                    boxs = box.box()
                    row = boxs.row(align=False)

                    row.operator("paint.save_layers", text="Save All Textures", icon="FILE_TICK")
                    row.prop(
                        context.scene.other_props,
                        "toggle_save",
                        text=f"Auto Save Textures",
                        icon="CHECKBOX_HLT" if context.scene.other_props.toggle_save else "CHECKBOX_DEHLT",
                    )
                    row = boxs.row(align=False)

                    rowb = boxs.box()
                    rowb.scale_y = 2.0
                    rowb.operator("paint.export_textures", text="Export Textures", icon="EXPORT")
                    row = rowb.row(align=False)

                    row.operator("paint.export_to_ora", text="Export Layers", icon="EXPORT")
                    row.operator("paint.import_from_ora", text="Import Layers", icon="IMPORT")

                    row = box.row(align=False)
                    box = box.box()
                    row.box().operator("paint.cleanup", text="Cleanup HAS Data", icon="FAKE_USER_OFF", emboss=False)
                    rowl = box.row(align=True)
                    rowl.prop(
                        context.scene.other_props,
                        "expand_area_MaterialCollection",
                        text="HAS Set collection",
                        icon="MATERIAL",
                        emboss=False,
                    )

                    if context.scene.other_props.expand_area_MaterialCollection:
                        box.label(text="Registered Materials")
                        rowl = box.row(align=True)

                        rowl.label(text="Set names")
                        rowl.label(text="Materials")
                        for i, p in enumerate(context.scene.material_props):
                            rowl = box.row(align=True)
                            rowl.prop(p, "name", text="")
                            rowl.prop(p, "material", text="")
                            rowl.operator("paint.remove_material", text="", icon="REMOVE").index = i

            if not bpy.context.active_object.data.materials or not check_mtl_used():
                box = layout.box()
                box.operator("paint.setup_material", text="Setup material", icon="ADD", emboss=False)
                return

            if context.scene.other_props.expand_area_butmtl:
                box = boxw.box()
                box.prop(context.scene.other_props, "expand_area_MtlSettings", text="Material", icon="NODE_MATERIAL", emboss=False)
                if context.scene.other_props.expand_area_MtlSettings:

                    rowd = box.column()
                    row1 = rowd.row()
                    row1.label(text="Material Set Name")
                    row1.prop(part, "name", text="")
                    row1 = rowd.row()
                    row1.label(text="Select Maps")
                    row1.operator("paint.setusedmaps", text="Maps", icon="COLLAPSEMENU")

                    row1 = rowd.row()
                    row1.label(text="Shader Type")
                    row1.prop(part, "shader_type", text="")
                    row1 = rowd.row()
                    row1.label(text="Texture filtering")
                    row1.prop(part, "texture_filtering", text="")
                    row1 = rowd.row()
                    row1.label(text="UV Channel")
                    row1.prop(part, "uvs", text="")
                    row1 = rowd.row()
                    row1.label(text="Height Intensity")
                    row1.prop(part, "height_intensity", text="")
                    row1 = rowd.row()
                    row1.label(text="Transparency Mode")
                    row1.prop(part, "opacity_mode", text="")
                    row1 = rowd.row()
                    row1.label(text="Alpha")
                    row1.prop(part, "diffusealpha", text="Use Diffuse Alpha", toggle=True)
                    row1 = rowd.row()
                    row1.label(text="Invert G in Normal")
                    row1.prop(part, "InvertG", text="")
                    # row1 = rowd.row()
                    # row1.label(text= "Fix")
                    # row1.prop(part, "colorfix", text="")

                    row = box.row(align=False)
                    row.label(text="Texture size")
                    txl = row.operator("paint.texture_size_add_subtract", text="", icon="ADD")
                    txl.add = True
                    txl.isbake = False
                    txl = row.operator("paint.texture_size_add_subtract", text="", icon="REMOVE")
                    txl.add = False
                    txl.isbake = False
                    row.prop(part, "texture_sizeX", text="X")
                    row.prop(part, "texture_sizeY", text="Y")
                    box = box.box()
                    box.prop(
                        context.scene.other_props,
                        "expand_area_DefaultMaterial",
                        text="Default Material Values",
                        icon="PROPERTIES",
                        emboss=False,
                    )
                    if context.scene.other_props.expand_area_DefaultMaterial:
                        node = get_node_by_name(bpy.context.active_object.active_material.node_tree, part.node)

                        if node:
                            colsq = box.column(align=False)
                            for ind, input_socket in enumerate(node.inputs):
                                colsqrow = colsq.row(align=True)
                                if input_socket.type == "RGBA":
                                    colsqrow.label(text=input_socket.name)
                                    colsqrow.prop(input_socket, "default_value", text="")

            if context.scene.other_props.expand_area_buttools:
                box = boxw.box()
                box.prop(context.scene.other_props, "expand_area_ProjectTexture", text="Tools", icon="TOOL_SETTINGS", emboss=False)
                if context.scene.other_props.expand_area_ProjectTexture:
                    rws = box.row()
                    op = rws.operator(
                        "paint.activate_tab",
                        text="Quick Edit",
                        icon="OUTLINER_OB_IMAGE",
                        emboss=context.scene.other_props.expand_area_QuickEdit,
                    )
                    op.activate_tab = 0

                    op = rws.operator(
                        "paint.activate_tab", text="Masking", icon="MOD_MASK", emboss=context.scene.other_props.expand_area_DepthSelection
                    )
                    op.activate_tab = 1

                    op = rws.operator(
                        "paint.activate_tab", text="Paint Tools", icon="BRUSH_DATA", emboss=context.scene.other_props.expand_area_PaintTools
                    )
                    op.activate_tab = 2

                    op = rws.operator(
                        "paint.activate_tab", text="Bake", icon="OUTLINER_OB_VOLUME", emboss=context.scene.other_props.expand_area_Bake
                    )
                    op.activate_tab = 3

                    if context.scene.other_props.expand_area_QuickEdit:
                        boxs = box.box()
                        rowq = boxs.row(align=False)

                        if not context.scene.view_settings.view_transform == "Standard":

                            rowqs = boxs.row(align=False)
                            spl = rowqs.split(factor=0.8)
                            spl.column().label(text=f"{context.scene.view_settings.view_transform} Will Cause Issues With Colors")
                            spl.alert = True
                            spl.column().operator("paint.setstandardvt", text="Fix", icon="ERROR")

                        if bpy.context.preferences.filepaths.image_editor:
                            rowq.alert = bpy.context.scene.other_props.operator_running
                            rowq.operator("paint.crop_tool", text="Select region for quick edit", icon="OBJECT_DATAMODE")

                            rowq.prop(context.scene.other_props, "screen_capture_scale", text="Capture scale")
                            rowq.operator("paint.setquefolder", text="", icon="FILE_FOLDER")

                            for index, vd in enumerate(context.scene.view_data):

                                rowq = box.row()

                                # op = rowq.operator('paint.snap_to_view', text="", icon = "SCREEN_BACK") #TODO Implement this function
                                # op.index = index
                                op = rowq.operator(ProjectApply.bl_idname, text="", icon="IMPORT")
                                op.index = index
                                op = rowq.operator(ProjectOpen.bl_idname, text=vd.image_name, icon="FILE_IMAGE")
                                op.index = index
                                op = rowq.operator(ProjectRemove.bl_idname, text="", icon="PANEL_CLOSE")
                                op.index = index
                        else:
                            rowq.label(text="External Image Editor Path:")
                            rowq.prop(context.preferences.filepaths, "image_editor", text="")

                    if context.scene.other_props.expand_area_DepthSelection:
                        boxs = box.box()
                        boxs.label(text="Mask by depth")
                        bxsplit = boxs.split(factor=0.5)
                        rowq = bxsplit.column(align=True)
                        rowq.prop(context.scene.debugplane_props, "plane_size", text="Size")
                        rowq.prop(context.scene.debugplane_props, "plane_color", text="")

                        rowq = bxsplit.column(align=True)
                        rowqrs = rowq.row(align=True)
                        rowqrs.operator("paint.depth_mask_operator", text="Select By Depth", icon="CLIPUV_DEHLT")
                        rowqrs.prop(context.scene.debugplane_props, "depth_distance", text="Depth")

                        rowq.operator("paint.adjust_depth_distance_operator", text="Adjust Depth", icon="ARROW_LEFTRIGHT")

                    if context.scene.other_props.expand_area_PaintTools:
                        boxs = box.box()
                        boxs.label(text="Paint By")

                        row = boxs.row(align=False)
                        row.operator("paint.paint_by_selection", text="Face", icon="SNAP_FACE").mode = "POLYGON"
                        row.operator("paint.paint_by_selection", text="UV", icon="UV_DATA").mode = "UV_ISLAND"
                        row.operator("paint.paint_by_selection", text="Part", icon="SNAP_VOLUME").mode = "PART"

                    if context.scene.other_props.expand_area_Bake:
                        boxs = box.box()
                        baking_props = part.baking_props
                        colboxs = boxs.column(align=True)
                        boxe = colboxs.box()
                        brow = boxe.row(align=True)
                        brow.prop(
                            baking_props, "visible_hp", text="", icon="HIDE_OFF" if baking_props.visible_hp else "HIDE_ON", emboss=False
                        )
                        brow.prop(
                            baking_props,
                            "expand_hp",
                            text=f"High ({len(baking_props.high_poly_obj)-1})",
                            icon="MESH_UVSPHERE",
                            emboss=False,
                        )

                        orp = brow.operator("paint.remove_all_bake_objects", text="", icon="TRASH", emboss=False)
                        orp.hp = True

                        if baking_props.expand_hp:
                            colbox = boxe.column(align=True)
                            for ob in baking_props.high_poly_obj:
                                colbox.prop(ob, "obj", text="")
                            if len(baking_props.high_poly_obj) == 0:
                                colbox.label(text="Empty collection")

                        boxe = colboxs.box()
                        brow = boxe.row(align=True)
                        brow.prop(
                            baking_props, "visible_lp", text="", icon="HIDE_OFF" if baking_props.visible_lp else "HIDE_ON", emboss=False
                        )
                        brow.prop(
                            baking_props, "expand_lp", text=f"Low ({len(baking_props.low_poly_obj)-1})", icon="MESH_ICOSPHERE", emboss=False
                        )

                        orp = brow.operator("paint.remove_all_bake_objects", text="", icon="TRASH", emboss=False)
                        orp.hp = False
                        if baking_props.expand_lp:
                            colbox = boxe.column(align=True)
                            for ob in baking_props.low_poly_obj:
                                colbox.prop(ob, "obj", text="")
                        if baking_props.high_poly_obj or baking_props.low_poly_obj:

                            hps = baking_props.gethpobjects(context)
                            lps = baking_props.getlpobjects(context)
                            for eg in lps:
                                if eg:
                                    if eg in hps:
                                        boxe = colboxs.box()
                                        boxe.label(text="Duplicate object found, collections should have unique objects")
                                        break

                            rowg1 = colboxs.box()
                            rowg = rowg1.row(align=True)

                            rowg.prop(
                                baking_props,
                                "visible_cage",
                                text="",
                                icon="HIDE_OFF" if baking_props.visible_cage else "HIDE_ON",
                                emboss=False,
                            )
                            rowg.prop(baking_props, "use_cage", text="Cage", icon="CUBE", emboss=baking_props.use_cage)

                            if baking_props.use_cage:
                                rowg.prop(
                                    baking_props,
                                    "smooth_cage",
                                    text="Smooth Cage",
                                    icon="META_PLANE" if baking_props.smooth_cage else "MESH_PLANE",
                                )
                                rowg = rowg1.row()
                                rowg.prop(baking_props, "cage_depth", text="Offset")
                                rowg.prop(baking_props, "cage_color", text="")

                        boxs = boxs.box()
                        rowt = boxs.row(align=False)
                        rowt.label(text="Size")
                        txb = rowt.operator("paint.texture_size_add_subtract", text="", icon="ADD")
                        txb.add = True
                        txb.isbake = True
                        txb = rowt.operator("paint.texture_size_add_subtract", text="", icon="REMOVE")
                        txb.add = False
                        txb.isbake = True
                        rowt.prop(baking_props, "bake_image_sizeY", text="")
                        rowt.prop(baking_props, "bake_image_sizeX", text="")
                        rowt = boxs.row(align=False)
                        rowt.label(text="Settings")
                        rowt.prop(baking_props, "samples", text="Samples")

                        rowt = boxs.row(align=False)
                        rowt.label(text="Maps")
                        rowt.operator("paint.add_bake_map", text="", icon="ADD")

                        for ind, bake_map in enumerate(part.bake_maps):

                            box2 = boxs.row()
                            box2.prop(
                                bake_map,
                                "use_map",
                                text="",
                                icon="SHADING_RENDERED" if bake_map.use_map else "SHADING_WIRE",
                                icon_only=True,
                            )

                            if bake_map.type == "HEIGHT" or bake_map.type == "DIFFUSE":
                                if not baking_props.high_poly_obj:
                                    box2.label(text="No Bake Source Selected", icon="ERROR")
                            if bake_map.image:
                                slct = bpy.context.scene.other_props.preview_image == bake_map.image

                                isolate = box2.operator("paint.isolate_image", text="", icon="IMAGE_REFERENCE", depress=slct)
                                isolate.texture_name = bake_map.image.name
                            bpr = box2.operator("paint.bakemapprefs", text="", icon="TOOL_SETTINGS")
                            bpr.bake_type = bake_map.type
                            box2.prop(bake_map, "type", text="")

                            box2.template_ID(bake_map, "image", open="image.open", text="")
                            box2.operator("paint.remove_bake_map", text="", icon="REMOVE").index = ind

                        rowt = boxs.row(align=False)
                        rowt.enabled = True if part.bake_maps else False
                        rowt.scale_y = 2.0
                        rowt.operator("paint.bake_textures", text="Bake", icon="OUTLINER_OB_VOLUME")

            if context.scene.other_props.expand_area_butlayers:
                rowl = layout.row(align=False)
                box = rowl.box()
                row = box.row(align=False)
                nimg = row.operator("paint.custom_new", text="", icon="BRUSH_DATA", emboss=False)
                nimg.fill = False
                box = rowl.box()
                row = box.row(align=False)
                nimg = row.operator("paint.custom_new", text="", icon="IMAGE", emboss=False)
                nimg.fill = True

                box = rowl.box()
                row = box.row(align=False)
                row.operator("paint.create_pbr", text="", icon="NODE_MATERIAL", emboss=False)

                box = rowl.box()
                row = box.row(align=False)
                row.operator("paint.create_folder", text="", icon="FILE_FOLDER", emboss=False)

                rowl.label(text="")
                box = rowl.box()
                row = box.row(align=False)
                row.prop(context.scene.other_props, "preview_mode", text="", icon="SHADING_RENDERED", icon_only=True, emboss=False)
                box = rowl.box()
                row = box.row(align=False)
                row.prop(part, "mtl_actions", text="", icon="COLLAPSEMENU", icon_only=True, emboss=False)

                part = get_material_collection()
                if not part:
                    return
                masks = []
                group_box = None
                if not context.scene.other_props.fixed:
                    rowqs = layout.row()
                    rowqs.alert = True
                    rowqs.operator("paint.setupscene", text="Setup Scene", icon="SCENE_DATA")
                    rowqs.scale_y = 2.0
                rowqs = layout.row()

                for templayer in reversed(part.base_layers):
                    rowl = layout.row()
                    layer = templayer.get_layer()
                    if layer:
                        layerbox(self, context, rowl, part.base_layers, masks, templayer.index, None)


def layerbox(self, context, layout, layers, masks, index, parent):
    drawlayerbox(self, context, layout, layers, masks, index, parent)


def compactlinelayerbox(self, context, layout, layers, masks, index):
    drawcompactlinelayerbox(self, context, layout, layers, masks, index)


def folderbox(self, context, layout, layer, masks, index):
    drawfolderbox(self, context, layout, layer, masks, index)


def compactlayerbox(self, context, layout, layer, masks, allselected, baselayer):
    # UI element. Layer properties. Used for PBR channels
    split = layout
    selected = False
    if layer.resource.image:
        selected = context.scene.selected_texture == layer.resource.image.name

    split = split.split(factor=0.2)
    middle_column = split.column()

    row = middle_column.row(align=True)

    row.label(text=getlabel(layer.texture_type))
    rsg = layout.row(align=True)

    if not layer.resource.image:
        if (
            layer.texture_type == "DIFFUSE"
            or layer.texture_type == "EMISSION"
            or layer.texture_type == "CUSTOM"
            or layer.texture_type == "NORMAL"
        ):
            rsg.prop(layer.resource, "default_color", text="", emboss=True)
        else:
            rsg.prop(layer.resource, "default_value", text="", emboss=True, slider=True)

    rsg.prop(layer.resource, "image", text="")
    if not layer.resource.image:

        op = rsg.operator("paint.open_image_file", text="", icon="FILE_FOLDER", emboss=True)
        op.layer_index = layer.index
    if layer.resource.image:
        rsg = layout.column(align=True)
        draw_mapping_box(rsg, layer.resource)
    row.scale_y = 1.0

    right_column = split.column(align=True)

    row = right_column.row(align=False)

    row.prop(layer, "blend_mode", text="", emboss=False)

    opas = row.operator("paint.opacity_controller", text=f"{round(layer.opacity*100)/100}", emboss=False)
    opas.layer_index = layer.index

    if layer.filters:
        rowbox = layout.column(align=True)
        for findex, filter in enumerate(reversed(layer.filters)):

            findex = len(layer.filters) - 1 - findex
            uifilter(self, context, layer, filter, findex, rowbox, layer.index)


def uifilter(self, context, layer, filter, index, rowbox, lindex):
    # UI element. Filter properties box
    rowbox = rowbox.box()
    row = rowbox.row(align=True)
    if filter.name == "PAINT":
        if filter.resource.image:
            slct = context.scene.selected_texture == filter.resource.image.name
            select_op = row.operator(
                "paint.select_texture", text="", icon="SNAP_FACE" if slct else "SHADING_BBOX", depress=True if slct else False
            )
            select_op.texture_name = filter.resource.image.name
            select_op.id = layer.id
            select_op.alpha = "Skip"
    hid = row.operator("paint.showhidefilter", text="", icon="HIDE_OFF" if filter.in_use else "HIDE_ON", emboss=False)
    hid.layer_index = lindex
    hid.filter_index = index
    hid.compfilter = False

    row.prop(filter, "edit", text="", icon="TRIA_DOWN" if filter.edit else "TRIA_RIGHT", emboss=False)

    filter_value = next((item for item in FILTERS if item and item[0] == filter.name), None)
    if filter_value:
        op = row.operator("paint.filter_select", text=filter_value[1], icon=filter_value[3], emboss=False)
    else:
        op = row.operator("paint.filter_select", text="Select Filter", icon="BLANK1", emboss=False)
    op.layer_index = lindex
    op.filter_index = index

    if filter.name == "CUSTOM" and filter.custom_node_tree_p and not filter.edit:
        row.prop_search(filter, "custom_node_tree_p", bpy.data, "node_groups", text="")
        # row.prop(filter, "custom_node_tree", text="", emboss=False)
    otp = context.scene.other_props

    move_up = row.operator("paint.move_filter", text="", icon="TRIA_UP", emboss=False)
    move_up.layer_index = lindex
    move_up.filter_index = index
    move_up.direction = "UP"
    move_down = row.operator("paint.move_filter", text="", icon="TRIA_DOWN", emboss=False)
    move_down.layer_index = lindex
    move_down.filter_index = index
    move_down.direction = "DOWN"

    remove_filter = row.operator("paint.remove_layer_filter", text="", icon="TRASH", emboss=False)
    remove_filter.layer_index = lindex
    remove_filter.filter_index = index

    socket_ui_mapping = {
        "VALUE": "value",
        "RGBA": "color",
        "VECTOR": "vector",
    }
    ignoreinputs = False

    if filter.edit:
        if filter.name == "CUSTOM":
            rowbox.prop_search(filter, "custom_node_tree_p", bpy.data, "node_groups", text="")
            alt = True
        else:
            alt = False
        row = row.row(align=True)
        node_group = bpy.data.node_groups.get(f"{getlayergroupname(layer)}_filters")

        if node_group:

            node = node_group.nodes.get(filter.node_name)
            opr = rowbox.column()

            rowsgefs = opr.row()
            rowsgefs.prop(filter, "blend_mode", text="", emboss=False)
            rowsgefs.prop(filter, "opacity", text="Opacity", emboss=False, slider=True)
            rowsge = opr.row(align=True)
            if layer.layer_type == "FOLDER" or layer.layer_type == "PBR":
                rowsge.prop(filter, "affect_channels", text="", emboss=False)

            if node:
                if filter.name == "COLORRAMP":
                    rowbox.box().template_color_ramp(node, "color_ramp", expand=False)
                elif filter.name == "SEPARATERGB":
                    alt = True
                elif filter.name == "LEVELS":
                    drawlevels(
                        filter.levels, rowbox, histogram_source=layer.resource.image.name if layer.resource.image else None, skipexpand=True
                    )

                elif filter.name == "CURVERGB":
                    rowbox.box().template_curve_mapping(node, "mapping", type="COLOR", levels=False)

                elif filter.name == "MASKCOLOR":
                    ros = rowbox.row(align=True)
                    if bpy.context.scene.other_props.preview_image:
                        ros.alert = True

                    if filter.resource.image:
                        isolate = ros.operator(
                            "paint.isolate_image", text="Preview", icon="IMAGE_REFERENCE" if filter.in_use else "FILE_IMAGE"
                        )
                        isolate.texture_name = filter.resource.image.name
                    ros.template_ID(filter.resource, "image", open="image.open", text="ID Map")

                elif filter.name == "PAINT":
                    ros = rowbox.row(align=False)
                    ignoreinputs = True
                    islt = False
                    if bpy.context.scene.other_props.preview_image == filter.resource.image:
                        islt = True
                    if filter.resource.image:
                        slct = context.scene.selected_texture == filter.resource.image.name
                        select_op = ros.operator(
                            "paint.select_texture", text="", icon="SNAP_FACE" if slct else "SHADING_BBOX", depress=True if slct else False
                        )
                        select_op.texture_name = filter.resource.image.name
                        select_op.id = layer.id
                        select_op.alpha = "Skip"
                        isolate = ros.operator(
                            "paint.isolate_image", text="", icon="IMAGE_REFERENCE" if filter.in_use else "FILE_IMAGE", depress=islt
                        )
                        isolate.texture_name = filter.resource.image.name

                elif filter.name == "FILL":
                    ros = rowbox.column(align=False)
                    ignoreinputs = True
                    islt = False
                    if bpy.context.scene.other_props.preview_image == filter.resource.image:
                        islt = True

                    if filter.resource.image:
                        ros.template_ID_preview(filter.resource, "image", open="image.open", rows=4, cols=6, hide_buttons=False)
                    else:
                        ros.template_ID(filter.resource, "image", open="image.open")
                    if not filter.resource.image:
                        rs = ros.row()
                        rs.scale_y = 2.0
                        rs.prop(
                            filter.resource, "default_value" if filter.connection_type == "ALPHA" else "default_color", text="", slider=True
                        )
                    if filter.resource.image:
                        draw_mapping_box(rowbox, filter.resource)
                elif filter.name == "MASKGEN":
                    ignoreinputs = True
                    ros = rowbox.box() if filter.maskgen.expand else rowbox
                    ros1 = ros.row()
                    ros1.prop(
                        filter.maskgen,
                        "expand",
                        text="Grunge",
                        icon="DISCLOSURE_TRI_DOWN" if filter.maskgen.expand else "DISCLOSURE_TRI_RIGHT",
                        emboss=False,
                    )

                    if filter.maskgen.expand:
                        rowcol = ros.column()

                        row1 = rowcol.row()
                        if filter.resource.image:
                            texture = bpy.data.images.get(filter.resource.image.name)
                            if texture and texture.preview:
                                icon_id = texture.preview.icon_id
                                row1.template_icon(icon_id, scale=2.0)
                        else:
                            row1.label(text="Choose Image")

                        row1.template_ID(filter.resource, "image", open="image.open", text="")
                        if filter.resource.image:
                            rowcol.prop(filter.resource, "expand_mapping", text="Mapping", icon="TEXTURE", emboss=False)
                            box = rowcol.column()
                            if filter.resource.expand_mapping:

                                rwbs = box.row()
                                rwbs.label(icon="MOD_EDGESPLIT")
                                rwbs.prop(filter.resource, "repeat", text="")
                                bws = box.row(align=True)
                                bws.label(text="Offset")
                                bws = box.row(align=True)
                                bws.prop(filter.resource, "mapx", text="X")
                                bws.prop(filter.resource, "mapy", text="Y")
                                bws = box.row(align=True)
                                bws.label(text="Scale")
                                bws = box.row(align=True)
                                bws.prop(filter.resource, "mapscalex", text="")
                                bws.prop(filter.resource, "mapscaley", text="")
                                bws = box.row(align=True)
                                bws.label(text="Rotate")
                                bws.prop(filter.resource, "maprot", text="")

                            box.prop(filter.resource.levels, "expand", text="Levels", icon="SEQ_HISTOGRAM", emboss=False)

                            if filter.resource.levels.expand:
                                rowcol = rowcol.box()
                                nodein = filter.resource.levels.levels_node.get_node()
                                if nodein:
                                    drawlevels(filter.resource.levels, rowcol, histogram_source=filter.resource.image.name, skipexpand=True)

                    for itm in MASKITEMS:
                        maskitem = filter.maskgen.get_item(itm[0])
                        cols = rowbox.column(align=True)
                        if maskitem:
                            bros = cols.box() if getattr(filter.maskgen, itm[3], None) else cols
                            bros.prop(
                                filter.maskgen,
                                itm[3],
                                text=f"{itm[0]} Static" if maskitem.image else f"{itm[0]} Realtime",
                                toggle=True,
                                emboss=False,
                                icon="DISCLOSURE_TRI_DOWN" if getattr(filter.maskgen, itm[3], None) else "DISCLOSURE_TRI_RIGHT",
                            )
                            if getattr(filter.maskgen, itm[3], None):
                                brosrow = bros.row()
                                brosrow.label(text="" if maskitem.image else "Optionally Choose Baked Map")
                                brosrow.template_ID(maskitem, "image", open="image.open", text="")
                                nodein = maskitem.levels.levels_node.get_node()
                                if nodein:
                                    drawlevels(
                                        maskitem.levels,
                                        bros,
                                        histogram_source=maskitem.image.name if maskitem.image else "",
                                        skipexpand=True,
                                        compact=True,
                                    )

                elif filter.name == "LIGHT":
                    filnd = filter.displnode.get_node()
                    if filnd:
                        rowbox.prop(filnd.outputs[0], "default_value", text="")
                    if not filter.resource.image:
                        rowbox.label(text="Create Object Normal Map before applying or exporting")
                    rowbox.template_ID(filter.resource, "image", text="Object Normal Map")

                if not ignoreinputs:
                    uiinputs(rowbox, node, layer, index, filter, lindex, alt)

        if filter.name == "SNAPSHOT" or filter.name == "BLUR":
            rosb = rowbox.box()
            ros = rosb.row(align=True)
            op = ros.operator("paint.open_website", text="", icon="QUESTION")
            op.link = "https://hirourk.github.io/HASPaintLayersWiki/03Filters"
            if filter.name == "BLUR":
                bi = ros.operator("paint.snapshotlayer", text="Apply Blur", icon="OUTLINER_OB_IMAGE")
                bi.layer_index = lindex
                bi.filter_index = index
                ros.prop(filter, "Unspval", text="Blur Size")
            else:
                bi = ros.operator("paint.snapshotlayer", text="Snapshot", icon="OUTLINER_OB_IMAGE")
                bi.layer_index = lindex
                bi.filter_index = index

            bi.layer_index = lindex
            bi.filter_index = index
            bi.addfilter = filter.name
            bi.addfiltervalue = filter.Unspval


def ui_common_inputs(layout, node):
    # UI element. Properties from node sockets
    socket_ui_mapping = {
        "VALUE": "value",
        "RGBA": "color",
        "VECTOR": "vector",
    }

    for ind, input_socket in enumerate(node.inputs):
        socket_type = input_socket.type
        socket_ui_type = socket_ui_mapping.get(socket_type)
        if socket_ui_type:
            socket_id = f"{input_socket.name}_{ind}"
            layout.prop(input_socket, "default_value", text=input_socket.name)


def uiinputs(rowbox, node, layer, index, filter, lindex, alt):
    # UI element. Properties from node sockets
    socket_ui_mapping = {
        "VALUE": "value",
        "RGBA": "color",
        "VECTOR": "vector",
    }
    if alt:
        split = rowbox.split(factor=0.75)
        col = split.column()
        colout = split.column()
    else:
        col = rowbox
    for ind, input_socket in enumerate(node.inputs):
        if not alt:
            if input_socket.is_linked:
                continue
        if input_socket.name == "Fac":
            return
        socket_type = input_socket.type
        socket_ui_type = socket_ui_mapping.get(socket_type)
        filtersockets(input_socket, socket_ui_mapping, col, ind, filter, layer, index, alt)
    if alt:
        for ind, input_socket in enumerate(node.outputs):
            socket_type = input_socket.type
            socket_ui_type = socket_ui_mapping.get(socket_type)
            filtersockets(input_socket, socket_ui_mapping, colout, ind, filter, layer, index, alt, inp=False)


def filtersockets(input_socket, socket_ui_mapping, col, ind, filter, layer, index, hide, inp=True):
    # UI element. Properties from node sockets
    socket_type = input_socket.type
    socket_ui_type = socket_ui_mapping.get(socket_type)
    if socket_ui_type:

        socket_id = f"{input_socket.name}_{ind}"
        rowc = col.row(align=False)
        sc = filter.socket_in if inp else filter.socket_out
        rowc.enabled = not input_socket.is_linked
        if hide:
            cinput = rowc.operator("paint.filter_inout", text="", icon="RADIOBUT_ON" if sc == ind else "RADIOBUT_OFF", emboss=False)
            cinput.layer_index = layer.index
            cinput.filter_index = index
            cinput.inputind = ind

            cinput.inpout = inp

        rowc.prop(input_socket, "default_value", text=input_socket.name, slider=True)


def drawresource(layout, resource):
    # UI element. Resource properties
    box = layout.column()
    box.template_ID(resource, "image", new="", open="image.open")
    if resource.image:
        if resource.image.preview:

            brr = box.row()

            brr.template_ID_preview(resource, "image", open="image.open", rows=4, cols=6, hide_buttons=True)
    else:
        boxe = box.row()
        boxe.prop(resource, "default_color", text="")
        boxe.scale_y = 1.0
    if resource.image:
        box = box.column()
        box.prop(resource, "repeat", text="")
        bws = box.row()
        bws.prop(resource, "mapx", text="Offset X")
        bws.prop(resource, "mapy", text="Offset Y")
        bws = box.row()
        bws.prop(resource, "mapscalex", text="Scale X")
        bws.prop(resource, "mapscaley", text="Scale Y")
        bws = box.row()
        bws.prop(resource, "maprot", text="Rotate")


def drawlevels(levels, rowbox, histogram_source="", skipexpand=False, compact=False):
    # UI element. Imitate Levels box
    box = rowbox.row(align=True)

    histe = None
    if not skipexpand:
        box.prop(levels, "expand", text="Levels", icon="SEQ_HISTOGRAM", emboss=False)
        if not levels.expand:
            return

    otp = bpy.context.scene.other_props
    count = 70
    b = round(remap_value(levels.val01, 0.0, 1.0, 0.0, count - 1))
    w = round(remap_value(levels.val03, 0.0, 1.0, 0.0, count - 1))
    m = round(lerp(b, w, levels.val02))
    db = round(remap_value(levels.val04, 0.0, 1.0, 0.0, count - 1))
    dw = round(remap_value(levels.val05, 0.0, 1.0, 0.0, count - 1))
    inv = b > w
    ignoreinputs = True
    rowbox = rowbox.column(align=True)
    if compact:
        xsb = rowbox.box()
        drawlevels_vis_01(xsb, b, w, m, count=count)
        drawlevels_vis_02(xsb, db, dw, count=count)
    if compact:
        bx = rowbox.row(align=True)
    else:
        bx = rowbox.column(align=True)

    bx.prop(levels, "val01", text="Shadows", slider=True)
    bx.prop(levels, "val02", text="Midtones", slider=True)
    bx.prop(levels, "val03", text="Highlights", slider=True)

    if not compact:
        xsb = rowbox.box()
        if histogram_source:
            sdq = xsb.row()
            sdq.prop(levels, "s_channel", emboss=True, icon_only=True)
            sdq.prop(levels, "expand_levels", text="Histogram", icon="SEQ_HISTOGRAM", emboss=False)
            if levels.expand_levels:
                histe = sdq.operator("paint.update_hist", icon="FILE_REFRESH", text="", emboss=False)
                histe.texture_name = histogram_source
        drawlevels_vis_01(xsb, b, w, m, count=count)
        if levels.expand_levels:

            if histe:
                name = ".HAS_SceneProperties"
                if name in bpy.data.node_groups:
                    node_group = bpy.data.node_groups[name]
                    histnode = get_node_by_name(node_group, histogram_source)
                    if histnode:
                        wr = xsb.column(align=True)
                        wr.scale_y = 0.3
                        wr.enabled = False
                        wr.template_curve_mapping(histnode, "mapping", type="COLOR", levels=False)
        drawlevels_vis_02(xsb, db, dw, count=count)

    if compact:
        bx = rowbox.row(align=True)
    else:
        bx = rowbox.column(align=True)
    bx.prop(levels, "val04", text="Black", slider=True)
    bx.prop(levels, "val05", text="White", slider=True)


def drawlevels_vis_01(layout, b, m, w, count=70):
    # UI element. Imitate slider for Levels
    otp = bpy.context.scene.other_props
    row = layout.row(align=True)
    row.scale_y = 0.3

    for p in range(count):
        icon = "BLANK1"
        if p == b:
            icon = "DECORATE_ANIMATE"
        if p == m:
            icon = "KEYFRAME"
        if p == w:
            icon = "DECORATE_KEYFRAME"

        row.prop(otp, "emptyprop", icon_only=True, icon=icon, emboss=False)


def drawlevels_vis_02(layout, db, dw, count=70):
    # UI element. Imitate slider for Levels
    otp = bpy.context.scene.other_props

    row = layout.row(align=True)
    row.scale_y = 0.3
    for p in range(count):
        icon = "BLANK1"
        if p == db:
            icon = "MARKER"
        if p == dw:
            icon = "MARKER_HLT"
        row.prop(otp, "emptyprop", icon_only=True, icon=icon, emboss=False)


def draw_mapping_box(rowcol, resource):
    # UI element. Box with mapping properties
    rowcol.prop(resource, "expand_mapping", text="Mapping", icon="TEXTURE", emboss=False)
    box = rowcol.column()
    if resource.expand_mapping:

        bws = box.row(align=True)
        bws.label(text="Offset")
        bws = box.row(align=True)
        bws.prop(resource, "mapx", text="X")
        bws.prop(resource, "mapy", text="Y")
        bws = box.row(align=True)
        bws.label(text="Scale")
        bws = box.row(align=True)
        bws.prop(resource, "mapscalex", text="")
        bws.prop(resource, "mapscaley", text="")
        bws = box.row(align=True)
        bws.label(text="Rotate")
        bws.prop(resource, "maprot", text="")


class OpacityControlOperatorPOPUP(Operator):
    bl_idname = "paint.opacity_controller"
    bl_label = "Opacity"

    layer_index: IntProperty()

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self)

    def draw(self, context):
        layout = self.layout
        part = get_material_collection()

        layer = part.layers[self.layer_index]
        layout.prop(layer, "opacity", text="Layer Opacity", slider=True)


class LayerActionPopup(Operator):
    bl_idname = "paint.layer_action"
    bl_label = "Layer Action"
    bl_options = {"REGISTER"}
    layer_index: IntProperty()

    def draw(self, context):
        layout = self.layout
        part = get_material_collection()
        if not part:
            return

        if len(part.layers) - 1 < self.layer_index:
            print("Error in num layers")
            return

        layer = part.layers[self.layer_index]
        if layer:

            rsb = layout.row()
            rsb.label(text="Layer Action")
            rsb.label(icon="GRIP")
            colcol = layout.column()
            bx = colcol.box()
            rowvs = bx.row()
            rowvs.alignment = "LEFT"
            rowvs.enabled = not layer.lock
            op = rowvs.operator("paint.otheractions", text="Add Filter", icon="SHADERFX", emboss=False)
            op.layer_index = self.layer_index
            op.action = "ADDFILTER"
            rowvs = bx.row()
            rowvs.alignment = "LEFT"
            rowvs.enabled = not layer.lock
            op = rowvs.operator("paint.otheractions", text="Add Paint Layer", icon="BRUSH_DATA", emboss=False)
            op.layer_index = self.layer_index
            op.action = "ADDPAINT"
            rowvs = bx.row()
            rowvs.alignment = "LEFT"
            rowvs.enabled = not layer.lock
            op = rowvs.operator("paint.otheractions", text="Add Fill Layer", icon="IMAGE", emboss=False)
            op.layer_index = self.layer_index
            op.action = "ADDFILL"
            rvsbx = bx.row(align=True)
            rvsbx.alignment = "LEFT"
            rvsbx.enabled = not layer.lock
            op = rvsbx.operator("paint.otheractions", text="Add Mask", icon="CLIPUV_DEHLT", emboss=False)
            op.layer_index = self.layer_index
            op.action = "ADDMASK"

            op = rvsbx.operator("paint.otheractions", text="Remove Mask", icon="SNAP_FACE", emboss=False)
            op.layer_index = self.layer_index
            op.action = "REMOVEMASK"
            bx = colcol.box()
            rowvs = bx.row()
            rowvs.alignment = "LEFT"

            rowvs.prop(layer, "lock", text="Lock" if not layer.lock else "Unlock", icon="DECORATE_LOCKED", emboss=False)
            bx = colcol.box()
            rowvs = bx.row()
            rowvs.alignment = "LEFT"
            rowvs.enabled = not layer.lock
            op = rowvs.operator("paint.combine_with_layer_below", text="Combine with Layer Below", icon="MOD_UVPROJECT", emboss=False)
            op.layer_index = self.layer_index
            rowvs = bx.row()
            rowvs.alignment = "LEFT"
            rowvs.enabled = not layer.lock
            op = rowvs.operator("paint.resize_texture", text="Resize Layer", icon="MOD_EDGESPLIT", emboss=False)
            op.layer_index = self.layer_index
            rowvs = bx.row()
            rowvs.alignment = "LEFT"
            rowvs.enabled = not layer.lock
            op = rowvs.operator("paint.collapse_layer", text="Collapse Layer", icon="IMPORT", emboss=False)
            op.layer_index = self.layer_index
            row = colcol.box().row(align=True)
            row.label(icon=layer.sort_color, text="Color Tag")
            row.enabled = not layer.lock
            if not layer.layer_type == "FOLDER":
                for c in SORT_COLORS:
                    select_op = row.operator("paint.set_color", text="", icon=c[0], emboss=False)
                    select_op.color = c[0]
                    select_op.layer_index = self.layer_index
            else:
                for c in FOLDER_SORT_COLORS:
                    select_op = row.operator("paint.set_color", text="", icon=c[0], emboss=False)
                    select_op.color = c[0]
                    select_op.layer_index = self.layer_index

            bx = colcol.box()
            rowvs = bx.row()
            rowvs.alignment = "LEFT"
            rowvs.enabled = not layer.lock
            op = rowvs.operator("paint.otheractions", text="Duplicate Layer", icon="DUPLICATE", emboss=False)
            op.layer_index = self.layer_index
            op.action = "DUPL"
            if layer.resource.image:
                rowvs = bx.row()
                rowvs.alignment = "LEFT"
                rowvs.enabled = not layer.lock
                op = rowvs.operator("paint.isolate_image", text="Isolate current layer image", icon="IMAGE_REFERENCE", emboss=False)
                op.texture_name = layer.resource.image.name
                rowvs = bx.row()
                rowvs.alignment = "LEFT"
                rowvs.enabled = not layer.lock
                op = rowvs.operator("paint.image_info_popup", text="Edit Image Properties", icon="PROPERTIES", emboss=False)
                op.texture_name = layer.resource.image.name
            bx = colcol.box()
            rowvs = bx.row()
            rowvs.alignment = "LEFT"
            rowvs.enabled = not layer.lock
            op = rowvs.operator("paint.remove_layer", text="Remove layer", icon="TRASH", emboss=False)
            op.layer_index = self.layer_index

            resource = layer.resource
            cols = colcol.box().split(factor=0.5)
            box = cols.column()
            cols.enabled = not layer.lock
            if not resource.image:
                boxe = box.row()

                boxe.prop(resource, "default_color", text="")
                boxe.scale_y = 1.0
            if not resource.image:
                box = box.row(align=True)
            box.template_ID(resource, "image")
            if not resource.image:
                op = box.operator("paint.add_has_image", text="New Image", icon="IMAGE_REFERENCE", emboss=True)
                op.layer_index = layer.index

            if resource.image:
                box.template_ID_preview(resource, "image", rows=4, cols=6, hide_buttons=True)

            op = box.operator("paint.open_image_file", text="Open", icon="FILE_FOLDER", emboss=True)
            op.layer_index = self.layer_index

            if resource.image:
                draw_mapping_box(cols.column(), layer.resource)

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self)


class FilterSelectPopup(Operator):
    bl_idname = "paint.filter_select"
    bl_label = "Select Filter"
    bl_options = {"REGISTER"}
    layer_index: IntProperty()
    filter_index: IntProperty()

    def draw(self, context):
        layout = self.layout
        part = get_material_collection()
        layer = part.layers[self.layer_index]
        if layer:

            rsb = layout.row()
            rsb.label(text="Select Filter")
            rsb.label(icon="GRIP")
            colcol = layout.column()
            bx = colcol.box()
            for filterenum in FILTERS:
                if not filterenum:
                    bx = colcol.box()
                    continue
                rowvs = bx.row()
                rowvs.alignment = "LEFT"
                op = rowvs.operator("paint.setfilter", text=filterenum[1], icon=filterenum[3], emboss=False)
                op.layer_index = self.layer_index
                op.filter_index = self.filter_index
                op.action = filterenum[0]

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self)


class TypeSelectPopup(Operator):

    bl_idname = "paint.type_select"
    bl_label = "Map Type"
    bl_options = {"REGISTER"}
    layer_index: IntProperty()
    current: StringProperty()

    def draw(self, context):
        layout = self.layout
        part = get_material_collection()
        layer = part.layers[self.layer_index]
        if layer:
            rsb = layout.row()
            rsb.label(text="Texture type")
            rsb.label(icon="GRIP")
            colcol = layout.column(align=True)
            bx = colcol
            for type in getusedmaps():
                if not type:
                    bx = colcol.box()
                    continue
                rowvs = bx.row()
                rowvs.alignment = "LEFT"
                op = rowvs.operator("paint.settype", text=type[1], emboss=self.current == type[0], depress=self.current == type[0])
                op.layer_index = self.layer_index
                op.action = type[0]

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, width=150)


class ImageInfoPopup(Operator):
    bl_idname = "paint.image_info_popup"
    bl_label = "Image Info"
    bl_options = {"REGISTER"}
    texture_name: StringProperty()

    def draw(self, context):
        layout = self.layout
        image = bpy.data.images.get(self.texture_name)

        if image:
            op = layout.row().operator("paint.save_image", text="Save", icon="FILE_TICK")
            op.image_name = self.texture_name
            column = layout.column()
            column.enabled = not image.is_dirty
            column.prop(image.colorspace_settings, "name")
            column.prop(image, "alpha_mode")
            column.prop(image, "use_generated_float", text="Use 32 bit depth")

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


classes = [
    HAS_PT_LayersPanel,
    OpacityControlOperatorPOPUP,
    LayerActionPopup,
    FilterSelectPopup,
    TypeSelectPopup,
    ImageInfoPopup,
]


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
