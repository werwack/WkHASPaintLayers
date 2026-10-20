import bpy
import re
import numpy as np
from contextlib import contextmanager
import mathutils
import uuid
from .has_enum import *
from mathutils import Matrix
import re

def shortid():
    #generate shorter id by checking used ids. Should not be a problem. It is assigned for each filter and each layer.
    usedids = list(bpy.context.scene.other_props.usedids)
    while True:
        id = str(uuid.uuid4()).replace('-', '')[:6]
        if id not in usedids:
            usedids.append(id)
            bpy.context.scene.other_props.usedids = ''.join(usedids)
            return id

def newimagename(layer_name = ""):
    # Get new image name by available
    part = get_material_collection()
    if not part:
        return 
    inlf = layer_name if layer_name else "Layer"
    base_name = f"{part.material.name}{inlf}"
    if bpy.data.images.get(base_name):
        number = 1
        while bpy.data.images.get(f"{base_name}_{number:02}"):
            number += 1
        image_name = f"{base_name}_{number:02}"
    else:
        image_name = base_name
    # Remove specific characters and spaces.
    result = image_name.replace(' ', '')
    result = re.sub(r'[^A-Za-z0-9]', '', result)
    return result

def newlayername(pref = ""):
    #Get layer name by available number
    part = get_material_collection()
    if not part:
        return 
    base_name = f"{pref} Layer"
    if pref == "Folder":
        base_name = pref
    number = 1
    existing_layer_names = {l.layer_name for l in part.layers}

    while True:
        layer_name = f"{base_name} {number:02}"
        if layer_name not in existing_layer_names:
            break
        number += 1

    return layer_name

def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

def CheckForEmpty():
    #Check if any layer is invalid
    part = get_material_collection()

    for index, layer in enumerate(part.layers):
        
        if layer.id == "empty":
            remove_by_id(layer.id)
            part.layers.remove(index)
    ids = get_all_ids_from_layers()

    for index, layer in enumerate(part.base_layers):
        if not layer.id in ids:
            part.base_layers.remove(index)
        if layer.get_layer():
            for si, sl in enumerate(get_layers(layer.get_layer().sub_layers)):
                if not sl.id in ids:
                    remove_by_id(sl.id)
                    sl.sub_layers.remove(si)
        else:
            part.base_layers.remove(index)

def remove_references(layer):
    # Remove all layer references by id 
    part = get_material_collection()
    remove_by_id(layer.id)

def remove_by_id(id):
    # Remove all layer references by id 
    part = get_material_collection()
    for i, l in enumerate(part.layers):
        for si, sl in enumerate(l.sub_layers):
            if sl.id == id:
                l.sub_layers.remove(i)
                break
    for i, l in enumerate(part.base_layers):
        if l.id == id:
            part.base_layers.remove(i)
            break
    for i, l in enumerate(part.layers):
        if l.id == id:
            part.layers.remove(i)
            break

def get_all_ids_from_layers():
    # Get layers id's
    part = get_material_collection()
    ids = []
    for index, layer in enumerate(part.layers):
        ids.append(layer.id)
    return ids

def remove_layer_ref(layers, id):
    # Remove layer reference in container
    for i, l in enumerate(layers):
        if l.id == id:
            layers.remove(i)
            return
    
def fixorder():
    # Fix layer order in current "Set\Part"
    part = get_material_collection()

    update_layers_index(part.layers)
    update_layers_index(part.base_layers)
    for l in get_layers(part.base_layers):
        if l:
            update_layers_index(l.sub_layers)

def update_layers_index(layers):
    # Update layer index in property to easy access in other operations
    for index, layer in enumerate(layers):
        layer.index = index

def get_material_collection():
    # Get material settings. Always referenced as "part"
    curscene = bpy.context.scene

    target_view_layer = curscene.view_layers[0]
    active_object = target_view_layer.objects.active

    mtlprops = curscene.material_props
    for ind, prop in enumerate(mtlprops):
        if prop:
            if prop.material == active_object.active_material:
                return prop
    return None

def getusedtypesinlayers(layers):
    # Get texture types used in existing layers
    usedtypes = []

    for type in getusedmaps():
        for layer in layers:
            if layer.texture_type == type[0]:
                
                usedtypes.append(type[0])

                break

    return usedtypes

def get_next_set_name():
    # Get unused name for Set (Set is a material settings collection)
    base_name = "Set"
    number = 1

    material_collection = bpy.context.scene.material_props

    existing_names = {mat.name for mat in material_collection}

    while f"{base_name}_{number:02}" in existing_names:
        number += 1

    return f"{base_name}_{number:02}"

def remap_value(value, in_min, in_max, out_min, out_max):
    return(((value - in_min) * (out_max - out_min)) / (in_max - in_min)) + out_min
    
def generate_filename(name_template, context, obj_name, mtl_name, file_name, set_name):
    # Generate texture name for exporting. Based on user input replace values by (object name) or (material name) etc.
    values = {
        'obj': obj_name,
        'mtl': mtl_name,
        'file': file_name,
        'set': set_name,
     }
    
    pattern = re.compile(r'\((.*?)\)')
    
    def replace_match(match):
        key = match.group(1)
        return values.get(key, f'({key})')
    
    file_name = pattern.sub(replace_match, name_template)
    
    return file_name

def find_node_by_name(self, node_tree, name):
    #get node by name in node tree. Used in shader updates. Usually these nodes are renamed in creation.
    for node in node_tree.nodes:
        if node.name == name:
            return node
        elif node.type == 'GROUP' and node.node_tree:
            found_node = self.find_node_by_name(node.node_tree, name)
            if found_node:
                return found_node
    return None

def next_power_of_two(x):
    # get power of two image size based on current value
    return 2**(x-1).bit_length()

def SelectTexture(texture_name):
    # Set selected layer using id. Select image texture to paint on.
    if not texture_name:
        texture_name = get_material_collection().layers[len(get_material_collection().layers)-1].image.name
    bpy.context.scene.selected_texture = texture_name
    texture = bpy.data.images.get(texture_name)
    if texture:
        bpy.context.scene.tool_settings.image_paint.canvas = texture
        if not texture.preview_ensure():
            texture.asset_generate_preview()
        if bpy.context.scene.tool_settings.image_paint.mode == 'MATERIAL':
            bpy.context.scene.tool_settings.image_paint.mode = 'IMAGE'                       

def SelectLayer(id):
    # Set selected layer using id. Select image texture to paint on.
    part = get_material_collection()
    layer = get_layer_by_id(id)
    part.selected_layer = id
    part.selected_alpha = False

    if layer.resource.image:
        SelectTexture(layer.resource.image.name)
        return
    bpy.context.scene.selected_texture = ""
    bpy.context.scene.tool_settings.image_paint.canvas = None

def lerp(a, b, t):
    return a + (b - a) * t

def can_be_added_to(layer):
    # Check if layer can be attached to anything
    part = get_material_collection()
    if part.addtofolder and not layer.attachedto or layer.attachedto == part.addtofolder:
        return True
    return False

def fraction_between(value, min_val, max_val):
    # simple math operation. Currently only used only in load values from Curve to Levels
    if max_val == min_val:
        return 0
    return (value - min_val) / (max_val - min_val)

def get_layer_by_id(id):
    # each layer has an ID, and we can get it using it
    part = get_material_collection()
    for l in part.layers:
        if l.id == id:
            return l
    return None

def reassign_layer(fromlist, tolist, id, parent = None):
    # Move layer from container to container using id 
    remove_layer_ref(fromlist, id)
    subl = tolist.add()
    subl.id = id
    get_layer_by_id(id).attachedto = parent.id if parent else ""

def get_links(node, socket):
    #Get saved links for socket
    node_tree = node.id_data
    socket = node.inputs[socket]
    saved_links = [(link.from_node, link.from_socket) for link in socket.links]
    return saved_links

def set_links(saved_links, socket):
    #Reconnect socket by saved links
    for from_node, from_socket in saved_links:
        node_tree = from_node.id_data  
        node_tree.links.new(from_socket, socket)

def clear_socket_links(node, index):
    # remove links from socket
    node_tree = node.id_data
    for link in node.inputs[index].links:
        node_tree.links.remove(link)

def get_layer_in_list(list, id):
    # Get Layer by id in container
    for item in list:
        if item.id == id:
            return item
    return None

def get_layer_below(inlist, id):
    lastind = -1
    for item in inlist:
        if item.id == id:
            
            foundlayer = inlist[lastind]
            part = get_material_collection()
            for layer in part.layers:
                if layer.id == foundlayer.id:

                    return layer
        lastind = item.index
    return None

def move_last_to_selected(inlist):
    # Used to move newly created layer to selected layer 
    part = get_material_collection()

    layer = get_layer_by_id(part.selected_layer)
    if layer:
        foundind= -1
        for i, ds in enumerate(inlist):
            if ds.id == layer.id:
                foundind = ds.index
        if not foundind == -1:
            inlist.move(len(inlist) - 1, foundind +1)
 
def get_selected_layer_index():
    part = get_material_collection()
    
    layer = get_layer_by_id(part.selected_layer)
    if layer:
        return layer.index

    selt = bpy.context.scene.selected_texture
    if selt:
        for layer in part.layers:
            if layer.resource.image:
                if selt == layer.resource.image.name:
                    return layer.index

    return -1

def is_selected(layer):
    # Check if layer is selected for UI 
    part = get_material_collection()
    selnm= ""
    sameimg = False
    selected =False
    if part.selected_layer:
        selected = layer.id == part.selected_layer
    if layer.resource.image:
        selnm = layer.resource.image.name
        sameimg = bpy.context.scene.selected_texture == layer.resource.image.name
    selectedalpha = False
    if selected:
        selectedalpha = part.selected_alpha
    return selected, selectedalpha, selnm, sameimg

def get_image_histogram(image_name, num_bins=20, sample_rate=0.25):
    # Calculate custom histogram for image as string
    image = bpy.data.images.get(image_name)
    if image is None or not image.pixels:
        return ""
    
    width, height = image.size
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape((height, width, 4))
    normalized_values = (pixels.flatten() * (num_bins - 1)).astype(int)
    histogram = np.bincount(normalized_values, minlength=num_bins)
    histogram = histogram / histogram.sum()
    
    return ','.join(map(str, histogram))

def any_active_filter(filters):
    # Check if layer has any active filter or any filter at all.
    if not filters:
        return False
    for filter in filters:
        if filter.in_use:
            return True
    return False

def parse_histogram_string(histogram_str):
    # Convert custom histogram string of values to split values
    return [float(value) for value in histogram_str.split(',')]

def get_histogram(texture_name):
    # Get Custom histogram by image name
    for hist in bpy.context.scene.other_props.HistogramRefs:
        if hist.texture_name == texture_name:
            return hist.histogram
    return ""

def set_histogram(texture_name, histogram):
    # Assign custom histogram to image
    for hist in bpy.context.scene.other_props.HistogramRefs:
        if hist.texture_name == texture_name:
            hist.histogram = histogram
            return
    hist = bpy.context.scene.other_props.HistogramRefs.add()
    hist.texture_name = texture_name
    hist.histogram = histogram
    
def update_hist_display(texture_name):
    # Get image and update custom histogram for "Levels" filter display
    name = ".HAS_SceneProperties"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)
    histrefs = bpy.context.scene.other_props.HistogramRefs

    for hist in histrefs:
        if hist.texture_name == texture_name:
            
            levelvis = get_node_by_name(node_group, texture_name)
            if not levelvis:
                levelvis = create_node(node_group, 'ShaderNodeFloatCurve' , -600,0, "", "")
                levelvis.name = hist.texture_name
            if levelvis:
                curve = levelvis.mapping.curves[0]
                for i, point in enumerate(parse_histogram_string(hist.histogram)):
                    if len(curve.points)>i:
                        curve.points[i].location = (i/19, point*1.0)
                    else:
                        curve.points.new(i/19, point*1.0)
                levelvis.mapping.update()

def check_socket(sockets, name):
    # Check if socket exists
    if name in sockets:
        return True
    return False

def check_for_sockets(sockets, names):
    # Check if sockets exists
    for name in names:
        if not check_socket(sockets, name):
            return False
    return True

def check_filter_sockets(filter, filternode):
    # Check if filter node contains enough sockets. Generally used for Custom Filter that can be set by user.
    if len(filternode.inputs)<=filter.socket_in:
        filter.socket_in = 0
    if len(filternode.outputs)<=filter.socket_out:
        filter.socket_out = 0

def getusedmaps():
    # Get used maps and return as Enum.
    types = []
    part = get_material_collection()
    if part:
        used = part.used_maps

        if used.Diffuse:
            types.append(('DIFFUSE', 'Diffuse', 'Texture as Diffuse'))
        if used.Roughness:
            types.append(('ROUGHNESS', 'Roughness', 'Texture as Roughness'))
        if used.Metallic:
            types.append(('METALLIC', 'Metallic', 'Texture as Metallic'))
        if used.Normal:
            types.append(('NORMAL', 'Normal', 'Texture as Normal'))
        if used.Height:
            types.append(('HEIGHT', 'Height', 'Texture as Height'))
        if used.Emission:
            types.append(('EMISSION', 'Emission', 'Texture as Emission'))
        if used.Alpha:
            types.append(('ALPHA', 'Alpha', 'Texture as Alpha'))
        if used.AO:
            types.append(('AO', 'Ambient Occlusion', 'Texture as Ambient Occlusion'))
        if used.Alpha:
            types.append(('CUSTOM', 'Custom', 'Custom texture'))

        return types
    return None

def getusedtypes():
    # Get Used types by existing layers
    usedtypes = []
    part = get_material_collection()
    usedtypes = getusedtypesinlayers(part.layers)
    for layer in part.layers:
        newused = getusedtypesinlayers(get_layers(layer.sub_layers))
        for tp in newused:
            if not tp in usedtypes:
                usedtypes.append(tp)
    return usedtypes

def getlabel(find_type):
    # Get Name of a type using used maps. (Diffuse, Roughness, Alpha, etc.)
    texture_type_dict = {item[0]: item[1] for item in getusedmaps()}
    texture_label = texture_type_dict.get(find_type, "")
    return texture_label

def gettexturelabel(find_type):
    # Get Name of a type using Enum. (Diffuse, Roughness, Alpha, etc.)
    texture_type_dict = {item[0]: item[1] for item in TEXTURE_TYPE}
    texture_label = texture_type_dict.get(find_type, "")
    return texture_label

def fix_image_colors_by_alpha(image_name):
    # Get image and fix alpha to cleaner projected image. Still not fixing it properly, and it's slow.
    image = bpy.data.images.get(image_name)

    if image is None:
        return
    if image.channels < 4:
        return

    pixels = np.array(image.pixels[:])  
    pixels = pixels.reshape((-1, 4)) 
    
    rgb = pixels[:, :3] 
    alpha = pixels[:, 3]

    rgb_corrected = np.where(alpha[:, None] > 0, rgb / alpha[:, None], rgb)
    rgb_corrected[alpha == 0] = [1.0, 1.0, 1.0]
    pixels[:, :3] = rgb_corrected
    
    image.pixels = pixels.flatten()
    
    image.update()

def create_image_node(node_group, img, resource = None):
    # Create image node in shader editor and attach mapping assigning settings
    part = get_material_collection()
    links = node_group.links
    image_node = create_node(node_group,'ShaderNodeTexImage', -600,0, "img", img)
    
    image_node.interpolation= part.texture_filtering

    attribute = create_node(node_group,'ShaderNodeUVMap', -600,0, "", "")
    attribute.uv_map = part.uvs

    mapping = create_node(node_group,'ShaderNodeMapping', -600,0, "", "")
    if resource:
        set_default(mapping, "Location", (resource.mapx,resource.mapy,0.0))
        set_default(mapping, "Rotation", (0.0,0.0,resource.maprot))
        set_default(mapping, "Scale", (resource.mapscalex,resource.mapscaley,1.0))
        resource.mapping_node.set_node_reference(mapping)
    links.new(attribute.outputs[0],mapping.inputs[0])
    links.new(mapping.outputs[0],image_node.inputs[0])
    if part.uvs:
        attribute = create_node(node_group,'ShaderNodeAttribute', -600,0, "", "")
        attribute.attribute_name = part.uvs
        links.new(attribute.outputs[1],mapping.inputs[0])
    return image_node

def get_layers(base_layers):
    layers = []
    for bl in base_layers:
        l = bl.get_layer()
        if l:
            layers.append(bl.get_layer())

    return layers

def create_normal_blend_group():
    # Node group for Normal blending
    name = ".HAS_BlendNormals"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]

        node_group.nodes.clear()
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)
    
    create_socket(node_group, "Fac", 'float', True)
    create_socket(node_group, "Color1", 'color', True)
    create_socket(node_group, "Color2", 'color', True)

    create_socket(node_group, "Color", 'color', False)

    Note(node_group)
    input_node = node_group.nodes.new(type='NodeGroupInput')
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    input_node.location = (-500, 0)
    output_node.location = (500, 0)
    math_nodeA = node_group.nodes.new('ShaderNodeVectorMath')
    math_nodeA.operation = 'ADD'
    math_nodeA.location = (0,0)
    math_nodeM = node_group.nodes.new('ShaderNodeVectorMath')
    math_nodeM.operation = 'MULTIPLY'
    math_nodeM.location = (-300,0)
    math_nodeN = node_group.nodes.new('ShaderNodeVectorMath')
    math_nodeN.operation = 'NORMALIZE'
    math_nodeN.location = (300,0)

    node_group.links.new(input_node.outputs['Color1'], math_nodeA.inputs[0])
    node_group.links.new(input_node.outputs['Color2'], math_nodeM.inputs[0])
    node_group.links.new(math_nodeM.outputs[0], math_nodeA.inputs[1])

    node_group.links.new(input_node.outputs['Fac'], math_nodeM.inputs[1])
    node_group.links.new(math_nodeA.outputs[0], math_nodeN.inputs[0])
    node_group.links.new(math_nodeN.outputs[0], output_node.inputs[0])

    return node_group

def mask_by_color_node(filter, layer):
    # Node group for "Select Color" filter
    node_group = None
    name = f".HAS_SelectColor"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        return node_group
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    node_group.nodes.clear()
    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Sample", 'color', True)
    create_socket(node_group, "Output Color", 'color', True)
    create_socket(node_group, "Threshold", 'float', True)
    Note(node_group)
    
    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)

    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)

    set_minmax(node_group, "Threshold", 0.0, 1.0)
    set_default(node_group, "Threshold", 0.1)
    set_default(node_group, "Output Color",(1.0,1.0,1.0,1.0))

    mix = create_node(node_group,'ShaderNodeMixRGB', -200,0, "mix", 'MIX')
    set_default(mix, 1, (0.0,0.0,0.0,0.0))
    sepimg = create_node(node_group,'ShaderNodeSeparateRGB', -200,0, "", '')
    sepcol = create_node(node_group,'ShaderNodeSeparateRGB', -200,0, "", '')

    comparer = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'COMPARE')
    compareg = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'COMPARE')
    compareb = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'COMPARE')

    mult1 = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'MULTIPLY')
    mult2 = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'MULTIPLY')

    blendalpha = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'MINIMUM')

    links = node_group.links

    links.new(input_node.outputs["Color"],sepimg.inputs[0])
    links.new(input_node.outputs["Sample"],sepcol.inputs[0])

    links.new(sepimg.outputs[0],comparer.inputs[0])
    links.new(sepimg.outputs[1],compareg.inputs[0])
    links.new(sepimg.outputs[2],compareb.inputs[0])
    
    links.new(sepcol.outputs[0],comparer.inputs[1])
    links.new(sepcol.outputs[1],compareg.inputs[1])
    links.new(sepcol.outputs[2],compareb.inputs[1])

    links.new(input_node.outputs["Threshold"],comparer.inputs[2])
    links.new(input_node.outputs["Threshold"],compareg.inputs[2])
    links.new(input_node.outputs["Threshold"],compareb.inputs[2])

    links.new(comparer.outputs[0],mult1.inputs[0])
    links.new(compareg.outputs[0],mult1.inputs[1])
    links.new(mult1.outputs[0],mult2.inputs[0])
    links.new(compareb.outputs[0],mult2.inputs[1])

    links.new(mult2.outputs[0],blendalpha.inputs[0])

    links.new(input_node.outputs["Alpha"],blendalpha.inputs[1])

    links.new(blendalpha.outputs[0],mix.inputs[0])
    links.new(input_node.outputs["Output Color"],mix.inputs[2])

    links.new(mix.outputs[0],output_node.inputs["Color"])

    return node_group

def mask_gen_node(filter, layer, part):
    # Node group for "Mask Generator" filter
    node_group = None
    name = getfiltergroupname(filter)
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
    if not node_group:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Color", 'color', False)

    for node in  node_group.nodes:
        safe = False
        for itm in MASKITEMS:
            maskitem = filter.maskgen.get_item(itm) 
            if maskitem:
                if maskitem.levels.levels_node.get_node() == node:
                    safe = True
        if not safe:
            node_group.nodes.remove(node)

    Note(node_group)
    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)

    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)

    links = node_group.links

    lastmaxconnection=input_node.outputs[0]
    
    lastmaxconnection = None
    filter.node_tree = node_group
    image_node = create_image_node(node_group, filter.resource.image, resource = filter.resource)
    
    levels_node = levels(node_group, image_node.outputs[0], filter.levels, id =filter.id)
    filter.node_name = levels_node.name
    filter.resource.levels.levels_node.set_node_reference(levels_node)
    #filter.resource.mapping_node.set_node_reference(mappingnode)

    blendalpha = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'SUBTRACT')
    prevao = None
    prevcurve = None
    prevpos = None
    prevobn = None
    for itm in MASKITEMS:
        maskitem = filter.maskgen.get_item(itm[0]) 
        if maskitem:
            if maskitem.image:
                masknode = create_image_node(node_group, maskitem.image)
                
                lastcol = masknode.outputs[0]
            else:
                masknode = create_node(node_group, itm[1], -600,0, "", "")
                if itm[0] == "Curvature":
                    masknode.inside = True

                lastcol = masknode.outputs[itm[2]]
            if itm[0] == "Position":
                Dot = create_node(node_group,'ShaderNodeVectorMath', -600,0, "op", "DOT_PRODUCT")
                set_default(Dot,1,(0.0,0.0,1.0))
                links.new(lastcol,Dot.inputs[0])
                lastcol = Dot.outputs["Value"]
            if itm[0] == "AO":
                prevao = levels(node_group, lastcol, maskitem.levels).outputs[0]
            if itm[0] == "Curvature":
                prevcurve = levels(node_group, lastcol, maskitem.levels).outputs[0]
            if itm[0] == "Position":
                prevpos = levels(node_group, lastcol, maskitem.levels).outputs[0]
            if itm[0] == "Object Normal":
                prevobn = levels(node_group, lastcol, maskitem.levels).outputs[0]
    if prevao and prevcurve and prevpos and prevobn:
        aocurve = create_node(node_group, 'ShaderNodeMixRGB', -600,0, "mix", "SUBTRACT")
        set_default(aocurve,0,1.0)
        links.new(prevao,aocurve.inputs[1])
        links.new(prevcurve,aocurve.inputs[2])
        acpos = create_node(node_group, 'ShaderNodeMixRGB', -600,0, "mix", "SUBTRACT")
        set_default(acpos,0,1.0)
        links.new(aocurve.outputs[0],acpos.inputs[1])
        links.new(prevpos,acpos.inputs[2])
        
        lastmix = create_node(node_group, 'ShaderNodeMixRGB', -600,0, "mix", "SUBTRACT")
        set_default(lastmix,0,1.0)
        links.new(levels_node.outputs[0],lastmix.inputs[1])
        links.new(acpos.outputs[0],lastmix.inputs[2])
        lastcol = lastmix.outputs[0]
        links.new(lastcol,output_node.inputs['Color'])
    return node_group

def getlayergroupname(layer):
    if layer:
        return f".HAS_{layer.id}_layer"
    return f"Undifined_layer"

def getfiltergroupname(filter):
    if filter:
        if filter.id:
            return f".HAS_{filter.id}_filter"
    return f"Undifined_filter"

def getmaterialgroupname(part):
    return f"HAS_{part.material.name}_Material"

def create_layer_node(layer, pbr = False):
    # Paint layer node group
    part = get_material_collection()
    name = getlayergroupname(layer)
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes(node_group, layer.filters)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)
    pth = layer.blend_mode== "PASS"

    active_filters = any_active_filter(layer.filters)

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', False)

    Note(node_group)

    img = layer.resource.image
    links = node_group.links

    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)

    lastconnection = None
    lastclipmaskconnection = None

    if img:
        image_node = create_image_node(node_group, img, resource = layer.resource)
        lastconnection = image_node.outputs[0]
        if layer.texture_type == "NORMAL" and layer.resource.image.colorspace_settings.name == "sRGB":
            gamma = create_node(node_group,'ShaderNodeGamma', -200,0, "", '')
            set_default(gamma,1, 0.454)
            lastconnection = gamma.outputs[0]
            links.new(image_node.outputs[0], gamma.inputs[0])
    math_node = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'MULTIPLY')

    initialmask = None
    if layer.mask:
        initialmask = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'MULTIPLY')
        initialmask.name = "InitialMask"
        initialmask.inputs[0].name = "MaskValue"
        set_default(initialmask, 0, 1.0 if layer.mask_value else 0.0)
        set_default(initialmask, 1, 1.0)
        #layer.mask_value.set_socket_reference(initialmask.inputs[1])
    #else:
        #layer.mask_value.set_socket_reference(math_node.inputs[0])

    set_default(math_node, 0, 1.0)    
    set_default(math_node, 1, layer.opacity)
    math_node.inputs[1].name = 'OpSock'
    layer.opacity_socket.set_socket_reference(math_node.inputs[1])
    
    if layer.blend_mode == "COMBNRM":
        mix_node = create_node(node_group, 'ShaderNodeGroup' , -600,0, "cus", ".HAS_BlendNormals")
    else:
        if not pth:
            mix_node= create_node(node_group,'ShaderNodeMixRGB', 0,0, "mix", layer.blend_mode)
        else:
            mix_node= create_node(node_group,'ShaderNodeMixRGB', 0,0, "mix", "MIX")

        mix_node.use_clamp = True
    
    mix_node.inputs[2].name = "ColSock"
    layer.resource.default_color_socket.set_socket_reference(mix_node.inputs["ColSock"])
    height_remap = None

    # if img:
    #     lastconnection = image_node.outputs[1]
    #     lastclipmaskconnection = image_node.outputs[0]

    if not img:
        set_default(mix_node, 'ColSock', layer.resource.default_color)

    if layer.texture_type == "HEIGHT" and img and layer.blend_mode == 'ADD':
        height_remap= create_node(node_group,'ShaderNodeMapRange', 0,0, "", "")
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
        filnode = create_node(node_group,'ShaderNodeGroup', -200,-200, "cus", layer_filter(layer).name)
        set_default(filnode, 'Color', layer.resource.default_color)
        set_default(filnode, 'Alpha', 1.0)
        if lastconnection:
            links.new(lastconnection, filnode.inputs['Color'])
        if lastclipmaskconnection:
            links.new(lastclipmaskconnection, filnode.inputs['Alpha']) 
        lastconnection = filnode.outputs["Color"]
        lastclipmaskconnection = filnode.outputs["Alpha"]
        layer.resource.default_color_socket.set_socket_reference(filnode.inputs["Color"])

    if not lastclipmaskconnection:
        if img:
            lastclipmaskconnection = image_node.outputs[1]

    links.new(input_node.outputs['Color'], mix_node.inputs[1])
    links.new(mix_node.outputs[0], output_node.inputs['Color'])
    if lastconnection:
        links.new(lastconnection, mix_node.inputs[2])
    if lastclipmaskconnection:

        links.new(lastclipmaskconnection, math_node.inputs[0])

    alphablend= create_node(node_group,'ShaderNodeMixRGB', 0,0, "mix", "SCREEN")
    set_default(alphablend,0,1.0)
    if lastconnection:
        links.new(lastconnection, mix_node.inputs[2])
    
    links.new(math_node.outputs[0], mix_node.inputs['Fac'])

    links.new(math_node.outputs[0], alphablend.inputs[1])
    links.new(input_node.outputs["Alpha"], alphablend.inputs[2])

    links.new(alphablend.outputs[0], output_node.inputs["Alpha"])

    return node_group

def simple_layer(name, image, opacity, blend_mode, default_color, mixmode = False, resource = None):
    # Simple node group for layers
    part = get_material_collection()
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes_ignoring(node_group)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)
    pth = blend_mode== "PASS"

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', False)

    Note(node_group)

    img = image
    links = node_group.links

    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)

    lastconnection = None
    lastclipmaskconnection = None

    if img:
        image_node = create_image_node(node_group, img, resource = resource)
    math_node = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'MULTIPLY')
    math_node.name = 'Opacity'
    set_default(math_node, 0, 1.0)    
    set_default(math_node, 1, opacity)
    math_node.inputs[1].name = 'OpSock'

    if blend_mode == "COMBNRM":
        mix_node = create_node(node_group, 'ShaderNodeGroup' , -600,0, "cus", ".HAS_BlendNormals")
    else:
        if not pth:
            mix_node= create_node(node_group,'ShaderNodeMixRGB', 0,0, "mix", blend_mode)
        else:
            mix_node= create_node(node_group,'ShaderNodeMixRGB', 0,0, "mix", "MIX")

        mix_node.use_clamp = True
    mix_node.name = "Color"
    mix_node.inputs[2].name = "ColSock"

    if img:
        lastconnection = image_node.outputs[1]
        lastclipmaskconnection = image_node.outputs[0]
    else:
        set_default(mix_node, 'ColSock', default_color)

    if img:
        lastconnection = image_node.outputs[0]
        lastclipmaskconnection = image_node.outputs[1]
    if not lastclipmaskconnection:
        if img:
            lastclipmaskconnection = image_node.outputs[1]

    links.new(input_node.outputs['Color'], mix_node.inputs[1])
    links.new(mix_node.outputs[0], output_node.inputs['Color'])
    if lastconnection:
        links.new(lastconnection, mix_node.inputs[2])
    if lastclipmaskconnection:
        links.new(lastclipmaskconnection, math_node.inputs[0])

    alphablend= create_node(node_group,'ShaderNodeMixRGB', 0,0, "mix", "SCREEN")
    set_default(alphablend,0,1.0)
    if lastconnection:
        links.new(lastconnection, mix_node.inputs[2])
    
    links.new(math_node.outputs[0], mix_node.inputs['Fac'])

    links.new(math_node.outputs[0], alphablend.inputs[1])
    links.new(input_node.outputs["Alpha"], alphablend.inputs[2])

    links.new(alphablend.outputs[0], output_node.inputs["Alpha"])

    return node_group

def layer_filter(layer, multi = False):
    #Filter nodegroup assigned to layer. 
    if not layer:
        return None
    part = get_material_collection()

    name = f"{getlayergroupname(layer)}_filters"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        if layer.filters:
            clear_nodes(node_group, layer.filters)
        else:
            simple_clear_node(node_group)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)
    
    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Alpha", 'float', False)
    create_socket(node_group, "Type", 'float', True)
    Note(node_group)
    group_input = node_group.nodes.new(type='NodeGroupInput')
    group_input.location = (-500, 0)
    group_output = node_group.nodes.new(type='NodeGroupOutput')
    group_output.location = (500, 0)

    if not check_for_sockets(group_input.outputs, ["Color","Alpha"]) or not check_for_sockets(group_output.inputs, ["Color","Alpha"]):
        return node_group

    lastcolorconnection = group_input.outputs["Color"]
    lastalphaconnection = group_input.outputs["Alpha"]
    links = node_group.links

    if multi and check_socket(group_input.outputs, "Type"):
        count = -1
        for ch in getusedmaps():
            count = count+1
            type_switch_node = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", type_switch().name)
            type_switch_node.name = ch[0]
            if "Type" in group_input.outputs:
                links.new(group_input.outputs["Type"], type_switch_node.inputs['Type'])
            set_default(type_switch_node, "Compare", float(count))

    count = 0

    for channel in ["COLOR","ALPHA"]:
        lastconnection = group_input.outputs["Color"] if channel == "COLOR" else group_input.outputs["Alpha"]
        for filter in layer.filters:
            if not filter.name:
                continue
            if not channel == filter.connection_type:
                continue
            alphafiller = False
            ignoresetup = False
            ignoremix = False
            assignalpha = False
            templast = None
            filter.layer_in = layer.id
            if filter.in_use:
                count = count+1
                filternodename = None
                filternode = None
                
                if not filternodename:
                    filternodename = f"{getdescription(FILTERS, filter.name)}"
                Op = None
                optype = ''
                opacitymult= None
                blendfilter = None
                custominput= None
                custominputalpha= None

                if filter.name == 'CUSTOM':
                    if not filter.custom_node_tree_p:
                        continue
                    Op = f"{filter.custom_node_tree_p.name}"
                    optype = 'cus'
                elif filter.name == "PAINT":

                    lrgroup = simple_layer(f'.HAS_{filter.id}_paint', filter.resource.image, filter.opacity, filter.blend_mode, (0.0,0.0,0.0,0.0), resource = filter.resource)
                    filternode = create_node(node_group, 'ShaderNodeGroup', -200,-200, "cus", lrgroup.name)
                    filter.node_name = filternode.name
                    links.new(lastconnection, filternode.inputs[0])
                    links.new(lastalphaconnection, filternode.inputs[1])
                    filter.opacity_socket.set_socket_reference(get_socket_from_name(lrgroup, "Opacity", "Opacity"))
                    templast = filternode.outputs[0]
                    lastconnection = filternode.outputs[0]
                    ignoresetup = True
                    ignoremix = True
                    lastalphaconnection = filternode.outputs[1]
                elif filter.name == "FILL":
                    lrgroup = simple_layer(f'.HAS_{filter.id}_fill', filter.resource.image, filter.opacity, filter.blend_mode, filter.resource.default_color, resource = filter.resource)
                    filternode = create_node(node_group, 'ShaderNodeGroup', -200,-200, "cus", lrgroup.name)
                    filter.node_name = filternode.name
                    links.new(lastconnection, filternode.inputs[0])
                    links.new(lastalphaconnection, filternode.inputs[1])
                    filter.resource.default_color_socket.set_socket_reference(get_socket_from_name(lrgroup, "Color", "ColSock"))
                    filter.opacity_socket.set_socket_reference(get_socket_from_name(lrgroup, "Opacity", "OpSock"))
                    templast = filternode.outputs[0]
                    
                    ignoresetup = True
                    ignoremix = True
                    assignalpha= False
                    lastalphaconnection = filternode.outputs[1]
                elif filter.name == "LEVELS":
                    filternode = levels(node_group, lastconnection, filter.levels, filter.id)
                    filternodename = filter.node_name
                    filter.node_name = filternode.name
                    templast = filternode.outputs["Color"]
                    ignoresetup = True
                elif filter.name == "MASKCOLOR":
                    Op = f"{mask_by_color_node(filter, layer).name}"
                    optype = 'cus'
                    image_node = create_image_node(node_group, filter.resource.image, resource = filter.resource)
                    filternode = node_group.nodes.get(filter.node_name)
                    if not filternode:
                        filternode = create_node(node_group, filternodename, -200,-200*count, optype, Op)
                    filter.node_name = filternode.name

                    custominput = image_node.outputs[0]
                    custominputalpha=image_node.outputs[1]
                elif filter.name == "MASKGEN":
                    Op = f"{mask_gen_node(filter, layer, part).name}"
                    optype = 'cus'
                elif filter.name == "LIGHT":
                    nqdd = light_node(filter)
                    Op = nqdd.name
                    
                    filter.displnode.set_node_reference(get_node_by_name(nqdd, "fs_LightNormal"))
                    optype = 'cus'
                    alphafiller= True
                elif filter.name == "BLUR":
                    Op = blur_node(filter).name
                    optype = 'cus'
                    assignalpha= True
                elif filter.name == "SNAPSHOT":
                    Op = snapshot_node(filter).name
                    optype = 'cus'
                    assignalpha= True
                    
                if filternodename:
                    
                    if not ignoresetup:
                        filternode = node_group.nodes.get(filter.node_name)
                        if filternode:
                            if filternode.type == 'GROUP' and not filternode.node_tree:
                                filternode = None
                        if not filternode:
                            filternode = create_node(node_group, filternodename, -200,-200*count, optype, Op)
                            filter.node_name = filternode.name
                            
                        else:
                            filternode.location = (-200,-200*count)

                        clear_node_socket_connections(filternode)

                        check_filter_sockets(filter, filternode)

                        if filternode.inputs:
                            if "Color" in filternode.inputs:
                                links.new(lastconnection, filternode.inputs["Color"])
                            else:
                                if filter.socket_in:
                                    links.new(lastconnection, filternode.inputs[filter.socket_in])
                                else:
                                    links.new(lastconnection, filternode.inputs[0])

                        if filternode.outputs:
                            if filter.socket_out:
                                templast = filternode.outputs[filter.socket_out]
                            else:
                                templast = filternode.outputs[0]
                        else:
                            continue
                    if not ignoremix:
                        
                        vldmode = "MIX" if filter.blend_mode == "PASS" or filter.blend_mode =="COMBNRM" else filter.blend_mode
                        blendfilter = create_node(node_group,'ShaderNodeMixRGB', -200,0, "mix", vldmode)
                        blendfilter.inputs[0].default_value = filter.opacity
                        blendfilter.inputs[0].name = "Opacity"
                        
                        links.new(lastconnection, blendfilter.inputs[1])
                        links.new(templast, blendfilter.inputs[2])
                        if opacitymult:
                            links.new(opacitymult.outputs[0], blendfilter.inputs[0])
                        lastconnection = blendfilter.outputs[0]
                        
                        blendfilter.name = filter.id
                        filter.mixnode = blendfilter.name
                        filter.opacity_socket.set_socket_reference(blendfilter.inputs[0])
                    else:
                        lastconnection = filternode.outputs[0]
                if not filternode:
                    continue
                if channel == "COLOR" and alphafiller:
                    alpbl = create_node(node_group,'ShaderNodeMixRGB', -200,0, "mix", "MIX")
                    set_default(alpbl, "Fac", filter.opacity)
                    set_default(alpbl, 2, (1.0,1.0,1.0,1.0))

                    links.new(lastalphaconnection, alpbl.inputs[1])
                    lastalphaconnection = alpbl.outputs[0]
               
                if channel == "COLOR":
                    lastcolorconnection = lastconnection   
                if assignalpha:
                    links.new(lastalphaconnection, filternode.inputs["Alpha"])
                    lastalphaconnection = filternode.outputs["Alpha"]
                if channel == "ALPHA":
                    lastalphaconnection = lastconnection

                if blendfilter:
                    ntypesw = get_node_by_name(node_group, filter.affect_channels)
                    if ntypesw:
                        opfis = create_node(node_group,'ShaderNodeMath', -200,0, "op", "MULTIPLY")
                        set_default(opfis, 1, filter.opacity)
                        links.new(ntypesw.outputs['Result'], opfis.inputs[0])
                        links.new(opfis.outputs[0], blendfilter.inputs[0])
                        opfis.name = f"{filter.id}_op"
                        opfis.inputs[1].name = 'opacity'
                        filter.opacity_socket.set_socket_reference(opfis.inputs[1])
                if custominput:
                    links.new(custominput, filternode.inputs["Color"])
                if custominputalpha:
                    links.new(custominputalpha, filternode.inputs["Alpha"])

    links.new(lastcolorconnection, group_output.inputs[0])
    links.new(lastalphaconnection, group_output.inputs[1])

    return node_group

def get_folder_nodegroup(folder_layer, pbr = False):
    part = get_material_collection()
    name = f"{getlayergroupname(folder_layer)}"
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    else:
        return create_pbr_nodegroup(folder_layer) if pbr else create_folder_nodegroup(folder_layer)
    
def create_folder_nodegroup(folder_layer, pbr = False):
    # Folder layer node group that contains other layers.
    part = get_material_collection()
    name = f"{getlayergroupname(folder_layer)}"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes(node_group, folder_layer.filters)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Alpha", 'float', False)
    create_socket(node_group, "Type", 'float', True)

    Note(node_group)
    group_input = node_group.nodes.new(type='NodeGroupInput')
    group_input.location = (-500, 0)
    group_output = node_group.nodes.new(type='NodeGroupOutput')
    group_output.location = (500, 0)
    
    links = node_group.links
    count = -1

    lastconnection = group_input.outputs['Color']

    prevnodes = []
    alsockets = []
    lrs = get_layers(folder_layer.sub_layers)
    
    for type in getusedtypes():
        prev_node = None

        for index, layer in enumerate(lrs):

            if layer.use_layer and type==layer.texture_type:
                
                count = count+1
                
                l_group = create_layer_node(layer)
                layer_node = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", l_group.name)

                if prev_node:
                    links.new(prev_node.outputs['Color'], layer_node.inputs['Color'])
                    links.new(prev_node.outputs['Alpha'], layer_node.inputs['Alpha'])
                if "Type" in layer_node.inputs:
                    links.new(group_input.outputs['Type'], layer_node.inputs['Type'])
                prev_node = layer_node
        
        if prev_node:
            prevnodes.append(prev_node)
    if prev_node:    
        links.new(prev_node.outputs['Color'], group_output.inputs['Color'])
        links.new(prev_node.outputs['Alpha'], group_output.inputs['Alpha'])
    else:
        links.new(group_input.outputs['Color'], group_output.inputs['Color'])
        links.new(group_input.outputs['Alpha'], group_output.inputs['Alpha'])
    prsef = None
    count = -1
    type_switch_node = None
    lastcol = None
    lastcolal = None
    for pren in prevnodes:
        count = count+1
        type_switch_node = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", type_switch().name)
        links.new(group_input.outputs["Type"], type_switch_node.inputs['Type'])
        set_default(type_switch_node, "Compare", float(count))
        links.new(pren.outputs["Color"], type_switch_node.inputs['Color'])
        links.new(pren.outputs["Alpha"], type_switch_node.inputs['Alpha'])
        if prsef:
            links.new(prsef.outputs["Color"], type_switch_node.inputs['PrevColor'])
            links.new(prsef.outputs["Alpha"], type_switch_node.inputs['PrevAlpha'])
        prsef = type_switch_node
    if type_switch_node:

        lastcol = type_switch_node.outputs["Color"]
        lastcolal = type_switch_node.outputs["Alpha"]
        folder_layerfinm = layer_filter(folder_layer, multi = True).name
        if folder_layerfinm:
            folder_layerfilnodegroup = create_node(node_group,'ShaderNodeGroup', -200,-200, "cus", folder_layerfinm)
            links.new(lastcol, folder_layerfilnodegroup.inputs['Color'])
            links.new(lastcolal, folder_layerfilnodegroup.inputs['Alpha'])
            links.new(group_input.outputs['Type'], folder_layerfilnodegroup.inputs['Type'])
            lastcol = folder_layerfilnodegroup.outputs["Color"]
            lastcolal = folder_layerfilnodegroup.outputs["Alpha"]

    mix = create_node(node_group,'ShaderNodeMixRGB', -200,-200, "mix", folder_layer.blend_mode)
    blenda = create_node(node_group,'ShaderNodeMixRGB', -200,-200, "mix", "SCREEN")
    set_default(blenda, 'Fac', 1.0)
    set_default(mix, 'Fac', folder_layer.opacity)
    folder_layer.opacity_socket.set_socket_reference(mix.inputs['Fac'])
    if lastcol:
        links.new(group_input.outputs['Color'], mix.inputs[1])
        links.new(lastcol, mix.inputs[2])
        links.new(group_input.outputs['Alpha'], blenda.inputs[1])
        links.new(lastcolal, blenda.inputs[2])

        links.new(lastcolal, mix.inputs[0])

        lastcol = mix.outputs[0]
        lastcolal = blenda.outputs[0]
        links.new(lastcol, group_output.inputs['Color'])
        links.new(lastcolal, group_output.inputs['Alpha'])

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

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Alpha", 'float', False)
    create_socket(node_group, "Type", 'float', True)

    Note(node_group)
    group_input = node_group.nodes.new(type='NodeGroupInput')
    group_input.location = (-500, 0)
    group_output = node_group.nodes.new(type='NodeGroupOutput')
    group_output.location = (500, 0)
    
    links = node_group.links
    
    lastconnection = group_input.outputs['Color']

    count = -1
    sockets = []
    alsockets = []
    lrs = get_layers(folder_layer.sub_layers)
    sourceimg = create_image_node(node_group, folder_layer.resource.image, resource = folder_layer.resource)
    mpng = get_node_by_name(node_group, "Mapping")
    srinm = sourceimg.outputs[1]
    folder_layerfinm = layer_filter(folder_layer, multi = True).name
    if folder_layerfinm:
        folder_layerfilnodegroup = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", folder_layerfinm)
        links.new(group_input.outputs["Type"], folder_layerfilnodegroup.inputs["Type"])
        links.new(sourceimg.outputs[1], folder_layerfilnodegroup.inputs["Alpha"])
        srinm = folder_layerfilnodegroup.outputs["Alpha"]
    for type in getusedtypes():
        prev_node = None

        for index, layer in enumerate(lrs):
            filnodegroup = None
            if layer.use_layer and type==layer.texture_type:
                layer_node = None
                count = count+1

                if layer.filters:
                    finm = layer_filter(layer, multi = True).name
                    if finm:
                        filnodegroup = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", finm)
                image = None
                mixrgb = create_node(node_group,'ShaderNodeMixRGB', -200,count*-200, "mix", layer.blend_mode)
                opacitynode = create_node(node_group,'ShaderNodeMath', -200,count*-200, "op", "MULTIPLY")
                opacitynode.inputs[1].name = "OpSock"
                if layer.resource.image:
                    image = create_image_node(node_group, layer.resource.image, resource = layer.resource)         

                    links.new(image.outputs[0], mixrgb.inputs[2])

                set_default(mixrgb,2,layer.resource.default_color)
                set_default(mixrgb,0,1.0)
                set_default(opacitynode,1,layer.opacity)

                layer.resource.default_color_socket.set_socket_reference(mixrgb.inputs[2])
                layer.opacity_socket.set_socket_reference(opacitynode.inputs[1])
                
                layer_node = mixrgb

                if filnodegroup:
                    if image:
                        links.new(image.outputs['Color'], filnodegroup.inputs["Color"])
                    else:
                        set_default(filnodegroup,"Color", layer.resource.default_color)
                        set_default(filnodegroup,"Alpha", 1.0)
                        layer.resource.default_color_socket.set_socket_reference(filnodegroup.inputs["Color"])
                    links.new(filnodegroup.outputs['Color'], mixrgb.inputs[2])

                if layer_node:
                    links.new(prev_node.outputs['Color'] if prev_node else group_input.outputs['Color'], layer_node.inputs[1])
                    links.new(srinm if srinm else group_input.outputs['Alpha'], opacitynode.inputs[0])
                    links.new(opacitynode.outputs[0], mixrgb.inputs[0])
                    prev_node = layer_node
        if prev_node:
            sockets.append(prev_node.outputs['Color'])
    if prev_node:  
        links.new(prev_node.outputs['Color'], group_output.inputs['Color'])
    else:
        links.new(group_input.outputs['Color'], group_output.inputs['Color'])

    lastcol = blendin(node_group, sockets, group_input.outputs["Type"])
    lastcolal = blendin(node_group, alsockets, group_input.outputs["Type"])
    if folder_layerfinm:
        lastcolal =  folder_layerfilnodegroup.outputs["Alpha"]
        colfilt = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", folder_layerfinm)
        links.new(group_input.outputs["Type"], colfilt.inputs["Type"])
    if lastcol:
        if colfilt:
            links.new(lastcol, colfilt.inputs["Color"])
            lastcol = colfilt.outputs["Color"]
        links.new(lastcol, group_output.inputs['Color'])
        links.new(lastcolal, group_output.inputs['Alpha'])

    alphablend= create_node(node_group,'ShaderNodeMixRGB', 0,0, "mix", "SCREEN")
    set_default(alphablend,0,1.0)

    links.new(lastcolal, alphablend.inputs[2])
    links.new(group_input.outputs["Alpha"], alphablend.inputs[1])
    links.new(alphablend.outputs[0], group_output.inputs['Alpha'])
    return node_group

def clear_node_socket_connections(node):
    for input_socket in node.inputs:
        while input_socket.links:
            bpy.data.node_groups[node.id_data.name].links.remove(input_socket.links[0])

    for output_socket in node.outputs:
        while output_socket.links:
            bpy.data.node_groups[node.id_data.name].links.remove(output_socket.links[0])

def clear_nodes(node_group,filters):
    # Remove nodes from node group ignoring filters
    for node in node_group.nodes:
        safe = False
        # if node.type == 'GROUP' and node.node_tree:
        #     node_group.nodes.remove(node)
        #     continue
        for filter in filters:
            if filter.node_name == node.name:
                safe = True
            if filter.levels.levels_node.name == node.name:
                safe = True
        if not safe:
            node_group.nodes.remove(node)

def simple_clear_node(node_group):
    # remove all nodes in node group
    for node in  node_group.nodes:
        node_group.nodes.remove(node)

def clear_nodes_ignoring(node_group):
    # Clear nodes in node groups. Check by name
    for node in  node_group.nodes:
        if not node.name.startswith("fs_"):
            node_group.nodes.remove(node)

def create_socket(node_group, name, socket_type_key, input):
    # Simplifying socket creation for node groups
    socket_type_mapping = {
        'float': 'NodeSocketFloat',
        'color': 'NodeSocketColor',
        'vector': 'NodeSocketVector',
        'shader': 'NodeSocketShader',
        'geom': 'NodeSocketGeometry',
    }
    if input:
        in_out = 'INPUT'
    else:
        in_out = 'OUTPUT'
    socket_type = socket_type_mapping.get(socket_type_key, 'NodeSocketColor')

    if is_4_0_or_newer():
        if name not in [sock.name for sock in node_group.interface.items_tree if sock.in_out == in_out]:
            node_group.interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)
    else:
        if in_out == 'INPUT' and name not in node_group.inputs:
            node_group.inputs.new(socket_type, name)
        elif in_out == 'OUTPUT' and name not in node_group.outputs:
            node_group.outputs.new(socket_type, name)

def set_default(node_group, name, value):
    # Set default socket value
    if hasattr(node_group, 'interface') and hasattr(node_group.interface, 'items_tree'):
        for ind, item in enumerate(node_group.interface.items_tree):
            if item.item_type == 'SOCKET':
                if item.in_out == 'INPUT':
                    try:
                        if isinstance(name, int):
                            if name == ind:
                                item.default_value = value
                                return
                        elif isinstance(name, str):
                            if name == item.name:
                                item.default_value = value
                                return
                    except (KeyError, IndexError):
                        pass
    else:
        try:
            if isinstance(name, int):
                if name < len(node_group.inputs):
                    input_socket = node_group.inputs[name]
                    if hasattr(input_socket, "default_value"):
                        input_socket.default_value = value
            elif isinstance(name, str):
                if name in node_group.inputs:
                    input_socket = node_group.inputs[name]
                    if hasattr(input_socket, "default_value"):
                        input_socket.default_value = value
        except (KeyError, IndexError):
            pass

def set_minmax(node_group, name, min, max):
    #Set default socket min and max values.
    if hasattr(node_group, 'interface'):
        try:
            if isinstance(name, int):
                node_group.interface.items_tree[name].min_value = min
                node_group.interface.items_tree[name].max_value = max
            elif isinstance(name, str):
                node_group.interface.items_tree[name].min_value = min
                node_group.interface.items_tree[name].max_value = max
        except (KeyError, IndexError):
            
            pass
    else:
        try:
            if isinstance(name, int):
                if name < len(node_group.inputs):
                    input_socket = node_group.inputs[name]
                    if hasattr(input_socket, "min_value"):
                        input_socket.min_value = min
                        input_socket.max_value = max
            elif isinstance(name, str):
                if name in node_group.inputs:
                    input_socket = node_group.inputs[name]
                    if hasattr(input_socket, "min_value"):
                        input_socket.min_value = min
                        input_socket.max_value = max
        except (KeyError, IndexError):
            pass

def create_node(node_group, nodename, locx, locy, mode, operation):
    #Simplifying node creation. Setting everything in one line.
    if not nodename or nodename == "None":
        return
    node = node_group.nodes.new(nodename)

    if mode == "op":
        node.operation = operation
    elif mode == "img":
        node.image = operation
    elif mode == "mix":
        node.blend_type = operation
    elif mode == "cus":
        node.node_tree = bpy.data.node_groups.get(operation) 

    node.location.x = locx
    node.location.y = locy

    return node

def Note(node_group):
    note = node_group.nodes.new('NodeFrame')
    note.location = (-200, 400)
    note.label = "This node group is created and used by HAS Paint Layers"
    note.width = 600

def UnlitNode():
    # Used for "Unlit" shader setup 
    part = get_material_collection()
    name = "HAS_Unlit"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes_ignoring(node_group)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Shader", 'shader', False)

    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)

    set_default(node_group, "Alpha", 1.0)

    Note(node_group)

    fixtransp = create_node(node_group,'ShaderNodeMixRGB', 50,300, "mix", "MULTIPLY")
    set_default(fixtransp, 0, 1.0)
    emission = node_group.nodes.new('ShaderNodeEmission')
    emission.location = (50, 300)
    transparent = node_group.nodes.new('ShaderNodeBsdfTransparent')
    transparent.location = (50, 300)
    invert = node_group.nodes.new('ShaderNodeInvert')
    invert.location = (50, 300)
    addshader = node_group.nodes.new('ShaderNodeAddShader')
    addshader.location = (50, 300)

    tree_links = node_group.links
    if part.colorfix:
        tree_links.new(input_node.outputs["Color"], emission.inputs[0])
    else:
        tree_links.new(input_node.outputs["Color"], fixtransp.inputs[1])
        tree_links.new(input_node.outputs["Alpha"], fixtransp.inputs[2])
        tree_links.new(fixtransp.outputs[0], emission.inputs[0])
    
    tree_links.new(input_node.outputs["Alpha"], invert.inputs[1])
    tree_links.new(invert.outputs[0], transparent.inputs[0])

    tree_links.new(emission.outputs[0], addshader.inputs[0])
    tree_links.new(transparent.outputs[0], addshader.inputs[1]) 
    tree_links.new(addshader.outputs[0], output_node.inputs[0])
    return node_group

def SetupMtl(material,part):
    # Setup base of a material
    if material.use_nodes is False:
        material.use_nodes = True

    tree = material.node_tree
    output_node = get_node_by_name(tree, "Material Output")
    if not output_node:
        output_node = tree.nodes.new('ShaderNodeOutputMaterial')
        output_node.location = (600, 0)
 
    shader_node = get_node_by_name(tree, "Principled BSDF")
    emit_node = get_node_by_name(tree, "HAS_Unlit")
    if part.shader_type == 'PRINCIPLED':
        if not shader_node:
            shader_node = tree.nodes.new('ShaderNodeBsdfPrincipled')
            shader_node.location = (output_node.location[0] -400,output_node.location[1])
        tree_links = tree.links

        tree_links.new(shader_node.outputs[0], output_node.inputs[0]) 

    elif part.shader_type == 'UNLIT':
        UnlitNode()
        if not emit_node:
            emit_node = create_node(tree, 'ShaderNodeGroup' , output_node.location[0] -200,output_node.location[1], "cus", UnlitNode().name)
            emit_node.name = "HAS_Unlit"
        tree_links = tree.links

        tree_links.new(emit_node.outputs[0], output_node.inputs[0]) 
        shader_node = emit_node

    return tree, shader_node, output_node

def UpdateShader():
    # Update whole shader. Validating layers, filters, and reconnecting everything to match user setup
    CheckForEmpty()
    fixorder()
    update_layer_index()
    create_normal_blend_group()
    matnode = hasmatnode()

    bpy.context.scene.other_props.layercombineactive = False
    part = get_material_collection()
    
    if part.shader_type == 'Custom':
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
        group_node = tree.nodes.new('ShaderNodeGroup')
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
    if part.shader_type == 'PRINCIPLED':
        if bpy.context.scene.other_props.preview_mode == "COMBINED":
            for type in getusedmaps():
                nm = type[1]
                if nm:
                    if nm == "Diffuse":
                        tree_links.new(group_node.outputs[nm], shader_node.inputs["Base Color"])
                        
                        if part.diffusealpha:
                            tree_links.new(group_node.outputs['DiffuseAlpha'], shader_node.inputs["Alpha"])
                        elif typeexist("ALPHA"):
                            tree_links.new(group_node.outputs['Alpha'], shader_node.inputs["Alpha"])
                    elif nm == "Height":
                        tree_links.new(group_node.outputs['Normal'], shader_node.inputs["Normal"])
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
                    
    elif part.shader_type == 'UNLIT':
        tree_links.new(group_node.outputs['Diffuse'], shader_node.inputs["Color"])
        if part.diffusealpha:
            tree_links.new(group_node.outputs['DiffuseAlpha'], shader_node.inputs["Alpha"])
        elif typeexist("ALPHA"):
            tree_links.new(group_node.outputs['Alpha'], shader_node.inputs["Alpha"])

def typeexist(Name):
    for type in getusedtypes():
        if type == Name:
            return True
    return False

def getlayer(index):
    part = get_material_collection()
    return part.layers[index]

def getsublayer(index):
    part = get_material_collection()
    return part.sublayers[index]

def layersgroup(tex_type, name):
    # Group created for each used Channel
    part = get_material_collection()
    layers = get_layers(part.base_layers)
    group_name = getgroupname(tex_type[0], name)
    if group_name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[group_name]
        for nodei in  node_group.nodes:
            node_group.nodes.remove(nodei)    
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=group_name)

    Note(node_group)
    group_output = node_group.nodes.new("NodeGroupOutput")
    group_output.location = (500, 0)
    group_input = node_group.nodes.new("NodeGroupInput")
    group_input.location = (-500, 0)

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', False)

    count = -1

    links = node_group.links
    for link in links:
        links.remove(link)
        
    prev_node = None

    for index, layer in enumerate(layers):
        fldrlrs = getusedtypesinlayers(get_layers(layer.sub_layers))

        if layer.layer_type =="FOLDER" or layer.layer_type =="PBR":
            if layer.use_layer and tex_type[0] in fldrlrs:
                count = count+1

                l_group = get_folder_nodegroup(layer, pbr = layer.layer_type =="PBR")

                layer_node = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", l_group.name)

                if prev_node:
                    links.new(prev_node.outputs['Color'], layer_node.inputs['Color'])
                    links.new(prev_node.outputs['Alpha'], layer_node.inputs['Alpha'])
                else:
                    links.new(group_input.outputs['Color'], layer_node.inputs['Color'])
                    links.new(group_input.outputs['Alpha'], layer_node.inputs['Alpha'])
                
                set_default(layer_node, "Type", fldrlrs.index(tex_type[0]))
                prev_node = layer_node
        
        else:
            if layer.use_layer and tex_type[0]==layer.texture_type:

                count = count+1
                
                l_group = create_layer_node(layer)
                layer_node = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", l_group.name)

                if prev_node:
                    links.new(prev_node.outputs['Color'], layer_node.inputs['Color'])
                    links.new(prev_node.outputs['Alpha'], layer_node.inputs['Alpha'])
                else:
                    links.new(group_input.outputs['Color'], layer_node.inputs['Color'])
                    links.new(group_input.outputs['Alpha'], layer_node.inputs['Alpha'])
                prev_node = layer_node

    if prev_node:
        links.new(prev_node.outputs['Color'], group_output.inputs['Color'])
        links.new(prev_node.outputs['Alpha'], group_output.inputs['Alpha'])
        if part.InvertG:
            if tex_type[0] == "NORMAL":
                invnrmnode = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", InvertNormalNode().name)
                if invnrmnode:
                    links.new(prev_node.outputs['Color'], invnrmnode.inputs['Normal'])
                    links.new(invnrmnode.outputs['Normal'], group_output.inputs['Color'])
        if part.colorfix and tex_type[0] == "DIFFUSE" and part.diffusealpha and not part.shader_type == "UNLIT":
            Colfix = create_node(node_group,'ShaderNodeMixRGB', -200,0, "mix", 'DIVIDE')
            set_default(Colfix, 0, 1.0)
            links.new(prev_node.outputs['Color'], Colfix.inputs[1])
            links.new(prev_node.outputs['Alpha'], Colfix.inputs[2])
            links.new(Colfix.outputs[0], group_output.inputs['Color'])
    else:
        links.new(group_input.outputs['Color'], group_output.inputs['Color'])
        links.new(group_input.outputs['Alpha'], group_output.inputs['Alpha'])


    return node_group

def hasmatnode():
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
    Note(node_group)
    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)
    hsocketout = None
    nrmsocketout = None
    for layer in part.layers:
        if layer.layer_type =="FOLDER":
            create_folder_nodegroup(layer)
        elif layer.layer_type =="PBR":
            create_pbr_nodegroup(layer)

    for indexgr, tex_type in enumerate(TEXTURE_TYPE):

        lgroup = layersgroup(tex_type, name)
        
        group_node = node_group.nodes.new('ShaderNodeGroup')
        group_node.node_tree = lgroup
        group_node.location = (0,-200*indexgr)
        type = tex_type[0]
        nm = tex_type[1]
        anm = f'{nm}Alpha'

        create_socket(node_group, f"{nm}", 'color', True)
        create_socket(node_group, f"{anm}", 'float', True)
        create_socket(node_group, f"{nm}", 'color', False)
        create_socket(node_group, f"{anm}", 'float', False)

        if not group_node.outputs or not group_node.inputs:
            continue
        links.new(group_node.outputs['Color'], output_node.inputs[nm])
        links.new(group_node.outputs['Alpha'], output_node.inputs[anm])
        links.new(input_node.outputs[nm], group_node.inputs['Color'])
        links.new(input_node.outputs[anm], group_node.inputs['Alpha'])

        if type == "ROUGHNESS":
            set_default(node_group, "Roughness", (0.9,0.9,0.9,1.0))
        if type == "HEIGHT":
            hsocketout = group_node.outputs['Color']
            set_default(node_group, "Height", (0.5,0.5,0.5,1.0))
        if type == "NORMAL":
            nrmsocketout = group_node.outputs['Color']
            set_default(node_group, "Normal", (0.5,0.5,1.0,1.0))
        if type == "DIFFUSE":
            set_default(node_group, "Diffuse", (0.0,0.0,0.0,1.0))
        if type == "ALPHA":
            set_default(node_group, "Alpha", (1.0,1.0,1.0,1.0))
        if not type == "DIFFUSE":
            set_default(node_group, anm, 1.0)

    create_socket(node_group, "RawNormal", 'Color', False)
    if nrmsocketout:
        links.new(nrmsocketout, output_node.inputs["RawNormal"])
    
    for type in getusedmaps():
        nm = type[1]
        anm = f'{nm}Alpha'
        if nm in output_node.inputs:
            if not input_node.outputs[nm].is_linked:
                links.new(input_node.outputs[nm], output_node.inputs[nm])
                links.new(input_node.outputs[anm], output_node.inputs[anm])
        
    if nrmsocketout or hsocketout:
        bump = node_group.nodes.new(type='ShaderNodeBump')
        set_default(bump, 0, part.height_intensity)
        bump.location = (500,-700)
        nrmap = node_group.nodes.new(type='ShaderNodeNormalMap')
        nrmap.location = (200,-500)
        if nrmsocketout:
            links.new(nrmsocketout, nrmap.inputs['Color'])
            links.new(nrmap.outputs[0], bump.inputs['Normal'])
        if hsocketout:
            links.new(hsocketout, bump.inputs['Height'])

        links.new(bump.outputs[0], output_node.inputs['Normal'])

    return node_group 

def update_layer_index():
    # simple layer indexing
    for ind, l in enumerate(get_material_collection().layers):
        l.index = ind
    for ind, l in enumerate(get_material_collection().sublayers):
        l.index = ind

def getfilter(layerindex, index):
    return get_material_collection().layers[layerindex].filters[index]

def check_mtl_used():
    mtlprops = bpy.context.scene.material_props
    for ind, prop in enumerate(mtlprops):
        if prop:
            if prop.material == bpy.context.active_object.active_material:
                return True
    return False 

def levels(node_group, colsoc, levelref, id = ""):
    # Curve node imitating "Levels"
    curve = levelref.levels_node.get_node()
    if not curve:
        curve = create_node(node_group, 'ShaderNodeRGBCurve' , -600,0, "", "")
    if curve:
        ind = {"COL": 3, "R": 0, "G": 1, "B": 2, "A": 3, "LUM": 3}.get(levelref.s_channel, -1)
        set_rgb_curve(curve, levelref.val01, levelref.val02, levelref.val03, levelref.val04, levelref.val05, ind)
        links = node_group.links

        links.new(colsoc, curve.inputs[1])

        colsoc = curve.outputs[0]
        if id:
            curve.name = id
        levelref.levels_node.set_node_reference(curve)
        return curve
    return None

def InvertNormalNode():
    # Node group to invert G channel in Normal
    part = get_material_collection()
    name = ".HAS_InvertNormal"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes_ignoring(node_group)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_socket(node_group, "Normal", 'color', True)
    create_socket(node_group, "Normal", 'color', False)

    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)

    Note(node_group)

    sep = create_node(node_group,'ShaderNodeSeparateRGB', 50,300, "", "")
    com = create_node(node_group,'ShaderNodeCombineRGB', 50,300, "", "")
    inv = create_node(node_group,'ShaderNodeInvert', 50,300, "", "")
    add = create_node(node_group,'ShaderNodeMath', 50,300, "op", "ADD")
    tree_links = node_group.links

    tree_links.new(input_node.outputs[0], sep.inputs[0])

    tree_links.new(sep.outputs[0], com.inputs[0])
    tree_links.new(sep.outputs[1], add.inputs[0])
    tree_links.new(add.outputs[0], inv.inputs[1])
    tree_links.new(inv.outputs[0], com.inputs[1])
    tree_links.new(sep.outputs[2], com.inputs[2])

    tree_links.new(com.outputs[0], output_node.inputs[0])

    return node_group

def set_rgb_curve(node, val1, val2, val3, val4, val5, index):
    # Set curve values to imitate "Levels"
    if not node:
        return
    if node.type != 'CURVE_RGB':
        return

    curve = node.mapping.curves[index]  
    val2 = clamp(val2,0.001,0.999)

    while len(curve.points) > 5:
        curve.points.remove(curve.points[-1])  
    while len(curve.points) < 5:
        curve.points.new(0.5, 0.5)  
    for p in curve.points:
        p.handle_type = 'VECTOR'

    curve.points[1].location = (val1, val4) 
    curve.points[3].location = (val3, val5) 

    curve.points[0].location = (0.0 if val1 < val3 else 1.0, val4) 
    curve.points[4].location = (1.0 if val1 < val3 else 0.0, val5) 

    mid_x = lerp(val1, val3, 0.5)
    mid_y = lerp(val4, val5, val2)
    curve.points[2].location = (mid_x, mid_y)

    node.mapping.update()
    node.update()

def light_node(filter):
    # Node group created for using "Light" Filter.
    part = get_material_collection()
    name = f".HAS_Light_{filter.id}"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes_ignoring(node_group)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)
    create_socket(node_group, "Color", 'color', True)

    create_socket(node_group, "Attenuation", 'float', True)
    create_socket(node_group, "Glossiness", 'float', True)
    create_socket(node_group, "Level", 'float', True)
    create_socket(node_group, "Color", 'color', False)

    set_default(node_group,"Level",1.0)
    set_default(node_group,"Glossiness",1.0)
    set_default(node_group,"Attenuation",0.0)

    set_minmax(node_group, "Level", 0.0, 1.0)
    set_minmax(node_group, "Glossiness", 0.0, 200.0)
    set_minmax(node_group, "Attenuation", -1.0, 1.0)

    if hasattr(node_group, 'interface'):
        node_group.interface.items_tree["Attenuation"].subtype = 'FACTOR'
        node_group.interface.items_tree["Glossiness"].subtype = 'NONE'
        node_group.interface.items_tree["Level"].subtype = 'FACTOR'

    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)

    Note(node_group)
    image = None
    if filter.resource.image:
        image = create_image_node(node_group, filter.resource.image)
        
        madd = create_node(node_group,'ShaderNodeVectorMath', 50,300, "op", "MULTIPLY_ADD")
        set_default(madd,1,(2.0,2.0,2.0))
        set_default(madd,2,(-1.0,-1.0,-1.0))

    geometry = create_node(node_group,'ShaderNodeNewGeometry', 50,300, "", "")
    normal = get_node_by_name(node_group, "fs_LightNormal")
    if not normal:
        normal = create_node(node_group,'ShaderNodeNormal', 50,300, "", "")
        normal.name = "fs_LightNormal"
    Rotate1 = create_node(node_group,'ShaderNodeVectorRotate', 50,300, "", "")

    Add = create_node(node_group,'ShaderNodeMath', 50,300, "op", "ADD")
    Mult1 = create_node(node_group,'ShaderNodeMath', 50,300, "op", "MULTIPLY")
    Mult2 = create_node(node_group,'ShaderNodeMath', 50,300, "op", "MULTIPLY")

    Mult1.use_clamp = True
    Mult2.use_clamp = True

    Rotate1.rotation_type = 'X_AXIS'
    
    tree_links = node_group.links

    tree_links.new(input_node.outputs["Attenuation"], Add.inputs[1])
    tree_links.new(input_node.outputs["Glossiness"], Mult1.inputs[1])
    tree_links.new(input_node.outputs["Level"], Mult2.inputs[1])
    if image:
        tree_links.new(image.outputs[0], madd.inputs[0])
        tree_links.new(madd.outputs[0], Rotate1.inputs[0])
    else:
        tree_links.new(geometry.outputs["Normal"], Rotate1.inputs[0])
    tree_links.new(Rotate1.outputs[0], normal.inputs[0])
    tree_links.new(normal.outputs[1], Add.inputs[0])

    tree_links.new(Add.outputs[0], Mult1.inputs[0])
    tree_links.new(Mult1.outputs[0], Mult2.inputs[0])
    tree_links.new(Mult2.outputs[0], output_node.inputs[0])

    return node_group

def blur_node(filter):
    # Node group created for using "Blur" Filter. 
    name = f".HAS_Blur_{filter.id}"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes_ignoring(node_group)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', False)

    create_socket(node_group, "Pass", 'color', False)
    create_socket(node_group, "PassAlpha", 'float', False)

    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)
    
    Note(node_group)
    image = create_image_node(node_group, filter.resource.image)
   
    tree_links = node_group.links

    tree_links.new(image.outputs[0], output_node.inputs[0])
    tree_links.new(image.outputs[1], output_node.inputs[1])
    tree_links.new(input_node.outputs["Color"], output_node.inputs["Pass"])
    tree_links.new(input_node.outputs["Alpha"], output_node.inputs["PassAlpha"])
    return node_group

def snapshot_node(filter):
    # Node group created for using "Snapshot" Filter.
    name = f".HAS_Snapshot_{filter.id}"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes_ignoring(node_group)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', False)

    create_socket(node_group, "Pass", 'color', False)
    create_socket(node_group, "PassAlpha", 'float', False)

    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)
    
    Note(node_group)
    image =  create_image_node(node_group, filter.resource.image)

    tree_links = node_group.links

    tree_links.new(image.outputs[0], output_node.inputs[0])
    tree_links.new(image.outputs[1], output_node.inputs[1])
    tree_links.new(input_node.outputs["Color"], output_node.inputs["Pass"])
    tree_links.new(input_node.outputs["Alpha"], output_node.inputs["PassAlpha"])
    return node_group

def getsocketconnection(node, socket_name):
    socket = node.inputs.get(socket_name)

    if socket.is_linked:
        link = socket.links[0]
        connected_socket = link.from_socket
        return connected_socket
    return None
            
def getgroupname(tex_type, mtl_name):
    res = f".HAS_{tex_type}_Group_{mtl_name}"
    return res

def newimage(texture_name):
    # Create new image based on "part" settings
    part = get_material_collection()
    if not part:
        return 

    new_image = bpy.data.images.new(
        name=texture_name,
        width=part.texture_sizeX,
        height=part.texture_sizeY,
        alpha= True,
        float_buffer= False,
        tiled=False
    )
    new_image.generated_type = 'BLANK'
    new_image.generated_color = (0.0, 0.0, 0.0, 0.0)
    new_image.alpha_mode = 'CHANNEL_PACKED'
    new_image.colorspace_settings.name = 'sRGB'

    return new_image

def blendin(node_group, sockets, value):
    # Shader nodes to switch between channels using type value
    links = node_group.links
    count = -1
    lastsock = None
    for socket in sockets:
        count = count +1
        mix= create_node(node_group,'ShaderNodeMixRGB', 0,-150*count, "mix", "MIX")
        compare = create_node(node_group,'ShaderNodeMath', -400,-150*count, "op", 'COMPARE')
        set_default(compare, 1, count)
        set_default(compare, 2, 0.1)

        links.new(value, compare.inputs[0])
        links.new(compare.outputs[0], mix.inputs[0])
        links.new(socket, mix.inputs[2])
        if lastsock:
            links.new(lastsock, mix.inputs[1])
        lastsock = mix.outputs[0]
    return lastsock

def getbyid(id):
    # Get layer by ID
    part = get_material_collection()
    for l in part.layers:
        if l.id == id:
            return l
    return None

def get_node_by_name(node_group, name):
    # Get node reference by name
    for node in node_group.nodes:
        if node.name == name:
            return node
    return None

def get_socket_from_name(node_group, name, socket):
    # get socket reference by name
    node = get_node_by_name(node_group, name)
    if node:
        if socket in node.inputs:
            return node.inputs[socket]
    return None

def get_image_nodes_recursive(node_tree, collected_nodes=None):
    if collected_nodes is None:
        collected_nodes = set()

    for node in node_tree.nodes:

        if node.type == 'TEX_IMAGE':

            if node.image is not None and any(node.outputs[i].is_linked for i in range(len(node.outputs))):
                collected_nodes.add(node)

        elif node.type == 'GROUP' and node.node_tree:
            get_image_nodes_recursive(node.node_tree, collected_nodes)

    return collected_nodes

def get_all_image_nodes_in_material(material):
    # Get all images currently used in a material. Used to automatically create layers for the addon from existing material
    node_tree = material.node_tree

    image_nodes = get_image_nodes_recursive(node_tree)

    return list(image_nodes)

def clear_unused_layers():

    part = get_material_collection()
    ids=[]
    for layer in part.base_layers:
        ids.append(layer.id)
        for subl in layer.get_layer().sub_layers:
            ids.append(subl.id)

    for ind, layer in reversed(list(enumerate(part.layers))):
        if not layer.id in ids:
            part.layers.remove(ind)

def type_switch():
    # Node to switch types. Used for shader nodes to store multiple layers from different channels. This allows to switch between them. 
    name = f".HAS_TypeSwitch"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        simple_clear_node(node_group)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "PrevColor", 'color', True)
    create_socket(node_group, "PrevAlpha", 'float', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', False)

    create_socket(node_group, "Type", 'float', True)
    create_socket(node_group, "Compare", 'float', True)
    create_socket(node_group, "Result", 'float', False)

    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)
    
    Note(node_group)

    mix= create_node(node_group,'ShaderNodeMixRGB', 0,-150, "mix", "MIX")
    alphamix= create_node(node_group,'ShaderNodeMixRGB', 0,-150, "mix", "MIX")
    compare = create_node(node_group,'ShaderNodeMath', -400,-150, "op", 'COMPARE')

    set_default(compare, 2, 0.1)

    links = node_group.links

    links.new(input_node.outputs["Type"], compare.inputs[0])
    links.new(input_node.outputs["Compare"], compare.inputs[1])
    links.new(compare.outputs[0], mix.inputs[0])
    links.new(compare.outputs[0], alphamix.inputs[0])
    links.new(input_node.outputs["Color"], mix.inputs[2])
    links.new(input_node.outputs["Alpha"], alphamix.inputs[2])
    links.new(input_node.outputs["PrevColor"], mix.inputs[1])
    links.new(input_node.outputs["PrevAlpha"], alphamix.inputs[1])
    links.new(mix.outputs[0], output_node.inputs["Color"])
    links.new(alphamix.outputs[0], output_node.inputs["Alpha"])
    links.new(compare.outputs[0], output_node.inputs["Result"])
    return node_group

def close_panel(event):
    x, y = event.mouse_x, event.mouse_y
    bpy.context.window.cursor_warp(10, 10)

    move_back = lambda: bpy.context.window.cursor_warp(x, y)
    bpy.app.timers.register(move_back, first_interval=0.001)

def copy_layer(layer, to_layer):
    l = to_layer
    l.opacity = layer.opacity
    l.image = layer.resource.image
    l.blend_mode = layer.blend_mode
    l.texture_type = layer.texture_type

    properties = ["name",
    "node_name",
    "layer_name",
    "in_use",
    'custom_node_tree_p',
    'socket_in',
    'socket_out',
    'image',
    'blend_mode',
    'opacity',
    'default_color',
    ]

    for filter in layer.filters:
        fil = l.filters.add()
        for prop in properties:
            try:
                
                setattr(fil, prop, getattr(filter, prop))

            except AttributeError:
                continue
    original_image = layer.resource.image
    
    new_image = original_image.copy()
    to_layer.resource.image = new_image

def getdescription(enumfrom, propfrom):
    # Get Description From Enum
    for item in enumfrom:
        if item:
            if item[0] == propfrom:
                return item[2]
    return None

def getname(enumfrom, propfrom):
    # Get Name from Enum
    for item in enumfrom:
        if item:
            if item[0] == propfrom:
                return item[1]
    return None

### From Operators

def texture_size_p2(add, size_x, size_y):
    part = get_material_collection()
    if add:

        new_size_x = next_power_of_two(size_x + 1) if size_x else 2
        new_size_y = next_power_of_two(size_y + 1) if size_y else 2
    else:

        new_size_x = next_power_of_two(max(size_x - 1, 1))
        new_size_y = next_power_of_two(max(size_y - 1, 1))
        
        if new_size_x >= size_x:
            new_size_x = next_power_of_two(max(size_x // 2, 1))
        if new_size_y >= size_y:
            new_size_y = next_power_of_two(max(size_y // 2, 1))
    return new_size_x, new_size_y

def setup_material(active_object):
    if active_object:
        if active_object.active_material:
            mat = active_object.active_material
            mat.use_nodes = True
        else:
            bpy.ops.object.mode_set(mode='OBJECT')
            mat = bpy.data.materials.new(name=re.sub(r'[^A-Za-z0-9]', '', f"has{active_object.name}"))

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

def new_layer(fill = False):
    part = get_material_collection()
    if not fill:
        new_image = bpy.data.images.new(
            name=newimagename(newlayername()),
            width=part.texture_sizeX,
            height=part.texture_sizeY,
            alpha= True,
            float_buffer= False,
            tiled=False
        )
        new_image.generated_type = 'BLANK'
        new_image.generated_color = (0.0, 0.0, 0.0, 0.0)
        new_image.alpha_mode = 'CHANNEL_PACKED'
        new_image.colorspace_settings.name = 'sRGB'
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
        reassign_layer(part.base_layers, get_layer_by_id(selectedisattached).sub_layers, layer_item.id, parent = get_layer_by_id(selectedisattached))
    else:
        move_last_to_selected(part.base_layers)

    if fill:
        layer_item.layer_type = "FILL"
    layer_item.suppress_update = False
    layer_item.resource.suppress_update = False
    SelectLayer(layer_item.id)
    
    UpdateShader()

def new_layer_from_image(new_image, layer_name = ""):

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
    layer_name = newlayername(pref= "PBR")
    image_name = newimagename(layer_name)
    
    xs = part.texture_sizeX
    ys = part.texture_sizeY

    new_image = bpy.data.images.new(
        name=image_name,
        width=xs,
        height=ys,
        alpha= True,
        float_buffer=False,
        tiled= False
    )
    new_image.generated_type = 'BLANK'
    new_image.generated_color = (0.0, 0.0, 0.0, 0.0)
    
    new_image.alpha_mode = 'CHANNEL_PACKED'
    new_image.colorspace_settings.name = 'sRGB'

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
        'DIFFUSE': ((0.5,0.5,0.5,1.0)),
        'ROUGHNESS': ((0.8,0.8,0.8,1.0)),
        'METALLIC': ((0.0,0.0,0.0,1.0)),
        'NORMAL': ((0.5,0.5,1.0,1.0)),
        'HEIGHT': ((0.5,0.5,0.5,1.0)),
        'ALPHA': ((1.0,1.0,1.0,1.0)),
        'EMISSION': ((0.0,0.0,0.0,1.0)),
        'AO': ((1.0,1.0,1.0,1.0)),
        'CUSTOM': ((0.0,0.0,0.0,1.0)),
    }
    for type in getusedmaps():
        layer_item = part.layers.add()
        layer_item.suppress_update = True
        layer_item.resource.suppress_update = True
        if type[0] == "DIFFUSE":
            layer_item.resource.image = new_image

        layer_item.resource.default_color = defcolor.get(type[0], ((0.0,0.0,0.0,1.0)))
        layer_item.resource.default_value = defcolor.get(type[0], ((0.0,0.0,0.0,1.0)))[0]
        layer_item.texture_type = type[0]
        layer_item.id = shortid()
        base_layer_item.sub_layers.add().id = layer_item.id
        layer_item.suppress_update = False
        layer_item.resource.suppress_update = False

    selectedisattached = part.layers[get_selected_layer_index()].attachedto
    
    if selectedisattached:
        reassign_layer(part.base_layers, get_layer_by_id(selectedisattached).sub_layers, base_layer_item.id, parent = get_layer_by_id(selectedisattached))
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
    layer_item.layer_name = newlayername(pref= "Folder")
    layer_item.layer_type = "FOLDER"
    layer_item.id = shortid()
    layer_item.sort_color = 'OUTLINER_COLLECTION'
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
                if node.type == 'OUTPUT_MATERIAL':
                    output_node = node
                else:
                    tree.nodes.remove(node)
            if 'output_node' not in locals():
                output_node = tree.nodes.new('ShaderNodeOutputMaterial')
                output_node.location = (600, 0)
            mtl_n = material.name

            image_node = create_image_node(tree, image)

            tree.links.new(image_node.outputs[0], output_node.inputs[0]) 
            return True
        else:
            return False

def is_3_4_or_newer():
    version = bpy.app.version
    return (version[0] > 3) or (version[0] == 3 and version[1] >= 4)
def is_4_0_or_newer():
    version = bpy.app.version
    return version[0] >= 4
def is_4_2_or_newer():
    version = bpy.app.version
    return version[0] > 4 or (version[0] == 4 and version[1] >= 2)
def get_presets_folder():
    if is_4_2_or_newer():
        return bpy.utils.extension_path_user(__package__, path= "presets/savedpresets", create=True)
    else:
        return bpy.utils.user_resource('SCRIPTS', path= "presets/haspresets/savedpresets", create=True)

def parse_stored_view(stored_view_str):
    # Use a more flexible regex to match the Matrix and perspective
    match = re.search(r'Matrix\(\(\((.*?)\)\)\),\s*\'(.*?)\'', stored_view_str, re.DOTALL)
    if not match:
        raise ValueError(f"Invalid stored view string format: {stored_view_str}")

    matrix_str, perspective = match.groups()

    # Split the matrix string into rows
    rows = matrix_str.split("), (")
    matrix = []

    # Convert each row into a tuple of floats, cleaning up any extra characters
    for row in rows:
        values = row.replace(")", "").replace("(", "").split(",")
        matrix.append(tuple(float(x.strip()) for x in values))

    # Convert to Blender's Matrix type
    return Matrix(matrix), perspective