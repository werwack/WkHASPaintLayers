import bpy
from bpy.utils import register_class, unregister_class
import os
from bpy.props import StringProperty, IntProperty, BoolProperty, FloatProperty
from bpy.types import Operator
import zipfile
from xml.etree.ElementTree import Element, SubElement, ElementTree
from .utils import *
from .has_enum import *

blend_mode_map = {
    'MIX': 'svg:mix',
    'PASS': 'svg:src-over',
    'ADD': 'svg:plus',
    'MULTIPLY': 'svg:multiply',
    'SUBTRACT': 'svg:subtract',
    'SCREEN': 'svg:screen',
    'DIVIDE': 'svg:divide',
    'DIFFERENCE': 'svg:difference',
    'DARKEN': 'svg:darken',
    'LIGHTEN': 'svg:lighten',
    'OVERLAY': 'svg:overlay',
    'DODGE': 'svg:dodge',
    'BURN': 'svg:burn',  
    'HUE': 'svg:hue',  
    'SATURATION': 'svg:saturation',  
    'VALUE': 'svg:value',  
    'COLOR': 'svg:color',  
    'SOFT_LIGHT': 'svg:soft-light',  
    'LINEAR_LIGHT': 'svg:linear-light',  
    'COMBNRM': 'svg:normal',  
}

class AddBakeMap(Operator):
    bl_idname = "paint.add_bake_map"
    bl_label = "Add Bake map"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        part = get_material_collection()
        baking_props = part.baking_props
        part.bake_maps.add()

        return {'FINISHED'}

class RemoveBakeMap(Operator):
    bl_idname = "paint.remove_bake_map"
    bl_label = "Remove Bake map"
    bl_options = {'REGISTER', 'UNDO'}
    index: IntProperty()

    def execute(self, context):
        part = get_material_collection()
        baking_props = part.baking_props
        part.bake_maps.remove(self.index)

        return {'FINISHED'}

class ExportTextures(Operator):
    bl_idname = "paint.export_textures"
    bl_label = "Export Textures"

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(
        default="*.png;*.jpg;*.jpeg;*.tiff;*.bmp;*.exr;*.hdr",
        options={'HIDDEN'}
    )

    def execute(self, context):
        part = get_material_collection()
        if not part:
            return {'FINISHED'}
        elif not part.layers:
            return {'FINISHED'}
        directory = os.path.dirname(self.filepath)
        user_filename = os.path.basename(self.filepath)
        otps = context.scene.other_props
        otps.save_path = directory
        otps.currentprefix = user_filename

        basescene = bpy.context.window.scene
        usedtypes = getusedtypes()

        layers = get_layers(part.base_layers)

        mtlname = getmaterialgroupname(part)
        obj_name = bpy.context.active_object.name
        file_name = os.path.basename(bpy.data.filepath) if bpy.data.filepath else "untitled"
        set_name = part.name
        bake_scene, material, plane, output_node, colorfix, alphasocket, camera = setup_bake_scene(basescene)
        if part.uvs:
            old_uv = plane.data.uv_layers[0]
            new_uv = plane.data.uv_layers.new(name=part.uvs)

        tree = material.node_tree
        if mtlname in bpy.data.node_groups:
            node_group = bpy.data.node_groups[mtlname]
        has_mtl = tree.nodes.new('ShaderNodeGroup')
        has_mtl.node_tree = node_group
        props = otps.exportprops
        if not otps.exportprops:

            pr = otps.exportprops.add()
            pr.type = 'RGB'
            pr.RGB = 'DIFFUSE'
            pr.save_name = '(mtl)_Color'
        if otps.exportprops:
            for textype in otps.exportprops:
                if textype.A:
                    alpha_name = gettexturelabel(textype.A)
                clear_socket_links(colorfix, 0)
                clear_socket_links(colorfix, 1)
                clear_socket_links(colorfix, 2)
                clear_socket_links(alphasocket.node, 0)
                alphafrom = None
                alphabake = False
                set_default(colorfix, 2, (1.0,1.0,1.0,1.0))
                alphasocket.default_value = 1.0
                if textype.type == "RGB":
                    type_name = gettexturelabel(textype.RGB)

                    tree.links.new(has_mtl.outputs[f'{type_name}'], colorfix.inputs[1])
                    #has_mtl.inputs["Normal"].default_value = (0.0,0.0,0.0,0.0)

                    if type_name == 'Normal':
                        invnrmnode = create_node(tree,'ShaderNodeGroup', -200,-200, "cus", InvertNormalNode().name) if otps.invert_green_n else None

                        gamma = create_node(tree,'ShaderNodeGamma', -200,0, "", '')
                        set_default(gamma,1, 2.4)
                        tree.links.new(has_mtl.outputs[f'RawNormal'], gamma.inputs[0])
                        tree.links.new(gamma.outputs[0], colorfix.inputs[1])
                        if invnrmnode:
                            tree.links.new(gamma.outputs[0], invnrmnode.inputs['Normal'])
                            tree.links.new(invnrmnode.outputs['Normal'], colorfix.inputs[1])
                        #seprgb = create_node(tree,'ShaderNodeSeparateRGB', -600,0, "", "")
                        #nrmlznd = create_node(tree,'ShaderNodeVectorMath', -600,0, "op", "NORMALIZE")
                        if otps.height_to_normal:
                            subt = create_node(tree,'ShaderNodeMixRGB', -600,0, "mix", "SUBTRACT")
                            set_default(subt, 0, 1.0)
                            bump = create_node(tree,'ShaderNodeBump', -600,0, "", "")
                            set_default(bump, 0, part.height_intensity)
                            nrmnd = create_node(tree,'ShaderNodeNormalMap', -600,0, "", "")

                            scre = create_node(tree,'ShaderNodeMixRGB', -600,0, "mix", "SCREEN")
                            set_default(scre, 0, 1.0)

                            tree.links.new(has_mtl.outputs["Height"], bump.inputs[2])
                            tree.links.new(bump.outputs[0], subt.inputs[1])
                            tree.links.new(nrmnd.outputs[0], subt.inputs[2])
                            tree.links.new(subt.outputs[0], scre.inputs[1])
                            #tree.links.new(has_mtl.outputs[f'RawNormal'], scre.inputs[2])
                            tree.links.new(has_mtl.outputs[f'RawNormal'], gamma.inputs[0])
                            tree.links.new(gamma.outputs[0], scre.inputs[2])
                            if invnrmnode:
                                tree.links.new(gamma.outputs[0], invnrmnode.inputs['Normal'])
                                tree.links.new(invnrmnode.outputs['Normal'], scre.inputs[2])
                            emis = get_node_by_name(tree,"Emission")
                            if emis:
                                tree.links.new(scre.outputs[0], emis.inputs[0])

                elif textype.type == "RGBA":
                    type_name = gettexturelabel(textype.RGBA)
                    #mixs = get_node_by_name(tree,"Mix Shader")
                    tree.links.new(has_mtl.outputs[f'{type_name}'], colorfix.inputs[1])
                    tree.links.new(has_mtl.outputs[f'{type_name}Alpha'], colorfix.inputs[2])
                    tree.links.new(has_mtl.outputs[f'{type_name}Alpha'], alphasocket)
                    #tree.links.new(has_mtl.outputs[f'{type_name}Alpha'], alphasocket)
                    
                    #alphafrom = has_mtl.outputs[f'{type_name}Alpha']
                    #alphabake = False
                elif textype.type == "RGB_A":
                    type_name = gettexturelabel(textype.RGB)
                    #alpha_name = gettexturelabel(textype.A)

                    tree.links.new(has_mtl.outputs[f'{type_name}'], colorfix.inputs[1])
                    set_default(colorfix, 2, (1.0,1.0,1.0,1.0))
                    #tree.links.new(has_mtl.outputs[f'{alpha_name}'], alphasocket)
                    if alpha_name in has_mtl.outputs:
                        alphafrom = has_mtl.outputs[f'{alpha_name}']
                        alphabake = True
                elif textype.type == "R_G_B_A":
                    R = gettexturelabel(textype.R)
                    G = gettexturelabel(textype.G)
                    B = gettexturelabel(textype.B)
                    A = gettexturelabel(textype.A)
                    Combine = create_node(material.node_tree,'ShaderNodeCombineRGB', 50,300, "", "")
                    
                    tree.links.new(has_mtl.outputs[f'{R}'], Combine.inputs[0])
                    tree.links.new(has_mtl.outputs[f'{G}'], Combine.inputs[1])
                    tree.links.new(has_mtl.outputs[f'{B}'], Combine.inputs[2])
                    #tree.links.new(has_mtl.outputs[f'{A}'], alphasocket)

                    tree.links.new(Combine.outputs[0], colorfix.inputs[1])
                    if alpha_name in has_mtl.outputs:
                        alphafrom = has_mtl.outputs[f'{A}']
                        alphabake = True
                    set_default(colorfix, 2, (1.0,1.0,1.0,1.0))

                elif textype.type == "R":
                    
                    R = gettexturelabel(textype.R)
                    bw = create_node(material.node_tree,'ShaderNodeRGBToBW', 50,300, "", "")
                    
                    tree.links.new(has_mtl.outputs[f'{R}'], bw.inputs[0])
                    tree.links.new(bw.outputs[0], colorfix.inputs[1])

                    set_default(colorfix, 2, (1.0,1.0,1.0,1.0))
                    alphasocket.default_value = 1.0
                    alphabake = True
                image_name = generate_filename(textype.save_name, context, obj_name, mtlname, file_name, set_name)
                albake_image = None
                if alphabake and alphafrom:
                    saved_links = get_links(colorfix, 1)
                    tree.links.new(alphafrom, colorfix.inputs[1])
                    albake_image = bpy.data.images.new(f"{image_name}_alpha", part.texture_sizeX, part.texture_sizeY, alpha=True)
                    render_image(bake_scene, albake_image)  
                    set_links(saved_links,colorfix.inputs[1])
                    clear_socket_links(alphasocket.node, 0)
                bake_image = bpy.data.images.new(image_name, part.texture_sizeX, part.texture_sizeY, alpha=True)
                render_image(bake_scene, bake_image, alpha_bake = albake_image)    
                file_path = os.path.join(directory, bake_image.name + ".png")
                bake_image.filepath_raw = os.path.join(directory, basescene.other_props.currentprefix + bake_image.name + ".png")
                
                bake_image.save()

                bpy.data.images.remove(bake_image)
                if albake_image:
                    bpy.data.images.remove(albake_image)

        cleanup_bake_scene( bake_scene, material, plane)

        bpy.context.window.scene = basescene

        for area in context.screen.areas:
            if area.type == 'FILE_BROWSER':
                area.tag_redraw()
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class CollapseLayer(Operator):
    bl_idname = "paint.collapse_layer"
    bl_label = "Collapse layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty(default = -1)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Warning: This operation cannot be undone.", icon='ERROR')

    def execute(self, context):
        basescene = bpy.context.window.scene
        part = get_material_collection()
        FoundLayer = part.layers[self.layer_index]
        suc = False
        bkimg = FoundLayer.resource.image
        if not bkimg:
            bkimg = create_bake_image(part.texture_sizeX,part.texture_sizeY, FoundLayer, suffix="")
        if bkimg:
            suc, bake_image = bake_layer(context, FoundLayer, basescene, bkimg)

        if suc:
            if bake_image:
                FoundLayer.resource.image = bkimg
                FoundLayer.filters.clear()
                FoundLayer.mask = False
                UpdateShader()
            return {'FINISHED'}
        else:
            return {'CANCELLED'}
       
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class CombineWithLayerBelowOperator(Operator):
    bl_idname = "paint.combine_with_layer_below"
    bl_label = "Combine with layer below"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty(default = -1)
    applyfilters: BoolProperty(default = True)
    applyfilters2: BoolProperty(default = False)

    def draw(self, context):
        layout = self.layout
        part = get_material_collection()
        layer = part.layers[self.layer_index]
        if not layer:
            return
        if layer.attachedto:
            attl = get_layer_by_id(layer.attachedto)
            if attl:
                FoundLayer = get_layer_below(attl.sub_layers, layer.id)
        else:
            FoundLayer = get_layer_below(part.base_layers, layer.id)
        if not FoundLayer:
            layout.row().label(text=f"No Layer To Combine With")
            return 
        layout.label(text="Warning: This operation cannot be undone.", icon='ERROR')
        layout.row().label(text=f"Combine current layer with {FoundLayer.layer_name}", icon='NODE_COMPOSITING')
        layout.row().label(text=f"Image {FoundLayer.resource.image.name}")
        layout.row().prop(self, "applyfilters", text="Apply Filters For Current layer", icon= "SHADERFX")
        layout.row().prop(self, "applyfilters2", text="Apply Filters For Layer Below", icon= "SHADERFX")
        
    def execute(self, context):
        basescene = bpy.context.window.scene
        part = get_material_collection()
        index = -1
        CurrentLayer = part.layers[self.layer_index]
        layer = CurrentLayer
        attl=None
        if not layer:
            return
        if layer.attachedto:
            attl = get_layer_by_id(layer.attachedto)
            if attl:
                BelowLayer = get_layer_below(attl.sub_layers, layer.id)
        else:
            BelowLayer = get_layer_below(part.base_layers, layer.id)
    
        if not CurrentLayer or not BelowLayer:
            return {'CANCELLED'}
        if self.applyfilters:
            suc, bake_image = bake_layer(context, CurrentLayer, basescene, CurrentLayer.resource.image)

        bake_scene, material, plane, output_node, colorfix, alphasocket, camera = setup_bake_scene(basescene)

        tree, group_node = Add_layer(material, output_node, CurrentLayer)
        tree, below_group_node = Add_layer(material, output_node, BelowLayer)

        tree.links.new(below_group_node.outputs['Color'], group_node.inputs['Color'])
        tree.links.new(below_group_node.outputs['Alpha'], group_node.inputs['Alpha'])

        tree.links.new(group_node.outputs['Color'], colorfix.inputs[1])
        tree.links.new(group_node.outputs['Alpha'], colorfix.inputs[2])
        tree.links.new(group_node.outputs['Alpha'], alphasocket)

        render_image(bake_scene, BelowLayer.resource.image)

        cleanup_bake_scene( bake_scene, material, plane)
        bpy.context.window.scene = basescene

        if attl:
            remove_layer_ref(attl.sub_layers,CurrentLayer.id)
        else:
            remove_layer_ref(part.base_layers,CurrentLayer.id)

        UpdateShader()
        if suc:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}
       
    def invoke(self, context, event):
        
        return context.window_manager.invoke_props_dialog(self)

class CombineAllLayersOperator(Operator):
    bl_idname = "paint.combine_all_layers"
    bl_label = "Combine All Layers"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Warning: This operation cannot be undone.", icon='ERROR')

    def execute(self, context):
        bsmtl = hasmatnode()
        usdtypes = getusedtypes()
        basescene = bpy.context.window.scene
        part = get_material_collection()
        
        bake_scene, material, plane, output_node, colorfix, alphasocket, camera = setup_bake_scene(basescene)

        group_node = material.node_tree.nodes.new('ShaderNodeGroup')
        group_node.node_tree = bsmtl
        imgs= []
        types= []

        tree = material.node_tree
        for type in usdtypes:
            nm = gettexturelabel(type)
            bake_image = bpy.data.images.new(nm, part.texture_sizeX, part.texture_sizeY, alpha=True)
            bake_image.alpha_mode = 'CHANNEL_PACKED'
            bake_image.colorspace_settings.name = 'sRGB'
            tree.links.new(group_node.outputs[f'{nm}'], colorfix.inputs[1])
            tree.links.new(group_node.outputs[f'{nm}Alpha'], colorfix.inputs[2])
            tree.links.new(group_node.outputs[f'{nm}Alpha'], alphasocket)

            render_image(bake_scene, bake_image)
            imgs.append(bake_image)
            types.append(type)

        cleanup_bake_scene( bake_scene, material, plane)

        bpy.context.window.scene = basescene
        part.base_layers.clear()
        
        for i, im in enumerate(imgs):
            layer_item = part.layers.add()
            layer_item.suppress_update = True
            layer_item.resource.suppress_update = True
            layer_item.resource.image = im
            layer_item.layer_name = newlayername()
            layer_item.id = shortid()

            part.base_layers.add().id = layer_item.id

            layer_item.suppress_update = False
            layer_item.resource.suppress_update = False
        SelectLayer(layer_item.id)

        UpdateShader()

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class SnapshotLayer(Operator):
    bl_idname = "paint.snapshotlayer"
    bl_label = "Snapshot Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty(default = -1)
    filter_index: IntProperty(default = -1)
    addfilter: StringProperty()
    addfiltervalue: FloatProperty()
    def execute(self, context):

        part = get_material_collection()
        FoundLayer = part.layers[self.layer_index]
        suc = False
        if FoundLayer:
            if FoundLayer.filters:
                suc, bake_image = snapshot(context, FoundLayer, FoundLayer.filters[self.filter_index], adfilter = self.addfilter, adfilter_value = self.addfiltervalue)
                UpdateShader()

        if suc:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

def snapshot(context, FoundLayer, foundfilter, adfilter = "", adfilter_value = 0.0):
    part = get_material_collection()
    node_group = bpy.data.node_groups.get(f"{getlayergroupname(FoundLayer)}_filters")
    basescene = bpy.context.window.scene

    image_name = f"{foundfilter.id}_snapshot"

    bake_image = foundfilter.resource.image
    if not foundfilter.resource.image:
        bake_image = bpy.data.images.new(image_name, part.texture_sizeX, part.texture_sizeY, alpha=True)

    filter_node = get_node_by_name(node_group, foundfilter.node_name)
    output = get_node_by_name(node_group, "Group Output")

    bake_scene, material, plane, output_node, colorfix, alphasocket, camera = setup_bake_scene(basescene)

    node_group.links.new(filter_node.outputs['Pass'], output.inputs["Color"])
    node_group.links.new(filter_node.outputs['PassAlpha'], output.inputs["Alpha"])
    tree, group_node = Add_layer(material, output_node, FoundLayer)
    tree.links.new(group_node.outputs['Color'], colorfix.inputs[1])
    tree.links.new(group_node.outputs['Alpha'], colorfix.inputs[2])
    tree.links.new(group_node.outputs['Alpha'], alphasocket)

    render_image(bake_scene, bake_image, filter = adfilter, filter_value = adfilter_value)
    cleanup_bake_scene( bake_scene, material, plane)

    bpy.context.window.scene = basescene

    if True:
        foundfilter.resource.image = bake_image
    return True, bake_image
    
def BakeLayerToImage(self,context, layer):
    basescene = bpy.context.window.scene
    part = get_material_collection()
    bake_image = create_bake_image(part.texture_sizeX, part.texture_sizeY, layer, suffix=layer.resource.image.name if layer.resource.image else layer.layer_name)
    suc, bake_image = bake_layer(context, layer, basescene,bake_image)

    return bake_image

def bake_layer(context, layer, basescene, bake_image):

    FoundLayer = layer

    if FoundLayer:

        bake_scene, material, plane, output_node, colorfix, alphasocket, camera = setup_bake_scene(basescene)

        tree, group_node = Add_layer(material, output_node, FoundLayer)

        tree.links.new(group_node.outputs['Color'], colorfix.inputs[1])
        tree.links.new(group_node.outputs['Alpha'], colorfix.inputs[2])
        tree.links.new(group_node.outputs['Alpha'], alphasocket)

        render_image(bake_scene, bake_image)
        cleanup_bake_scene( bake_scene, material, plane)
        bpy.context.window.scene = basescene

        return True, bake_image
        
    else:
        return False, None

def setup_bake_scene(basescene):
    part = get_material_collection()

    new_scene = bpy.data.scenes.new("BakeScene")
    bpy.context.window.scene = new_scene
    material = bpy.data.materials.new(name="HASBakeMtlTemp")

    new_scene.render.resolution_y = part.texture_sizeY
    new_scene.render.resolution_x = part.texture_sizeX
    yr = part.texture_sizeY
    xr = part.texture_sizeX
    if material.use_nodes is False:
        material.use_nodes = True

    tree = material.node_tree
    material.blend_method = 'BLEND'
    new_scene.render.film_transparent = True
    new_scene.view_layers["ViewLayer"].use_pass_combined = False
    new_scene.view_layers["ViewLayer"].use_pass_emit = True
    new_scene.view_settings.view_transform = 'Standard'
    new_scene.render.image_settings.color_mode = 'RGBA'
    new_scene.render.image_settings.color_depth = '16'
    new_scene.render.image_settings.compression = 0
    
    new_scene.render.engine = 'BLENDER_EEVEE'
    new_scene.render.dither_intensity = 0
    new_scene.render.filter_size = 0

    for node in tree.nodes:
        if node.type == 'OUTPUT_MATERIAL':
            output_node = node
        else:
            tree.nodes.remove(node)

    if 'output_node' not in locals():
        output_node = tree.nodes.new('ShaderNodeOutputMaterial')
        output_node.location = (200, 0)

    MixShader = tree.nodes.new('ShaderNodeMixShader')
    MixShader.location = (200, 0)
    MixRGB = create_node(tree,'ShaderNodeMixRGB', -200,0, "mix", 'DIVIDE')

    set_default(MixRGB, 0, 1.0)
    Transparent = tree.nodes.new('ShaderNodeBsdfTransparent')
    Transparent.location = (200, 0)
    Emission = tree.nodes.new('ShaderNodeEmission')
    Emission.location = (200, 0)

    tree.links.new(MixRGB.outputs[0], Emission.inputs[0])
    tree.links.new(Transparent.outputs[0], MixShader.inputs[1])
    tree.links.new(Emission.outputs[0], MixShader.inputs[2])
    tree.links.new(MixShader.outputs[0], output_node.inputs[0])

    sftext = bpy.ops.object.text_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    sftext = bpy.context.object
    sftext.data.body = "Scene for offscreen operations. Just delete this scene if you stuck here"
    sftext.hide_render = True

    bpy.ops.object.camera_add(location=(0, 0, 2), rotation=(0, 0, 0))
    camera = bpy.context.object
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 2  
    camera.location = (0, 0, 2)

    new_scene.camera = camera
    bpy.ops.mesh.primitive_plane_add(size=2)
    plane = bpy.context.active_object
    plane.name = "BakePlane"
    plane.data.materials.append(material)

    plane.scale.y = yr / max(xr, yr)
    plane.scale.x = xr / max(yr, xr)

    return new_scene, material, plane, output_node, MixRGB, MixShader.inputs[0], camera

def Add_layer(mat, output_node, layer):

    name = getlayergroupname(layer)

    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        if node_group:
            tree = mat.node_tree
            group_node = tree.nodes.new('ShaderNodeGroup')
            group_node.node_tree = node_group
            group_node.name = name
            group_node.location = (-300, 0)
            return tree, group_node

def create_bake_image(texture_sizeX,texture_sizeY, layer, suffix=""):

    image_name = f"BR_{layer.name}{suffix}"
    bake_image = bpy.data.images.new(image_name, texture_sizeX, texture_sizeY, alpha=True)
    
    bake_image.alpha_mode = 'CHANNEL_PACKED'
    bake_image.colorspace_settings.name = 'sRGB'

    return bake_image

def render_image(scene, bake_image, filter = "", filter_value = 0.0, alpha_bake = None):
    
    bpy.context.window.scene = scene
    
    # tree = scene.node_tree
    
    tree = bpy.data.node_groups.new("My new comp", "CompositorNodeTree")
    scene.compositing_node_group = tree

    render_layers = tree.nodes.new('CompositorNodeRLayers')
    render_layers.location = (-300, 0)
    if alpha_bake:
        alphaimage = tree.nodes.new('CompositorNodeImage')
        alphaimage.location = (0, 0)
        alphaimage.image = alpha_bake

    alpha_convert = tree.nodes.new('CompositorNodePremulKey')
    alpha_convert.location = (0, 0)
    # alpha_convert.inputs['Mapping'].default_value = 'PREMULTIPLIED_TO_STRAIGHT'
    alpha_convert.inputs[1].default_value = 'To Straight'
    
    colorspace = tree.nodes.new('CompositorNodeConvertColorSpace')
    colorspace.location = (0, 0)
    if is_4_0_or_newer():
        colorspace.from_color_space = 'Linear Rec.709'
    else:
        colorspace.from_color_space = 'Linear'
    colorspace.to_color_space = 'sRGB'

    gamma_node = tree.nodes.new(type='ShaderNodeGamma')
    
    set_default(gamma_node, 1, 1.0)
    gamma_node.location = (-600, 0)

    render_node = tree.nodes.new(type='CompositorNodeRLayers')
    render_node.location = (400, -200)
    filternode = None
    if filter == "BLUR":
        filternode = tree.nodes.new(type='CompositorNodeBlur')
        filternode.location = (400, -200) 
        filternode.size_y = int(filter_value*20)
        filternode.size_x = int(filter_value*20)

    viewer_node = tree.nodes.new(type='CompositorNodeViewer')
    viewer_node.location = (400, -200)
    links = tree.links
    
    links.new(render_layers.outputs[0], alpha_convert.inputs[0])
    links.new(alpha_convert.outputs[0], colorspace.inputs[0])
    if alpha_bake:
        links.new(colorspace.outputs[0], viewer_node.inputs[0])
        links.new(alphaimage.outputs[0], viewer_node.inputs[1])
    else:
        links.new(colorspace.outputs[0], viewer_node.inputs[0])

    if filternode:
        links.new(colorspace.outputs[0], filternode.inputs['Image'])
        links.new(filternode.outputs['Image'], viewer_node.inputs[0])

    bpy.ops.render.render()

    render_result = bpy.data.images.get("Viewer Node")
    if render_result:
        bake_image.scale(render_result.size[0], render_result.size[1])
        
        bake_image.pixels = list(render_result.pixels)

def cleanup_bake_scene( new_scene, mat, plane):
    bpy.data.materials.remove(mat)
    bpy.data.objects.remove(plane)
    bpy.data.scenes.remove(new_scene)

class ResizeTexturePopup(Operator):
    """Resize the selected texture"""
    bl_idname = "paint.resize_texture"
    bl_label = "Resize Layer"
    bl_options = {'REGISTER'}

    layer_index: IntProperty(default=-1)

    new_width: IntProperty(name="New Width", default=1024, min=1)
    new_height: IntProperty(name="New Height", default=1024, min=1)

    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Warning: This operation cannot be undone.", icon='ERROR')
        
        layout.prop(self, "new_width")
        layout.prop(self, "new_height")

    def execute(self, context):

        basescene = bpy.context.window.scene
        part = get_material_collection()

        layer = part.layers[self.layer_index]
        bake_scene, material, plane, output_node, colorfix, alphasocket, camera = setup_bake_scene(basescene)
        bake_scene.render.resolution_x = self.new_width
        bake_scene.render.resolution_y = self.new_height
        tree = material.node_tree
        image_node = create_node(tree,'ShaderNodeTexImage', -600,0, "img", layer.resource.image)
        image_node.interpolation= part.texture_filtering
        tree.links.new(image_node.outputs[0], colorfix.inputs[1])
        tree.links.new(image_node.outputs[1], colorfix.inputs[2])
        tree.links.new(image_node.outputs[1], alphasocket)

        render_image(bake_scene, layer.resource.image)

        cleanup_bake_scene( bake_scene, material, plane)

        bpy.context.window.scene = basescene
        return {'FINISHED'}
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class ResizeAllLayersPopup(Operator):
    """Resize the selected texture"""
    bl_idname = "paint.resize_layers"
    bl_label = "Resize Layers"
    bl_options = {'REGISTER'}

    new_width: IntProperty(name="New Width", default=1024, min=1)
    new_height: IntProperty(name="New Height", default=1024, min=1)

    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Warning: This operation cannot be undone.", icon='ERROR')
        
        layout.prop(self, "new_width")
        layout.prop(self, "new_height")

    def execute(self, context):
        basescene = bpy.context.window.scene
        part = get_material_collection()
        bake_scene, material, plane, output_node, colorfix, alphasocket, camera = setup_bake_scene(basescene)
        bake_scene.render.resolution_x = self.new_width
        bake_scene.render.resolution_y = self.new_height
        tree = material.node_tree

        for layer in part.layers:

            image_node = create_node(tree,'ShaderNodeTexImage', -600,0, "img", layer.resource.image)
            image_node.interpolation= part.texture_filtering
            tree.links.new(image_node.outputs[0], colorfix.inputs[1])
            tree.links.new(image_node.outputs[1], colorfix.inputs[2])
            tree.links.new(image_node.outputs[1], alphasocket)

            render_image(bake_scene, layer.resource.image)

        cleanup_bake_scene( bake_scene, material, plane)

        bpy.context.window.scene = basescene
        return {'FINISHED'}
    def invoke(self, context, event):

        return context.window_manager.invoke_props_dialog(self)

class BAKING_OT_BakeTextures(Operator):
    bl_idname = "paint.bake_textures"
    bl_label = "Bake Textures"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        original_scene = context.scene
        low_poly = bpy.context.active_object
        high_poly = None
        part = get_material_collection()
        if not part.bake_maps:
            return {'CANCELLED'}

        if "Baking_Scene" not in bpy.data.scenes:
            baking_scene = bpy.data.scenes.new("Baking_Scene")
        else:
            baking_scene = bpy.data.scenes["Baking_Scene"]
        sel=[]
        baking_props = part.baking_props
        bpy.context.window.scene = baking_scene
        if baking_props.use_cage and baking_props.cage:
            bpy.context.scene.render.bake.cage_object = baking_props.cage
            baking_props.cage.hide_select = False
            baking_props.cage.hide_render = False
        if baking_props.gethpobjects(context):
            high_poly = combine_objects(baking_props.gethpobjects(context), apply_modifiers=True)
            high_poly.name = "HP"
            if high_poly:
                sel.append(high_poly)
        if baking_props.getlpobjects(context):
            low_poly = combine_objects(baking_props.getlpobjects(context), apply_modifiers=True)
        else:
            low_poly = combine_objects([low_poly], apply_modifiers=True)
        
        if low_poly:
            low_poly.name = "LP"
            sel.append(low_poly)

        if baking_scene.render.bake.cage_object:
            bpy.data.scenes["Baking_Scene"].collection.objects.link(baking_scene.render.bake.cage_object)
        bpy.context.scene.render.engine='CYCLES'
        bpy.context.scene.cycles.samples=part.baking_props.samples
        bpy.context.scene.render.bake.use_selected_to_active=True if high_poly else False
        bpy.context.scene.render.bake.use_cage=True if baking_props.use_cage else False

        bpy.ops.object.select_all(action='DESELECT')
        for obj in sel:
            obj.select_set(True)

        view_layer = baking_scene.view_layers[0]
        view_layer.objects.active = low_poly

        if low_poly.material_slots:
            low_poly.data.materials.clear()

        lpmtl = bpy.data.materials.new(name=f"LP_tmpbakemtl")
        low_poly.data.materials.append(lpmtl)
        lpmtl.use_nodes = True
        hpmtl = None
        if high_poly:
            if not len(high_poly.data.materials) ==0:
                hpmtl = high_poly.data.materials[0]
            else:
                hpmtl = bpy.data.materials.new(name=f"HP_tmpbakemtl")
                high_poly.data.materials.append(hpmtl)

        bakefrom = low_poly
        if high_poly:
            high_poly.select_set(True)
            bakefrom = high_poly
        bakefrommtl = bakefrom.data.materials[0]
        
        tmp_material = bpy.data.materials.new(name="HAS_TempCapture_Mtl")
        tmp_material.use_nodes = True
        tmp_nodes = tmp_material.node_tree.nodes
        if not high_poly:
            lpmtl = tmp_material
        links = tmp_material.node_tree.links
        gnr = None
        
        for bake_map in part.bake_maps:
            defaultbake = False
            for node in tmp_nodes:
                tmp_nodes.remove(node)
            if bake_map.use_map:

                if bake_map.type == "CURVATURE":

                    subsurf_modifier = bakefrom.modifiers.new(name="HASTempSubdivision", type='SUBSURF')
                    if not bake_map.smsubd:
                        subsurf_modifier.subdivision_type = 'SIMPLE'

                    subsurf_modifier.levels = 0
                    subsurf_modifier.render_levels = bake_map.subd

                    geom = tmp_nodes.new(type='ShaderNodeNewGeometry')
                    power = tmp_nodes.new(type='ShaderNodeMath')
                    power.operation = "POWER"

                    set_default(power, 1, 2.478)
                    emission = tmp_nodes.new(type='ShaderNodeEmission')

                    material_output_node = tmp_nodes.new(type='ShaderNodeOutputMaterial')
                    links.new(geom.outputs["Pointiness"], power.inputs[0])
                    links.new(power.outputs[0], emission.inputs["Color"])
                    links.new(emission.outputs[0], material_output_node.inputs['Surface'])
                elif bake_map.type == "AO":

                    aonode = tmp_nodes.new(type='ShaderNodeAmbientOcclusion')

                    set_default(aonode, "Distance", 50)
                    emission = tmp_nodes.new(type='ShaderNodeEmission')

                    material_output_node = tmp_nodes.new(type='ShaderNodeOutputMaterial')     

                    links.new(aonode.outputs[0], emission.inputs[0])

                    links.new(emission.outputs[0], material_output_node.inputs['Surface'])

                elif bake_map.type == "NRMOBJ":

                    geometry_node = tmp_nodes.new(type='ShaderNodeNewGeometry')
                    vector_math_add = tmp_nodes.new(type='ShaderNodeVectorMath')
                    vector_math_add.operation = 'MULTIPLY_ADD'
                    set_default(vector_math_add, 1, (0.5,0.5,0.5))
                    set_default(vector_math_add, 2, (0.5,0.5,0.5))
                    
                    material_output_node = tmp_nodes.new(type='ShaderNodeOutputMaterial')

                    links.new(geometry_node.outputs['Normal'], vector_math_add.inputs[0])

                    links.new(vector_math_add.outputs[0], material_output_node.inputs['Surface'])

                elif bake_map.type == "POSITION":

                    texcoord = tmp_nodes.new(type='ShaderNodeTexCoord')
                    seprgb = tmp_nodes.new(type='ShaderNodeSeparateRGB')
                    combrgb = tmp_nodes.new(type='ShaderNodeCombineRGB')
                    invert = tmp_nodes.new(type='ShaderNodeInvert')
                    gamma = tmp_nodes.new(type='ShaderNodeGamma')

                    set_default(gamma, 1, 2.2)
                    emission = tmp_nodes.new(type='ShaderNodeEmission')

                    material_output_node = tmp_nodes.new(type='ShaderNodeOutputMaterial')

                    links.new(texcoord.outputs[0], seprgb.inputs[0])

                    links.new(seprgb.outputs[0], combrgb.inputs[0])
                    links.new(seprgb.outputs[1], invert.inputs[1])
                    links.new(invert.outputs[0], combrgb.inputs[1])
                    links.new(seprgb.outputs[2], combrgb.inputs[2])

                    links.new(combrgb.outputs[0], gamma.inputs[0])
                    links.new(gamma.outputs[0], emission.inputs[0])

                    links.new(emission.outputs[0], material_output_node.inputs['Surface'])
        
                elif bake_map.type == "HEIGHT":
                    if high_poly:
                        bpy.ops.object.select_all(action='DESELECT')
                        high_poly.select_set(True)
                        bpy.context.view_layer.objects.active = high_poly

                        geo_nodes_mod = high_poly.modifiers.new(name="Height_GeometryNodes", type='NODES')
                        geo_nodes_mod.node_group = bpy.data.node_groups.new(name="HeightGeometryNodes", type='GeometryNodeTree')
                        nodes = geo_nodes_mod.node_group.nodes

                        for node in nodes:
                            nodes.remove(node)
                        for link in geo_nodes_mod.node_group.links:
                            geo_nodes_mod.node_group.links.remove(link)
                        gnlinks = geo_nodes_mod.node_group.links
                        input_node = nodes.new(type='NodeGroupInput')
                        output_node = nodes.new(type='NodeGroupOutput')
                        gnr = geo_nodes_mod.node_group
                        create_socket(geo_nodes_mod.node_group, 'Geometry', 'geom', True)
                        create_socket(geo_nodes_mod.node_group, 'Geometry', 'geom', False)
                        create_socket(geo_nodes_mod.node_group, 'Height', 'float', False)
                        object_info_node = nodes.new(type='GeometryNodeObjectInfo')
                        if baking_props.cage:
                            object_info_node.inputs['Object'].default_value = baking_props.cage
                        else:
                            object_info_node.inputs['Object'].default_value = low_poly

                        transfer = nodes.new(type='GeometryNodeAttributeTransfer' if not is_3_4_or_newer() else "GeometryNodeSampleNearestSurface")
                        transfer.data_type = 'FLOAT_VECTOR' if is_3_4_or_newer() else "FLOAT"
                        if not is_3_4_or_newer():
                            transfer.mapping = 'NEAREST_FACE_INTERPOLATED'

                        source = nodes.new(type='GeometryNodeInputPosition')
                        base = nodes.new(type='GeometryNodeInputPosition')

                        dist = nodes.new(type='ShaderNodeVectorMath')
                        dist.operation = 'DISTANCE'

                        maprange = nodes.new(type='ShaderNodeMapRange')
                    
                        set_default(maprange, 3, 1.0)
                        set_default(maprange, 4, 0.0)
                        set_default(maprange, 1, -bake_map.heightdist)
                        set_default(maprange, 2, bake_map.heightdist)

                        add = nodes.new(type='ShaderNodeMath')
                        add.operation = "ADD"
                        set_default(add, 1, bake_map.heightoffset)

                        for input_socket in output_node.inputs[1:-1]:
                            if input_socket.name == "Height":
                                geo_nodes_mod[input_socket.identifier + "_attribute_name"] = "Height"

                        gnlinks.new(input_node.outputs[0], output_node.inputs[0])
                        gnlinks.new(object_info_node.outputs['Geometry'], transfer.inputs[0])
                        gnlinks.new(source.outputs[0], transfer.inputs['Attribute' if not is_3_4_or_newer() else "Value"])
                        
                        gnlinks.new(transfer.outputs['Value'], dist.inputs[0])
                        gnlinks.new(base.outputs[0], dist.inputs[1])

                        gnlinks.new(dist.outputs['Value'], add.inputs[0])
                        gnlinks.new(add.outputs[0], maprange.inputs[0])
                        gnlinks.new(maprange.outputs[0], output_node.inputs[1])

                        height_nodes = tmp_material.node_tree.nodes

                        attribute_node = height_nodes.new(type='ShaderNodeAttribute')
                        attribute_node.attribute_name = 'Height'
                        material_output_node = height_nodes.new(type='ShaderNodeOutputMaterial')

                        tmp_material.node_tree.links.new(attribute_node.outputs['Fac'], material_output_node.inputs['Surface'])
                        for obj in sel:
                            obj.select_set(True)
                        view_layer.objects.active = low_poly
                    else:
                        continue
                else:
                    defaultbake = True

                self.addimage(lpmtl, part, bake_map, baking_props)
                if not bake_map.type == "DIFFUSE":
                    bakefrom.data.materials[0] = tmp_material
                    baking_scene.render.bake.use_clear = True
                    baking_scene.cycles.bake_type = 'EMIT'
                if bake_map.type == "EMISSION":
                    bakefrom.data.materials[0] = bakefrommtl
                    baking_scene.render.bake.use_clear = True
                    baking_scene.cycles.bake_type = 'EMIT'
                    defaultbake = False
                try:
                    if not defaultbake:
                        bpy.ops.object.bake(type='EMIT')
                    else:
                        if bake_map.type == "DIFFUSE":
                            baking_scene.render.bake.use_pass_direct = False
                            baking_scene.render.bake.use_pass_indirect = False
                            baking_scene.cycles.bake_type = 'DIFFUSE'
                        bpy.ops.object.bake(type=bake_map.type, use_clear=True, margin=4, save_mode='INTERNAL')
                except RuntimeError as e:
                    self.report({'ERROR'}, f"Bake failed: {e}")
                bpy.ops.object.modifier_remove(modifier="HASTempSubdivision")
        if tmp_material == lpmtl and tmp_material.users == 0:
            bpy.data.materials.remove(tmp_material)
        else:
            if tmp_material and tmp_material.users == 0:
                bpy.data.materials.remove(tmp_material)
            if lpmtl and lpmtl.users == 0:
                bpy.data.materials.remove(lpmtl)
        if not tmp_material == hpmtl:
            if hpmtl and hpmtl.users == 0:
                bpy.data.materials.remove(hpmtl)
        if gnr and gnr.users == 0:
            bpy.data.node_groups.remove(gnr)
            
        remove_object(high_poly)
        remove_object(low_poly)

        bpy.data.scenes.remove(baking_scene)
        if baking_props.cage:
            baking_props.cage.hide_select = True
            baking_props.cage.hide_render = True
        bpy.context.window.scene = original_scene

        return {'FINISHED'}

    def addimage(self, mtl,part,bake_map,baking_props):
        image_name = f"{part.name.replace(' ', '')}_{getname(BAKE_TYPE, bake_map.type).replace(' ', '')}"
        bake_image = bpy.data.images.get(image_name)
        if not bake_image:
            bake_image = bpy.data.images.new(name=image_name, width=baking_props.bake_image_sizeY, height=baking_props.bake_image_sizeY)
            bake_image.generated_type = 'BLANK'
            bake_image.generated_color = (0.0, 0.0, 0.0, 1.0)
        else:
            bake_image.generated_type = 'BLANK'
            bake_image.generated_color = (0.0, 0.0, 0.0, 1.0)
            bake_image.user_clear()

            bpy.data.images[bake_image.name].scale( baking_props.bake_image_sizeY, baking_props.bake_image_sizeY )

            bake_image.pixels = [0.0] * (bake_image.size[0] * bake_image.size[1] * bake_image.channels)
            bake_image.pack()

        mtl.use_nodes = True
        nodes = mtl.node_tree.nodes
        texture_node = nodes.new('ShaderNodeTexImage')
        texture_node.image = bake_image
        bake_image.use_fake_user = True
        nodes.active = texture_node
        bake_map.image = bake_image
        
        return bake_image

def remove_object(obj):
    if obj and obj.name in bpy.data.objects:
        
        mesh = obj.data if obj.type == 'MESH' else None

        for collection in obj.users_collection:
            collection.objects.unlink(obj)

        bpy.data.objects.remove(obj, do_unlink=True)

        if mesh and mesh.users == 0:
            bpy.data.meshes.remove(mesh)

def combine_objects(objects, apply_modifiers=False):
    if not objects:
        return None

    copied_objects = []
    for obj in objects:
        if obj:
            
            new_mesh = obj.data.copy()
            new_obj = obj.copy()
            new_obj.data = new_mesh
            bpy.context.collection.objects.link(new_obj)
            
            if apply_modifiers:
                for modifier in new_obj.modifiers:
                    if modifier.show_viewport:  
                        bpy.context.view_layer.objects.active = new_obj
                        bpy.ops.object.modifier_apply(modifier=modifier.name)
                new_obj.modifiers.clear()
            else:
                new_obj.modifiers.clear()
            
            copied_objects.append(new_obj)

    bpy.ops.object.select_all(action='DESELECT')

    for obj in copied_objects:
        obj.select_set(True)

    if copied_objects:
        bpy.context.view_layer.objects.active = copied_objects[0]

    if bpy.ops.object.join.poll():
        bpy.ops.object.join()
    else:
        return None

    return bpy.context.object

def set_smooth_cage(cage, smooth):
    if cage:
        
        if cage:
            if "smooth" in cage.modifiers:
                mod = cage.modifiers["smooth"]
            else:
                mod = cage.modifiers.new(name="smooth", type='WEIGHTED_NORMAL')
            
            mod.weight = 1
            
            cage.data.use_auto_smooth = smooth

        cage.modifiers["smooth"].show_viewport = smooth
        cage.modifiers["smooth"].show_render = smooth

def create_or_update_cage(context):
    part = get_material_collection()
    baking_props = part.baking_props
    nm = get_cage_name()

    set_smooth_cage(baking_props.cage, baking_props.smooth_cage)

    curobj = context.view_layer.objects.active
    if not baking_props.use_cage:
        if baking_props.cage:
            bpy.data.objects.remove(baking_props.cage, do_unlink=True) 
        return
    if get_cage():
        return
    low_poly = None

    if baking_props.use_cage:
        low_poly = combine_objects(baking_props.getlpobjects(context), apply_modifiers=True)

    if not low_poly:
        return

    if baking_props.use_cage:
        
        cage = low_poly
        cage.name = nm
        cage.modifiers.new(name="Cage_Displace", type='DISPLACE')
        cage_material = bpy.data.materials.new(name="CageMaterial")
        cage_material.use_nodes = True
        cage_material.blend_method = 'BLEND'
        cage_material.diffuse_color = baking_props.cage_color
        nodes = cage_material.node_tree.nodes
        nodes.clear()
        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')

        set_default(principled_node, 'Base Color', baking_props.cage_color)

        set_default(principled_node, 'Alpha', baking_props.cage_color[3])
        cage_material.node_tree.links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])
        context.view_layer.objects.active = cage
        cage.update_tag()
        cage.data.materials.clear()
        cage.data.materials.append(cage_material)
        cage.modifiers['Cage_Displace'].strength = baking_props.cage_depth
        baking_props.cage = cage
        cage.hide_select = True
        cage.hide_render = True

        set_smooth_cage(cage, baking_props.smooth_cage)
            
        context.view_layer.objects.active = curobj

    context.view_layer.objects.active = curobj

def update_cage_depth(context):
    part = get_material_collection()
    baking_props = part.baking_props
    cage = baking_props.cage
    if cage:
        cage = bpy.data.objects[get_cage_name()]
        cage.modifiers['Cage_Displace'].strength = baking_props.cage_depth

def update_cage_material(context):
    part = get_material_collection()
    curobj = context.view_layer.objects.active
    baking_props = part.baking_props
    cage = baking_props.cage
    if cage:
        if cage.active_material:
            cage.active_material.use_nodes = True
            cage.active_material.blend_method = 'BLEND'
            cage.active_material.diffuse_color = baking_props.cage_color
            nodes = cage.active_material.node_tree.nodes
            nodes.clear()
            output_node = nodes.new(type='ShaderNodeOutputMaterial')
            principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')

            set_default(principled_node, 'Base Color', baking_props.cage_color)
            set_default(principled_node, 'Alpha', baking_props.cage_color[3])
            cage.active_material.node_tree.links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])
            context.view_layer.objects.active = cage
            cage.update_tag()
            context.view_layer.objects.active = curobj

def get_cage_name():
    part = get_material_collection()
    if not part:
        return None
    return f"{part.name}_BakeCage"

def get_cage():
    nm = get_cage_name()
    if nm in bpy.data.objects:
        return bpy.data.objects[nm]
    return None
         
class BakeMapPref(Operator):
    bl_idname = "paint.bakemapprefs"
    bl_label = "Bake Preferences"
    bl_options = {'REGISTER', 'UNDO'}

    bake_type: StringProperty()

    def draw(self, context):
        layout = self.layout
        part = get_material_collection()
        for bkmp in part.bake_maps: 

            if bkmp.type == self.bake_type:
                if self.bake_type == "CURVATURE":
                    layout.label(text = "Curvature")
                    layout.prop(bkmp, "subd", text="Subdivide",slider = True)
                    layout.prop(bkmp, "smsubd", text="Smooth Subdiv",toggle = True)
                if self.bake_type == "AO":
                    layout.label(text = "Ambient Occlusion")
                    layout.prop(bkmp, "aodist", text="AO Distance",slider = True)
                if self.bake_type == "HEIGHT":
                    layout.label(text = "Height")
                    layout.prop(bkmp, "heightdist", text="Height Distance")
                    layout.prop(bkmp, "heightoffset", text="Height Offset")
                    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class GetFromSelected(Operator):
    bl_idname = "paint.get_from_selected"
    bl_label = "Make Group From Selected"
    bl_options = {'REGISTER', 'UNDO'}

    hp: BoolProperty(default = False)

    def execute(self, context):
        part = get_material_collection()
        expobj = []
        if self.hp:
            for ep in part.baking_props.high_poly_obj:
                if ep.obj:
                    expobj.append(ep.obj)
        else:
            for ep in part.baking_props.low_poly_obj:
                if ep.obj:
                    expobj.append(ep.obj)
                    
        for obj in context.selected_objects:
            if obj and obj.type == 'MESH':
                if not obj in expobj:
                    if self.hp:
                        part.baking_props.high_poly_obj.add().obj = obj 
                    else:
                        part.baking_props.low_poly_obj.add().obj = obj 
        return {'FINISHED'}

class RemoveAllBakeObjects(Operator):
    bl_idname = "paint.remove_all_bake_objects"
    bl_label = "Remove All Bake Objects"
    bl_options = {'REGISTER', 'UNDO'}

    hp: BoolProperty(default = False)

    def execute(self, context):
        part = get_material_collection()
        if self.hp:
            part.baking_props.high_poly_obj.clear()
            part.baking_props.high_poly_obj.add()
        else:
            part.baking_props.low_poly_obj.clear()
            part.baking_props.low_poly_obj.add()
    
        return {'FINISHED'}

class ExportORALayersOperator(Operator):
    """Export current layers to ORA file"""
    bl_idname = "paint.export_to_ora"
    bl_label = "Export to ORA"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype="FILE_PATH")
    
    def execute(self, context):

        if not self.filepath:
            self.report({'ERROR'}, "No file path specified.")
            return {'CANCELLED'}

        if not self.filepath.lower().endswith(".ora"):
            self.filepath += ".ora"

        ora_file = self.filepath

        part = get_material_collection() 
        layers = list(get_layers(part.base_layers))  
        layers.reverse() 

        save_dir = os.path.join(bpy.app.tempdir, "ora_temp")
        os.makedirs(save_dir, exist_ok=True)
        
        layer_files = []
        ora_layers = []
        
        for i, layer in enumerate(layers):
            baked_texture = BakeLayerToImage(self,context, layer)
            self.report({'INFO'}, f"Processing Layer {i}: {baked_texture.name}")

            image_name = baked_texture.name
            image_path = os.path.join(save_dir, image_name)
            baked_texture.filepath_raw = image_path
            baked_texture.file_format = 'PNG'
            baked_texture.save_render(image_path)
            
            ora_layer = {
                "name": baked_texture.name,
                "src": f"data/{image_name}",
                "opacity": str(layer.opacity),
                "composite-op": blend_mode_map.get(layer.blend_mode, "svg:src-over") 
            }

            ora_layers.append(ora_layer)
            layer_files.append(image_path)

            self.report({'INFO'}, f"Layer {i}: {baked_texture.name} saved as {image_name}")

        stack = Element("image", {"w": str(baked_texture.size[0]), "h": str(baked_texture.size[1]), "xres": "96", "yres": "96"})
        root_stack = SubElement(stack, "stack", {"name": "root", "opacity": "1.0", "composite-op": "svg:src-over"})
        
        for ora_layer in ora_layers:
            SubElement(root_stack, "layer", ora_layer)

        stack_xml_path = os.path.join(save_dir, "stack.xml")
        ElementTree(stack).write(stack_xml_path, encoding='utf-8', xml_declaration=True)

        with zipfile.ZipFile(ora_file, 'w') as ora_zip:
            ora_zip.write(stack_xml_path, "stack.xml")
            for image_file in layer_files:
                ora_zip.write(image_file, os.path.join("data", os.path.basename(image_file)))

        for image_file in layer_files:
            os.remove(image_file)
        os.remove(stack_xml_path)
        os.rmdir(save_dir)

        self.report({'INFO'}, f"ORA file created: {ora_file}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class ImportORALayersOperator(Operator):
    """Import ORA file as layers"""
    bl_idname = "paint.import_from_ora"
    bl_label = "Import ORA"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')

    filter_glob: StringProperty(
        default="*.ora",
        options={'HIDDEN'}
    )

    def execute(self, context):
        extract_dir = os.path.join(bpy.app.tempdir, "ora_import_temp")
        os.makedirs(extract_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(self.filepath, 'r') as ora_zip:
                ora_zip.extractall(extract_dir)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to extract ORA file: {e}")
            return {'CANCELLED'}

        stack_xml_path = os.path.join(extract_dir, 'stack.xml')
        if not os.path.exists(stack_xml_path):
            self.report({'ERROR'}, "stack.xml not found in the ORA file")
            return {'CANCELLED'}

        tree = ElementTree()
        try:
            tree.parse(stack_xml_path)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to parse stack.xml: {e}")
            return {'CANCELLED'}

        root = tree.getroot()

        canvas_width = int(root.attrib.get('w', 500))  
        canvas_height = int(root.attrib.get('h', 500))

        part = get_material_collection()
        layers = get_layers(part.base_layers)

        reverse_blend_mode_map = {v: k for k, v in blend_mode_map.items()}

        for i, layer_element in enumerate(reversed(root.findall(".//layer"))):
            layer_name = layer_element.attrib.get('name', f"Unnamed Layer {i}")
            layer_src = layer_element.attrib.get('src')
            layer_x = int(layer_element.attrib.get('x', 0))
            layer_y = int(layer_element.attrib.get('y', 0))

            image_path = os.path.join(extract_dir, layer_src)
            if not os.path.exists(image_path):
                self.report({'ERROR'}, f"Layer image not found: {layer_src}")
                continue

            try:

                src_image = bpy.data.images.load(image_path)
                src_image.name = layer_name

                new_image = bpy.data.images.new(layer_name, width=canvas_width, height=canvas_height)

                new_image.pixels = [0.0] * (canvas_width * canvas_height * 4)

                self.copy_pixels_into_canvas(src_image, new_image, layer_x, layer_y)

                new_layer = new_layer_from_image(new_image, layer_name = layer_name)

                composite_op = layer_element.attrib.get('composite-op', 'svg:src-over')
                opacity = float(layer_element.attrib.get('opacity', 1.0))

                new_layer.blend_mode = reverse_blend_mode_map.get(composite_op, 'MIX')
                new_layer.opacity = opacity  

            except Exception as e:
                self.report({'ERROR'}, f"Failed to add layer {layer_name}: {e}")
                continue
        try:
            for root_dir, dirs, files in os.walk(extract_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root_dir, name))
                for name in dirs:
                    os.rmdir(os.path.join(root_dir, name))
            os.rmdir(extract_dir)
        except Exception as e:
            self.report({'WARNING'}, f"Failed to clean up temporary files: {e}")

        return {'FINISHED'}
    def copy_pixels_into_canvas(self, src_image, canvas_image, offset_x, offset_y):
        """Copy src_image data into canvas_image at the given offset without resizing the original image."""
        if not src_image.has_data:
            src_image.reload()
        if not canvas_image.has_data:
            canvas_image.reload()

        src_pixels = list(src_image.pixels[:])
        canvas_pixels = list(canvas_image.pixels[:])

        src_width, src_height = src_image.size
        canvas_width, canvas_height = canvas_image.size

        for y in range(src_height):
            for x in range(src_width):
                canvas_x = x + offset_x
                canvas_y = (canvas_height - y - 1) - offset_y 

                if 0 <= canvas_x < canvas_width and 0 <= canvas_y < canvas_height:
                    src_index = ((src_height - y - 1) * src_width + x) * 4
                    canvas_index = (canvas_y * canvas_width + canvas_x) * 4

                    canvas_pixels[canvas_index:canvas_index + 4] = src_pixels[src_index:src_index + 4]

        canvas_image.pixels = canvas_pixels
        canvas_image.update()

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

classes = [
AddBakeMap,
RemoveBakeMap,
ExportTextures,
CollapseLayer,
CombineWithLayerBelowOperator,
CombineAllLayersOperator,
SnapshotLayer,
ResizeTexturePopup,
ResizeAllLayersPopup,
BAKING_OT_BakeTextures,
BakeMapPref,
GetFromSelected,
RemoveAllBakeObjects,
ExportORALayersOperator,
ImportORALayersOperator,
]
def register():
    for cls in classes:
        register_class(cls)
def unregister():
    for cls in reversed(classes):
        unregister_class(cls)