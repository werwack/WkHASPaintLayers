import bpy
import re
import numpy as np
from contextlib import contextmanager
import mathutils
import uuid
from mathutils import Matrix
import re

from ..has_enum import *
from .utils import (
    get_material_collection,
    getlayergroupname,
    any_active_filter,
    create_socket,
    getmaterialgroupname,
    clear_nodes,
    getusedmaps,
    set_default,
    create_node,
    layer_filter,
    blendin,
    get_layers,
    getusedtypes,
    CheckForEmpty,
    fixorder,
    update_layer_index,
    get_node_by_name,
    clear_socket_links,
    typeexist,
    move_last_to_selected,
    shortid,
    SetupMtl,
    get_all_image_nodes_in_material,
    newlayername,
    get_selected_layer_index,
    SelectLayer,
    reassign_layer,
    get_next_set_name,
    newimagename,
    getgroupname,
    getusedtypesinlayers,
)


def create_image_node(node_group, img, resource=None, returnAllNodes=False, createTransformMappingNodes=False):
    """Create image node in shader editor and attach mapping assigning settings"""

    nodeXOffset = 200
    nodeXPos = -2000

    part = get_material_collection()
    links = node_group.links

    image_node = create_node(node_group, "ShaderNodeTexImage", -600, 0, "img", img)
    image_node.interpolation = part.texture_filtering

    attribute = create_node(node_group, "ShaderNodeUVMap", nodeXPos, 0, "", "")
    attribute.uv_map = part.uvs

    if createTransformMappingNodes:
        nodeXPos += nodeXOffset
        mapping_node_parent_offset = create_node(node_group, "ShaderNodeMapping", nodeXPos, 0, "", "")
        # mapping_node_parent_offset.description = "Offset in Parent CS. Must be -0.5, -0.5 by default"
        set_default(mapping_node_parent_offset, "Location", (-0.5, -0.5, 0.0))

        nodeXPos += nodeXOffset
        mapping_node_local_center_rotation = create_node(node_group, "ShaderNodeMapping", nodeXPos, 0, "", "")
        # mapping_node_local_center_rotation.description = "Rotation in Local Centered CS"

        nodeXPos += nodeXOffset
        mapping_node_local_scale = create_node(node_group, "ShaderNodeMapping", nodeXPos, 0, "", "")
        set_default(mapping_node_local_scale, "Location", (0.5, 0.5, 0.0))
        # mapping_node_local_scale.description = "Scale in Local Centered CS"

        # if resource:
        #     set_default(mapping_node_offset, "Location", (resource.mapx, resource.mapy, 0.0))
        #     set_default(mapping_node_offset, "Rotation", (0.0, 0.0, resource.maprot))
        #     set_default(mapping_node_offset, "Scale", (resource.mapscalex, resource.mapscaley, 1.0))
        #     resource.mapping_node.set_node_reference(mapping_node_offset)

        links.new(attribute.outputs[0], mapping_node_parent_offset.inputs[0])
        links.new(mapping_node_parent_offset.outputs[0], mapping_node_local_center_rotation.inputs[0])
        links.new(mapping_node_local_center_rotation.outputs[0], mapping_node_local_scale.inputs[0])
        links.new(mapping_node_local_scale.outputs[0], image_node.inputs[0])

    else:
        nodeXPos += nodeXOffset
        mapping_node_offset = create_node(node_group, "ShaderNodeMapping", nodeXPos, 0, "", "")

        if resource:
            set_default(mapping_node_offset, "Location", (resource.mapx, resource.mapy, 0.0))
            set_default(mapping_node_offset, "Rotation", (0.0, 0.0, resource.maprot))
            set_default(mapping_node_offset, "Scale", (resource.mapscalex, resource.mapscaley, 1.0))
            resource.mapping_node.set_node_reference(mapping_node_offset)

        links.new(attribute.outputs[0], mapping_node_offset.inputs[0])

        links.new(mapping_node_offset.outputs[0], image_node.inputs[0])

    if part.uvs:
        attribute = create_node(node_group, "ShaderNodeAttribute", -600, 0, "", "")
        attribute.attribute_name = part.uvs
        links.new(attribute.outputs[1], mapping_node_offset.inputs[0])

    if returnAllNodes:
        return (image_node, mapping_node_parent_offset, mapping_node_local_center_rotation, mapping_node_local_scale)

    return image_node


def create_layer_node(layer, pbr=False):
    # Paint layer node group
    part = get_material_collection()
    name = getlayergroupname(layer)
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes(node_group, layer.filters)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)
    pth = layer.blend_mode == "PASS"

    active_filters = any_active_filter(layer.filters)

    create_socket(node_group, "Color", "color", True)
    create_socket(node_group, "Alpha", "float", True)
    create_socket(node_group, "Color", "color", False)
    create_socket(node_group, "Alpha", "float", False)

    createNote(node_group)

    img = layer.resource.image
    links = node_group.links

    input_node = node_group.nodes.new(type="NodeGroupInput")
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type="NodeGroupOutput")
    output_node.location = (500, 0)

    lastconnection = None
    lastclipmaskconnection = None

    if img:
        image_node, mapping_node_parent_offset, mapping_node_local_center_rotation, mapping_node_local_scale = create_image_node(
            node_group, img, resource=layer.resource, returnAllNodes=True, createTransformMappingNodes=True
        )
        lastconnection = image_node.outputs[0]
        if layer.texture_type == "NORMAL" and layer.resource.image.colorspace_settings.name == "sRGB":
            gamma = create_node(node_group, "ShaderNodeGamma", -200, 0, "", "")
            set_default(gamma, 1, 0.454)
            lastconnection = gamma.outputs[0]
            links.new(image_node.outputs[0], gamma.inputs[0])
    math_node = create_node(node_group, "ShaderNodeMath", -200, -60, "op", "MULTIPLY")

    initialmask = None
    if layer.mask:
        initialmask = create_node(node_group, "ShaderNodeMath", -200, 0, "op", "MULTIPLY")
        initialmask.name = "InitialMask"
        initialmask.inputs[0].name = "MaskValue"
        set_default(initialmask, 0, 1.0 if layer.mask_value else 0.0)
        set_default(initialmask, 1, 1.0)
        # layer.mask_value.set_socket_reference(initialmask.inputs[1])
    # else:
    # layer.mask_value.set_socket_reference(math_node.inputs[0])

    set_default(math_node, 0, 1.0)
    set_default(math_node, 1, layer.opacity)
    math_node.inputs[1].name = "OpSock"
    layer.opacity_socket.set_socket_reference(math_node.inputs[1])

    #########
    # offsetX
    # mapping_node.inputs[1].name = "MappingSock"
    layer.offsetX_socket.set_socket_reference(mapping_node_parent_offset.inputs[1])
    layer.offsetY_socket.set_socket_reference(mapping_node_parent_offset.inputs[1])
    layer.rotateZ_socket.set_socket_reference(mapping_node_local_center_rotation.inputs[2])
    layer.scaleX_socket.set_socket_reference(mapping_node_local_scale.inputs[3])
    layer.scaleY_socket.set_socket_reference(mapping_node_local_scale.inputs[2])
    # layer.textureTile_socket.set_socket_reference(image_node.inputs[2])

    if layer.blend_mode == "COMBNRM":
        mix_node = create_node(node_group, "ShaderNodeGroup", -600, 0, "cus", ".HAS_BlendNormals")
    else:
        if not pth:
            mix_node = create_node(node_group, "ShaderNodeMixRGB", 0, 0, "mix", layer.blend_mode)
        else:
            mix_node = create_node(node_group, "ShaderNodeMixRGB", 0, 0, "mix", "MIX")

        mix_node.use_clamp = True

    mix_node.inputs[2].name = "ColSock"
    layer.resource.default_color_socket.set_socket_reference(mix_node.inputs["ColSock"])
    height_remap = None

    # if img:
    #     lastconnection = image_node.outputs[1]
    #     lastclipmaskconnection = image_node.outputs[0]

    if not img:
        set_default(mix_node, "ColSock", layer.resource.default_color)

    if layer.texture_type == "HEIGHT" and img and layer.blend_mode == "ADD":
        height_remap = create_node(node_group, "ShaderNodeMapRange", 0, 0, "", "")
        height_remap.clamp = False
        set_default(height_remap, 3, -0.5)
        set_default(height_remap, 4, 0.5)

    if pth:
        lastconnection = input_node.outputs["Color"]
        lastclipmaskconnection = input_node.outputs["Alpha"]
    else:
        if img:
            if height_remap:
                links.new(image_node.outputs[0], height_remap.inputs[0])
                lastconnection = height_remap.outputs[0]
            else:
                if not lastconnection:
                    lastconnection = image_node.outputs[0]
            lastclipmaskconnection = image_node.outputs[1]
    if layer.mask:
        if initialmask and lastclipmaskconnection:
            links.new(lastclipmaskconnection, initialmask.inputs[1])
        if initialmask:
            lastclipmaskconnection = initialmask.outputs[0]
    if active_filters:
        filnode = create_node(node_group, "ShaderNodeGroup", -200, -200, "cus", layer_filter(layer).name)
        set_default(filnode, "Color", layer.resource.default_color)
        set_default(filnode, "Alpha", 1.0)
        if lastconnection:
            links.new(lastconnection, filnode.inputs["Color"])
        if lastclipmaskconnection:
            links.new(lastclipmaskconnection, filnode.inputs["Alpha"])
        lastconnection = filnode.outputs["Color"]
        lastclipmaskconnection = filnode.outputs["Alpha"]
        layer.resource.default_color_socket.set_socket_reference(filnode.inputs["Color"])

    if not lastclipmaskconnection:
        if img:
            lastclipmaskconnection = image_node.outputs[1]

    links.new(input_node.outputs["Color"], mix_node.inputs[1])
    links.new(mix_node.outputs[0], output_node.inputs["Color"])
    if lastconnection:
        links.new(lastconnection, mix_node.inputs[2])
    if lastclipmaskconnection:

        links.new(lastclipmaskconnection, math_node.inputs[0])

    alphablend = create_node(node_group, "ShaderNodeMixRGB", 0, 0, "mix", "SCREEN")
    set_default(alphablend, 0, 1.0)
    if lastconnection:
        links.new(lastconnection, mix_node.inputs[2])

    links.new(math_node.outputs[0], mix_node.inputs["Fac"])

    links.new(math_node.outputs[0], alphablend.inputs[1])
    links.new(input_node.outputs["Alpha"], alphablend.inputs[2])

    links.new(alphablend.outputs[0], output_node.inputs["Alpha"])

    return node_group


def createlayersgroup(tex_type, name):
    # Group created for each used Channel
    part = get_material_collection()
    layers = get_layers(part.base_layers)
    group_name = getgroupname(tex_type[0], name)
    if group_name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[group_name]
        for nodei in node_group.nodes:
            node_group.nodes.remove(nodei)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=group_name)

    createNote(node_group)
    group_output = node_group.nodes.new("NodeGroupOutput")
    group_output.location = (500, 0)
    group_input = node_group.nodes.new("NodeGroupInput")
    group_input.location = (-500, 0)

    create_socket(node_group, "Color", "color", True)
    create_socket(node_group, "Alpha", "float", True)
    create_socket(node_group, "Color", "color", False)
    create_socket(node_group, "Alpha", "float", False)

    count = -1

    links = node_group.links
    for link in links:
        links.remove(link)

    prev_node = None

    for index, layer in enumerate(layers):
        fldrlrs = getusedtypesinlayers(get_layers(layer.sub_layers))

        if layer.layer_type == "FOLDER" or layer.layer_type == "PBR":
            if layer.use_layer and tex_type[0] in fldrlrs:
                count = count + 1

                l_group = get_folder_nodegroup(layer, pbr=layer.layer_type == "PBR")

                layer_node = create_node(node_group, "ShaderNodeGroup", -200, count * -200, "cus", l_group.name)

                if prev_node:
                    links.new(prev_node.outputs["Color"], layer_node.inputs["Color"])
                    links.new(prev_node.outputs["Alpha"], layer_node.inputs["Alpha"])
                else:
                    links.new(group_input.outputs["Color"], layer_node.inputs["Color"])
                    links.new(group_input.outputs["Alpha"], layer_node.inputs["Alpha"])

                set_default(layer_node, "Type", fldrlrs.index(tex_type[0]))
                prev_node = layer_node

        else:
            if layer.use_layer and tex_type[0] == layer.texture_type:

                count = count + 1

                l_group = create_layer_node(layer)
                layer_node = create_node(node_group, "ShaderNodeGroup", -200 + count * 60, count * 200, "cus", l_group.name)

                if prev_node:
                    links.new(prev_node.outputs["Color"], layer_node.inputs["Color"])
                    links.new(prev_node.outputs["Alpha"], layer_node.inputs["Alpha"])
                else:
                    links.new(group_input.outputs["Color"], layer_node.inputs["Color"])
                    links.new(group_input.outputs["Alpha"], layer_node.inputs["Alpha"])
                prev_node = layer_node

    if prev_node:
        links.new(prev_node.outputs["Color"], group_output.inputs["Color"])
        links.new(prev_node.outputs["Alpha"], group_output.inputs["Alpha"])
        if part.InvertG:
            if tex_type[0] == "NORMAL":
                invnrmnode = create_node(node_group, "ShaderNodeGroup", -200, count * -200, "cus", InvertNormalNode().name)
                if invnrmnode:
                    links.new(prev_node.outputs["Color"], invnrmnode.inputs["Normal"])
                    links.new(invnrmnode.outputs["Normal"], group_output.inputs["Color"])
        if part.colorfix and tex_type[0] == "DIFFUSE" and part.diffusealpha and not part.shader_type == "UNLIT":
            Colfix = create_node(node_group, "ShaderNodeMixRGB", -200, 0, "mix", "DIVIDE")
            set_default(Colfix, 0, 1.0)
            links.new(prev_node.outputs["Color"], Colfix.inputs[1])
            links.new(prev_node.outputs["Alpha"], Colfix.inputs[2])
            links.new(Colfix.outputs[0], group_output.inputs["Color"])
    else:
        links.new(group_input.outputs["Color"], group_output.inputs["Color"])
        links.new(group_input.outputs["Alpha"], group_output.inputs["Alpha"])

    return node_group


def creatematnode():
    # Base node group that creates shader setup from all layers assigned
    part = get_material_collection()
    name = getmaterialgroupname(part)
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        node_group.nodes.clear()
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    links = node_group.links

    usedtypes = getusedtypes()
    createNote(node_group)
    input_node = node_group.nodes.new(type="NodeGroupInput")
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type="NodeGroupOutput")
    output_node.location = (500, 0)
    hsocketout = None
    nrmsocketout = None
    for layer in part.layers:
        if layer.layer_type == "FOLDER":
            create_folder_nodegroup(layer)
        elif layer.layer_type == "PBR":
            create_pbr_nodegroup(layer)

    for indexgr, tex_type in enumerate(TEXTURE_TYPE):

        lgroup = createlayersgroup(tex_type, name)

        group_node = node_group.nodes.new("ShaderNodeGroup")
        group_node.node_tree = lgroup
        group_node.location = (0, -200 * indexgr)
        type = tex_type[0]
        nm = tex_type[1]
        anm = f"{nm}Alpha"

        create_socket(node_group, f"{nm}", "color", True)
        create_socket(node_group, f"{anm}", "float", True)
        create_socket(node_group, f"{nm}", "color", False)
        create_socket(node_group, f"{anm}", "float", False)

        if not group_node.outputs or not group_node.inputs:
            continue
        links.new(group_node.outputs["Color"], output_node.inputs[nm])
        links.new(group_node.outputs["Alpha"], output_node.inputs[anm])
        links.new(input_node.outputs[nm], group_node.inputs["Color"])
        links.new(input_node.outputs[anm], group_node.inputs["Alpha"])

        if type == "ROUGHNESS":
            set_default(node_group, "Roughness", (0.9, 0.9, 0.9, 1.0))
        if type == "HEIGHT":
            hsocketout = group_node.outputs["Color"]
            set_default(node_group, "Height", (0.5, 0.5, 0.5, 1.0))
        if type == "NORMAL":
            nrmsocketout = group_node.outputs["Color"]
            set_default(node_group, "Normal", (0.5, 0.5, 1.0, 1.0))
        if type == "DIFFUSE":
            set_default(node_group, "Diffuse", (0.0, 0.0, 0.0, 1.0))
        if type == "ALPHA":
            set_default(node_group, "Alpha", (1.0, 1.0, 1.0, 1.0))
        if not type == "DIFFUSE":
            set_default(node_group, anm, 1.0)

    create_socket(node_group, "RawNormal", "Color", False)
    if nrmsocketout:
        links.new(nrmsocketout, output_node.inputs["RawNormal"])

    for type in getusedmaps():
        nm = type[1]
        anm = f"{nm}Alpha"
        if nm in output_node.inputs:
            if not input_node.outputs[nm].is_linked:
                links.new(input_node.outputs[nm], output_node.inputs[nm])
                links.new(input_node.outputs[anm], output_node.inputs[anm])

    if nrmsocketout or hsocketout:
        bump = node_group.nodes.new(type="ShaderNodeBump")
        set_default(bump, 0, part.height_intensity)
        bump.location = (500, -700)
        nrmap = node_group.nodes.new(type="ShaderNodeNormalMap")
        nrmap.location = (200, -500)
        if nrmsocketout:
            links.new(nrmsocketout, nrmap.inputs["Color"])
            links.new(nrmap.outputs[0], bump.inputs["Normal"])
        if hsocketout:
            links.new(hsocketout, bump.inputs["Height"])

        links.new(bump.outputs[0], output_node.inputs["Normal"])

    return node_group


def createNote(node_group):
    note = node_group.nodes.new("NodeFrame")
    note.location = (-200, 400)
    note.label = "This node group is created and used by HAS Paint Layers"
    note.width = 600


def create_folder_nodegroup(folder_layer, pbr=False):
    # Folder layer node group that contains other layers.
    part = get_material_collection()
    name = f"{getlayergroupname(folder_layer)}"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes(node_group, folder_layer.filters)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_socket(node_group, "Color", "color", True)
    create_socket(node_group, "Color", "color", False)
    create_socket(node_group, "Alpha", "float", True)
    create_socket(node_group, "Alpha", "float", False)
    create_socket(node_group, "Type", "float", True)

    createNote(node_group)
    group_input = node_group.nodes.new(type="NodeGroupInput")
    group_input.location = (-500, 0)
    group_output = node_group.nodes.new(type="NodeGroupOutput")
    group_output.location = (500, 0)

    links = node_group.links
    count = -1

    lastconnection = group_input.outputs["Color"]

    prevnodes = []
    alsockets = []
    lrs = get_layers(folder_layer.sub_layers)

    for type in getusedtypes():
        prev_node = None

        for index, layer in enumerate(lrs):

            if layer.use_layer and type == layer.texture_type:

                count = count + 1

                l_group = create_layer_node(layer)
                layer_node = create_node(node_group, "ShaderNodeGroup", -200, count * 200, "cus", l_group.name)

                if prev_node:
                    links.new(prev_node.outputs["Color"], layer_node.inputs["Color"])
                    links.new(prev_node.outputs["Alpha"], layer_node.inputs["Alpha"])
                if "Type" in layer_node.inputs:
                    links.new(group_input.outputs["Type"], layer_node.inputs["Type"])
                prev_node = layer_node

        if prev_node:
            prevnodes.append(prev_node)
    if prev_node:
        links.new(prev_node.outputs["Color"], group_output.inputs["Color"])
        links.new(prev_node.outputs["Alpha"], group_output.inputs["Alpha"])
    else:
        links.new(group_input.outputs["Color"], group_output.inputs["Color"])
        links.new(group_input.outputs["Alpha"], group_output.inputs["Alpha"])
    prsef = None
    count = -1
    type_switch_node = None
    lastcol = None
    lastcolal = None
    for pren in prevnodes:
        count = count + 1
        type_switch_node = create_node(node_group, "ShaderNodeGroup", -200, count * -200, "cus", type_switch().name)
        links.new(group_input.outputs["Type"], type_switch_node.inputs["Type"])
        set_default(type_switch_node, "Compare", float(count))
        links.new(pren.outputs["Color"], type_switch_node.inputs["Color"])
        links.new(pren.outputs["Alpha"], type_switch_node.inputs["Alpha"])
        if prsef:
            links.new(prsef.outputs["Color"], type_switch_node.inputs["PrevColor"])
            links.new(prsef.outputs["Alpha"], type_switch_node.inputs["PrevAlpha"])
        prsef = type_switch_node
    if type_switch_node:

        lastcol = type_switch_node.outputs["Color"]
        lastcolal = type_switch_node.outputs["Alpha"]
        folder_layerfinm = layer_filter(folder_layer, multi=True).name
        if folder_layerfinm:
            folder_layerfilnodegroup = create_node(node_group, "ShaderNodeGroup", -200, -200, "cus", folder_layerfinm)
            links.new(lastcol, folder_layerfilnodegroup.inputs["Color"])
            links.new(lastcolal, folder_layerfilnodegroup.inputs["Alpha"])
            links.new(group_input.outputs["Type"], folder_layerfilnodegroup.inputs["Type"])
            lastcol = folder_layerfilnodegroup.outputs["Color"]
            lastcolal = folder_layerfilnodegroup.outputs["Alpha"]

    mix = create_node(node_group, "ShaderNodeMixRGB", -200, -200, "mix", folder_layer.blend_mode)
    blenda = create_node(node_group, "ShaderNodeMixRGB", -200, -200, "mix", "SCREEN")
    set_default(blenda, "Fac", 1.0)
    set_default(mix, "Fac", folder_layer.opacity)
    folder_layer.opacity_socket.set_socket_reference(mix.inputs["Fac"])
    if lastcol:
        links.new(group_input.outputs["Color"], mix.inputs[1])
        links.new(lastcol, mix.inputs[2])
        links.new(group_input.outputs["Alpha"], blenda.inputs[1])
        links.new(lastcolal, blenda.inputs[2])

        links.new(lastcolal, mix.inputs[0])

        lastcol = mix.outputs[0]
        lastcolal = blenda.outputs[0]
        links.new(lastcol, group_output.inputs["Color"])
        links.new(lastcolal, group_output.inputs["Alpha"])

    return node_group


def create_pbr_nodegroup(folder_layer):
    # PBR layer Node group that contains all used channels with Typeswitch.
    part = get_material_collection()
    name = f"{getlayergroupname(folder_layer)}"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes(node_group, folder_layer.filters)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_socket(node_group, "Color", "color", True)
    create_socket(node_group, "Color", "color", False)
    create_socket(node_group, "Alpha", "float", True)
    create_socket(node_group, "Alpha", "float", False)
    create_socket(node_group, "Type", "float", True)

    createNote(node_group)
    group_input = node_group.nodes.new(type="NodeGroupInput")
    group_input.location = (-500, 0)
    group_output = node_group.nodes.new(type="NodeGroupOutput")
    group_output.location = (500, 0)

    links = node_group.links

    lastconnection = group_input.outputs["Color"]

    count = -1
    sockets = []
    alsockets = []
    lrs = get_layers(folder_layer.sub_layers)
    sourceimg = create_image_node(node_group, folder_layer.resource.image, resource=folder_layer.resource)
    mpng = get_node_by_name(node_group, "Mapping")
    srinm = sourceimg.outputs[1]
    folder_layerfinm = layer_filter(folder_layer, multi=True).name
    if folder_layerfinm:
        folder_layerfilnodegroup = create_node(node_group, "ShaderNodeGroup", -200, count * -200, "cus", folder_layerfinm)
        links.new(group_input.outputs["Type"], folder_layerfilnodegroup.inputs["Type"])
        links.new(sourceimg.outputs[1], folder_layerfilnodegroup.inputs["Alpha"])
        srinm = folder_layerfilnodegroup.outputs["Alpha"]
    for type in getusedtypes():
        prev_node = None

        for index, layer in enumerate(lrs):
            filnodegroup = None
            if layer.use_layer and type == layer.texture_type:
                layer_node = None
                count = count + 1

                if layer.filters:
                    finm = layer_filter(layer, multi=True).name
                    if finm:
                        filnodegroup = create_node(node_group, "ShaderNodeGroup", -200, count * -200, "cus", finm)
                image = None
                mixrgb = create_node(node_group, "ShaderNodeMixRGB", -200, count * -200, "mix", layer.blend_mode)
                opacitynode = create_node(node_group, "ShaderNodeMath", -200, count * -200, "op", "MULTIPLY")
                opacitynode.inputs[1].name = "OpSock"
                if layer.resource.image:
                    image = create_image_node(node_group, layer.resource.image, resource=layer.resource)

                    links.new(image.outputs[0], mixrgb.inputs[2])

                set_default(mixrgb, 2, layer.resource.default_color)
                set_default(mixrgb, 0, 1.0)
                set_default(opacitynode, 1, layer.opacity)

                layer.resource.default_color_socket.set_socket_reference(mixrgb.inputs[2])
                layer.opacity_socket.set_socket_reference(opacitynode.inputs[1])

                layer_node = mixrgb

                if filnodegroup:
                    if image:
                        links.new(image.outputs["Color"], filnodegroup.inputs["Color"])
                    else:
                        set_default(filnodegroup, "Color", layer.resource.default_color)
                        set_default(filnodegroup, "Alpha", 1.0)
                        layer.resource.default_color_socket.set_socket_reference(filnodegroup.inputs["Color"])
                    links.new(filnodegroup.outputs["Color"], mixrgb.inputs[2])

                if layer_node:
                    links.new(prev_node.outputs["Color"] if prev_node else group_input.outputs["Color"], layer_node.inputs[1])
                    links.new(srinm if srinm else group_input.outputs["Alpha"], opacitynode.inputs[0])
                    links.new(opacitynode.outputs[0], mixrgb.inputs[0])
                    prev_node = layer_node
        if prev_node:
            sockets.append(prev_node.outputs["Color"])
    if prev_node:
        links.new(prev_node.outputs["Color"], group_output.inputs["Color"])
    else:
        links.new(group_input.outputs["Color"], group_output.inputs["Color"])

    lastcol = blendin(node_group, sockets, group_input.outputs["Type"])
    lastcolal = blendin(node_group, alsockets, group_input.outputs["Type"])
    if folder_layerfinm:
        lastcolal = folder_layerfilnodegroup.outputs["Alpha"]
        colfilt = create_node(node_group, "ShaderNodeGroup", -200, count * -200, "cus", folder_layerfinm)
        links.new(group_input.outputs["Type"], colfilt.inputs["Type"])
    if lastcol:
        if colfilt:
            links.new(lastcol, colfilt.inputs["Color"])
            lastcol = colfilt.outputs["Color"]
        links.new(lastcol, group_output.inputs["Color"])
        links.new(lastcolal, group_output.inputs["Alpha"])

    alphablend = create_node(node_group, "ShaderNodeMixRGB", 0, 0, "mix", "SCREEN")
    set_default(alphablend, 0, 1.0)

    links.new(lastcolal, alphablend.inputs[2])
    links.new(group_input.outputs["Alpha"], alphablend.inputs[1])
    links.new(alphablend.outputs[0], group_output.inputs["Alpha"])
    return node_group


def create_normal_blend_group():
    # Node group for Normal blending
    name = ".HAS_BlendNormals"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]

        node_group.nodes.clear()
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_socket(node_group, "Fac", "float", True)
    create_socket(node_group, "Color1", "color", True)
    create_socket(node_group, "Color2", "color", True)

    create_socket(node_group, "Color", "color", False)

    createNote(node_group)
    input_node = node_group.nodes.new(type="NodeGroupInput")
    output_node = node_group.nodes.new(type="NodeGroupOutput")
    input_node.location = (-500, 0)
    output_node.location = (500, 0)
    math_nodeA = node_group.nodes.new("ShaderNodeVectorMath")
    math_nodeA.operation = "ADD"
    math_nodeA.location = (0, 0)
    math_nodeM = node_group.nodes.new("ShaderNodeVectorMath")
    math_nodeM.operation = "MULTIPLY"
    math_nodeM.location = (-300, 0)
    math_nodeN = node_group.nodes.new("ShaderNodeVectorMath")
    math_nodeN.operation = "NORMALIZE"
    math_nodeN.location = (300, 0)

    node_group.links.new(input_node.outputs["Color1"], math_nodeA.inputs[0])
    node_group.links.new(input_node.outputs["Color2"], math_nodeM.inputs[0])
    node_group.links.new(math_nodeM.outputs[0], math_nodeA.inputs[1])

    node_group.links.new(input_node.outputs["Fac"], math_nodeM.inputs[1])
    node_group.links.new(math_nodeA.outputs[0], math_nodeN.inputs[0])
    node_group.links.new(math_nodeN.outputs[0], output_node.inputs[0])

    return node_group


def UpdateShader():
    # Update whole shader. Validating layers, filters, and reconnecting everything to match user setup
    CheckForEmpty()
    fixorder()
    update_layer_index()
    create_normal_blend_group()
    matnode = creatematnode()

    bpy.context.scene.other_props.layercombineactive = False
    part = get_material_collection()

    if part.shader_type == "Custom":
        return
    material = bpy.context.active_object.active_material

    if material is None:
        return
    mtl_n = material.name

    tree, shader_node, output_node = SetupMtl(material, part)
    material.blend_method = part.opacity_mode
    tree_links = material.node_tree.links
    group_node = get_node_by_name(tree, "HAS_Material_OO")

    if not group_node:
        group_node = tree.nodes.new("ShaderNodeGroup")
        group_node.location = shader_node.location - mathutils.Vector((300, 0))
        group_node.node_tree = matnode
        group_node.name = "HAS_Material_OO"
        group_node.label = "HAS_Material"
    part.node = group_node.name

    for input in group_node.inputs:
        input.hide = not input.hide
    for output in group_node.outputs:
        output.hide = not output.hide
    clear_socket_links(shader_node, "Alpha")
    if part.shader_type == "PRINCIPLED":
        if bpy.context.scene.other_props.preview_mode == "COMBINED":
            for type in getusedmaps():
                nm = type[1]
                if nm:
                    if nm == "Diffuse":
                        tree_links.new(group_node.outputs[nm], shader_node.inputs["Base Color"])

                        if part.diffusealpha:
                            tree_links.new(group_node.outputs["DiffuseAlpha"], shader_node.inputs["Alpha"])
                        elif typeexist("ALPHA"):
                            tree_links.new(group_node.outputs["Alpha"], shader_node.inputs["Alpha"])
                    elif nm == "Height":
                        tree_links.new(group_node.outputs["Normal"], shader_node.inputs["Normal"])
                    else:
                        if nm in shader_node.inputs:
                            tree_links.new(group_node.outputs[nm], shader_node.inputs[nm])
        else:
            for type in getusedmaps():
                if bpy.context.scene.other_props.preview_mode == type[0]:
                    material.blend_method = "OPAQUE"
                    tree_links.new(group_node.outputs[type[1]], output_node.inputs[0])
                if bpy.context.scene.other_props.preview_mode == "NORMAL":
                    tree_links.new(group_node.outputs["RawNormal"], output_node.inputs[0])

    elif part.shader_type == "UNLIT":
        tree_links.new(group_node.outputs["Diffuse"], shader_node.inputs["Color"])
        if part.diffusealpha:
            tree_links.new(group_node.outputs["DiffuseAlpha"], shader_node.inputs["Alpha"])
        elif typeexist("ALPHA"):
            tree_links.new(group_node.outputs["Alpha"], shader_node.inputs["Alpha"])


def setup_material(active_object):
    if active_object:
        if active_object.active_material:
            mat = active_object.active_material
            mat.use_nodes = True
        else:
            bpy.ops.object.mode_set(mode="OBJECT")
            mat = bpy.data.materials.new(name=re.sub(r"[^A-Za-z0-9]", "", f"has{active_object.name}"))

            if active_object.material_slots:
                active_material_index = active_object.active_material_index
                active_material_slot = active_object.material_slots[active_material_index]
                if active_material_slot.material is None:
                    active_material_slot.material = mat
                else:
                    active_object.data.materials.append(mat)
            else:
                active_object.data.materials.append(mat)
            mat.use_nodes = True

        part = bpy.context.scene.material_props.add()
        part.material = mat
        part.name = get_next_set_name()
        part.baking_props.high_poly_obj.add()
        part.baking_props.low_poly_obj.add()
    obj = active_object
    if not obj:
        return

    if not obj.material_slots:
        return

    material = obj.active_material
    if not material:
        return

    image_nodes = get_all_image_nodes_in_material(material)
    if image_nodes:
        part = get_material_collection()

        for node in image_nodes:
            layer_item = part.layers.add()
            layer_item.suppress_update = True
            layer_item.resource.suppress_update = True

            layer_item.resource.image = node.image

            layer_item.layer_name = newlayername()
            layer_item.id = shortid()
            part.base_layers.add().id = layer_item.id

            layer_item.suppress_update = False
            layer_item.resource.suppress_update = False

        UpdateShader()


def new_layer(fill=False):
    part = get_material_collection()
    if not fill:
        new_image = bpy.data.images.new(
            name=newimagename(newlayername()),
            width=part.texture_sizeX,
            height=part.texture_sizeY,
            alpha=True,
            float_buffer=False,
            tiled=False,
        )
        new_image.generated_type = "BLANK"
        new_image.generated_color = (0.0, 0.0, 0.0, 0.0)
        new_image.alpha_mode = "CHANNEL_PACKED"
        new_image.colorspace_settings.name = "sRGB"
    else:
        new_image = None
    if not part:
        return
    layer_item = part.layers.add()
    layer_item.suppress_update = True
    layer_item.resource.suppress_update = True
    if not fill:
        layer_item.resource.image = new_image
    layer_item.layer_name = newlayername()
    layer_item.id = shortid()

    selectedisattached = part.layers[get_selected_layer_index()].attachedto

    part.base_layers.add().id = layer_item.id
    if selectedisattached:
        reassign_layer(
            part.base_layers, get_layer_by_id(selectedisattached).sub_layers, layer_item.id, parent=get_layer_by_id(selectedisattached)
        )
    else:
        move_last_to_selected(part.base_layers)

    if fill:
        layer_item.layer_type = "FILL"
    layer_item.suppress_update = False
    layer_item.resource.suppress_update = False
    SelectLayer(layer_item.id)

    UpdateShader()


def new_layer_from_image(new_image, layer_name=""):

    part = get_material_collection()
    if not part:
        return None
    if not layer_name:
        layer_name = newlayername()
    layer_item = part.layers.add()
    layer_item.suppress_update = True
    layer_item.resource.suppress_update = True
    layer_item.resource.image = new_image
    layer_item.layer_name = layer_name
    layer_item.id = shortid()

    part.base_layers.add().id = layer_item.id

    layer_item.suppress_update = False
    layer_item.resource.suppress_update = False
    return layer_item


def new_pbr_layer():
    part = get_material_collection()
    if not part:
        return
    layer_name = newlayername(pref="PBR")
    image_name = newimagename(layer_name)

    xs = part.texture_sizeX
    ys = part.texture_sizeY

    new_image = bpy.data.images.new(name=image_name, width=xs, height=ys, alpha=True, float_buffer=False, tiled=False)
    new_image.generated_type = "BLANK"
    new_image.generated_color = (0.0, 0.0, 0.0, 0.0)

    new_image.alpha_mode = "CHANNEL_PACKED"
    new_image.colorspace_settings.name = "sRGB"

    if not part:
        return
    base_layer_item = part.layers.add()
    base_layer_item.suppress_update = True
    base_layer_item.resource.suppress_update = True
    base_layer_item.resource.image = new_image
    base_layer_item.layer_name = layer_name
    base_layer_item.layer_type = "PBR"
    base_layer_item.id = shortid()
    part.base_layers.add().id = base_layer_item.id
    base_layer_item.suppress_update = False
    base_layer_item.resource.suppress_update = False
    defcolor = {
        "DIFFUSE": ((0.5, 0.5, 0.5, 1.0)),
        "ROUGHNESS": ((0.8, 0.8, 0.8, 1.0)),
        "METALLIC": ((0.0, 0.0, 0.0, 1.0)),
        "NORMAL": ((0.5, 0.5, 1.0, 1.0)),
        "HEIGHT": ((0.5, 0.5, 0.5, 1.0)),
        "ALPHA": ((1.0, 1.0, 1.0, 1.0)),
        "EMISSION": ((0.0, 0.0, 0.0, 1.0)),
        "AO": ((1.0, 1.0, 1.0, 1.0)),
        "CUSTOM": ((0.0, 0.0, 0.0, 1.0)),
    }
    for type in getusedmaps():
        layer_item = part.layers.add()
        layer_item.suppress_update = True
        layer_item.resource.suppress_update = True
        if type[0] == "DIFFUSE":
            layer_item.resource.image = new_image

        layer_item.resource.default_color = defcolor.get(type[0], ((0.0, 0.0, 0.0, 1.0)))
        layer_item.resource.default_value = defcolor.get(type[0], ((0.0, 0.0, 0.0, 1.0)))[0]
        layer_item.texture_type = type[0]
        layer_item.id = shortid()
        base_layer_item.sub_layers.add().id = layer_item.id
        layer_item.suppress_update = False
        layer_item.resource.suppress_update = False

    selectedisattached = part.layers[get_selected_layer_index()].attachedto

    if selectedisattached:
        reassign_layer(
            part.base_layers, get_layer_by_id(selectedisattached).sub_layers, base_layer_item.id, parent=get_layer_by_id(selectedisattached)
        )
    else:
        move_last_to_selected(part.base_layers)
    SelectLayer(base_layer_item.id)

    UpdateShader()


def new_folder_layer():
    part = get_material_collection()
    if not part:
        return
    layer_item = part.layers.add()
    layer_item.suppress_update = True
    layer_item.layer_name = newlayername(pref="Folder")
    layer_item.layer_type = "FOLDER"
    layer_item.id = shortid()
    layer_item.sort_color = "OUTLINER_COLLECTION"
    part.base_layers.add().id = layer_item.id

    layer_item.suppress_update = False
    move_last_to_selected(part.base_layers)

    UpdateShader()


def isolate_image(texture_name):
    image = bpy.context.scene.other_props.preview_image

    if image and texture_name == image.name:
        bpy.context.scene.other_props.preview_image = None
        UpdateShader()
        return True
    else:
        image = bpy.data.images.get(texture_name, None)
        if image:
            bpy.context.scene.other_props.preview_image = image
            part = get_material_collection()
            material = bpy.context.active_object.active_material
            if not material:
                return
            tree = material.node_tree

            if material is None:
                return

            for node in tree.nodes:
                if node.type == "OUTPUT_MATERIAL":
                    output_node = node
                else:
                    tree.nodes.remove(node)
            if "output_node" not in locals():
                output_node = tree.nodes.new("ShaderNodeOutputMaterial")
                output_node.location = (600, 0)
            mtl_n = material.name

            image_node = create_image_node(tree, image)

            tree.links.new(image_node.outputs[0], output_node.inputs[0])
            return True
        else:
            return False
