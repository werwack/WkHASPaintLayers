import bpy
from bpy.utils import register_class, unregister_class
from bpy.props import CollectionProperty, StringProperty, IntProperty, PointerProperty, BoolProperty, FloatVectorProperty, FloatProperty, EnumProperty
from bpy.types import PropertyGroup
from .utils import *
from .has_enum import *

class UsedMaps(PropertyGroup):
    # Stored per Material. User can toggle active channels
    def update_shader(self, context):
        UpdateShader()
    Diffuse: BoolProperty(name="Diffuse", default= True, update = update_shader)
    Metallic: BoolProperty(name="Metallic", default= True, update = update_shader)
    Roughness: BoolProperty(name="Roughness", default= True, update = update_shader)
    Emission: BoolProperty(name="Emission", default= False, update = update_shader)
    Alpha: BoolProperty(name="Alpha", default= False, update = update_shader)
    Normal: BoolProperty(name="Normal", default= True, update = update_shader)
    Height: BoolProperty(name="Height", default= True, update = update_shader)
    AO: BoolProperty(name="Ambient Occlusion", default= False, update = update_shader)
    Custom: BoolProperty(name="Custom", default= False, update = update_shader)

class LayerReference(PropertyGroup):
    # Used to store layer ID for recursive dependencies
    id: StringProperty()
    index: IntProperty()
    def get_layer(self):
        part = get_material_collection()

        for l in part.layers:
            if l.id == self.id:
                return l
        
        return None
 
class SocketReference(PropertyGroup):
    # Store node socket similar to Pointer
    def updatesocket(self, context):
        node_tree = bpy.data.node_groups.get(self.node_tree_name)
        if node_tree:
            node = node_tree.nodes.get(self.node_name)
            if node:
                set_default(node, self.socket_name, self.default_value)
    default_value: FloatProperty(update= updatesocket, min = 0.0, max =1.0)
    node_name: StringProperty(name="Node Name")
    socket_name: StringProperty(name="Socket Name")
    node_tree_name: StringProperty(name="Node Tree Name")
    
    def get_socket(self):
        node_tree = bpy.data.node_groups.get(self.node_tree_name)
        if node_tree:
            node = node_tree.nodes.get(self.node_name)
            if node:
                return node.inputs[self.socket_name]
        return None
    def set_socket_reference(self, socket):
        if socket:
            self.node_tree_name = socket.node.id_data.name
            self.node_name = socket.node.name 
            self.socket_name = socket.name

class NodeReference(PropertyGroup):
    #Store node similar to Pointer
    node_name: StringProperty(name="Node Name")
    node_tree_name: StringProperty(name="Node Tree Name")
    node_type: StringProperty(name="Node Type")
    
    def get_node(self):
        node_tree = bpy.data.node_groups.get(self.node_tree_name)
        if node_tree:
            node = node_tree.nodes.get(self.node_name)
            return node
        return None

    def set_node_reference(self, node):
        if node:

            self.node_tree_name = node.id_data.name
            self.node_name = node.name
            self.node_type = node.bl_idname 

class HistrogramReference(PropertyGroup):
    # Image Histogram as String of values
    texture_name: StringProperty()
    histogram: StringProperty()
    
class LevelsProperty(PropertyGroup):
    # Used for Filters
    def valupdate(self, context):
        if self.suppress_update:
            return
        self.suppress_update = True
        if self.levels_node:
            ind = {"COL": 3, "R": 0, "G": 1, "B": 2, "A": 3, "LUM": 3}.get(self.s_channel, -1)
            set_rgb_curve(self.levels_node.get_node(), self.val01, self.val02, self.val03, self.val04, self.val05, ind)
        self.suppress_update = False

    levels_node: PointerProperty(type=NodeReference)

    val01: FloatProperty(
        default=0.0,
        min=0.0,
        max=1.0,
        update=valupdate
    )
    val02: FloatProperty(
        default=0.5,
        min=0.0,
        max=1.0,
        update=valupdate
    )
    val03: FloatProperty(
        default=1.0,
        min=0.0,
        max=1.0,
        update=valupdate
    )
    val04: FloatProperty(
        default=0.0,
        min=0.0,
        max=1.0,
        update=valupdate
    )
    val05: FloatProperty(
        default=1.0,
        min=0.0,
        max=1.0,
        update=valupdate
    )
    def channelswitch(self, context):
        if self.suppress_update:
            return
        self.suppress_update = True
        node = self.levels_node.get_node()
        ind = {"COL": 3, "R": 0, "G": 1, "B": 2, "A": 3, "LUM": 3}.get(self.s_channel, -1)
        if not ind == -1:
            curve = node.mapping.curves[ind]
            if not len(curve.points) == 2:
                while len(curve.points) < 5:
                    curve.points.new(0.5, 0.5)
                self.val01 = curve.points[1].location[0]
                self.val03 = curve.points[3].location[0]
                self.val02 = fraction_between(curve.points[2].location[0], self.val01, self.val03)
                self.val04 = curve.points[0].location[1]
                self.val05 = curve.points[4].location[1]
            else:
                self.val01 = 0.0
                self.val02 = 0.5
                self.val03 = 1.0
                self.val04 = 0.0
                self.val05 = 1.0
                set_rgb_curve(node, self.val01, self.val02, self.val03, self.val04, self.val05, ind)

        curve = node.mapping.curves[ind]  
        self.suppress_update = False
    s_channel: EnumProperty(
        name="Channel",
        items=[
            ('COL', 'Color', '', "EVENT_C",0),
            (None),
            ('R', 'R Channel', '',"EVENT_R",1),
            ('G', 'G Channel', '',"EVENT_G",2),
            ('B', 'B Channel', '',"EVENT_B",3),
        ],
        update=channelswitch,
    )
    expand: BoolProperty(default = False)
    expand_levels: BoolProperty(default = False)
    suppress_update: BoolProperty()

class ResourceProperty(PropertyGroup):
    # Store image/color with settings
    def update(self, context):
        if self.suppress_update:
            return
        UpdateShader()
    def MappingUpdate(self, context):
        if self.suppress_update:
            return
        mapping = self.mapping_node.get_node()
        if mapping:
            set_default(mapping, "Location", (self.mapx,self.mapy,0.0))
            set_default(mapping, "Rotation", (0.0,0.0,self.maprot))
            set_default(mapping, "Scale", (self.mapscalex,self.mapscaley,1.0))
    suppress_update: BoolProperty()
    expand: BoolProperty(default = False)
    grayscale: BoolProperty(default = False)
    image: PointerProperty(
        name="Image",
        type=bpy.types.Image,
        update=update
    )
    mapping_node: PointerProperty(type=NodeReference)
    histogram: StringProperty()
    def default_value_socket_update(self, context):
        if self.suppress_update:
            return
        self.default_color = (self.default_value,self.default_value,self.default_value,self.default_value)

    def default_color_socket_update(self, context):
        if self.suppress_update:
            return
        if self.grayscale:
            self.suppress_update = True
            self.default_color = (self.default_color[0],self.default_color[0],self.default_color[0],1.0)
            self.suppress_update = False
        if self.default_color_socket.get_socket():
            self.default_color_socket.get_socket().default_value = self.default_color
        else:
            UpdateShader()
    default_color: FloatVectorProperty(
        name="Default Color",
        description="Default color",
        subtype='COLOR',
        size=4, 
        default=(0.5, 0.5, 0.5, 1.0),
        min=0.0,
        max=1.0,
        update=default_color_socket_update
    )
    default_color_socket: PointerProperty(type=SocketReference)

    default_value: FloatProperty(
        name="Default Value",
        default=0.5,
        min=0.0,
        max=1.0,
        update=default_value_socket_update
    )
    mapx: FloatProperty(
        name="Mapping Offset X",
        default=0,
        update=MappingUpdate,
        subtype='DISTANCE'
    )
    mapy: FloatProperty(
        name="Mapping Offset Y",
        default=0,
        update=MappingUpdate,
        subtype='DISTANCE',
    )
    mapscalex: FloatProperty(
        name="Mapping Scale X",
        default=1.0,
        update=MappingUpdate
    )
    mapscaley: FloatProperty(
        name="Mapping Scale Y",
        default=1.0,
        update=MappingUpdate
    )
    maprot: FloatProperty(
        name="Mapping Rotation",
        default=0,
        update=MappingUpdate,
        subtype='ANGLE'
    )

    repeat: EnumProperty(
        name="Repeat",
        items=[
            ('TILE', "Repeat XY", "Repeat Texture in All Directions"),
            ('X', "Repeat X", "Repeat Texture Horizontally"),
            ('Y', "Repeat Y", "Repeat Texture Vertically"),
            ('CLIP', "Clip", "Texture will be Clipped"),
        ],
        default="TILE",
        update=update
    )
    expand_mapping: BoolProperty(default = False)
    levels: PointerProperty(type=LevelsProperty)

class TextureMappedProperty(PropertyGroup):
    # Mapping attached to each texture
    texture_type: EnumProperty(
        name="Type",
        items=[
            ('PAINT', "Paint Layer", ""),
            ('TEXTURE', "Texture", ""),
            ('PROC', "Procedural", ""),
        ],
        description="Texture use type",
        default="PAINT",
    )
    proc_node_type: EnumProperty(
        name="Type",
        items=[
            ('PAINT', "Paint Layer", ""),
            ('TEXTURE', "Texture", ""),
            ('PROC', "Procedural", ""),
        ],
        description="Texture use type",
        default="PAINT",
    ) 
    image: PointerProperty(
        name="Image",
        type=bpy.types.Image,
    )
    mapping_x: FloatProperty(
        name="Offset X",
        default=0.0,
    )
    mapping_y: FloatProperty(
        name="Offset Y",
        default=0.0,
    )
    mapping_rotation: FloatProperty(
        name="Rotation",
        default=0.0,
    )
    mapping_scale_x: FloatProperty(
        name="Scale X",
        default=1.0,
    )
    mapping_scale_Y: FloatProperty(
        name="Scale Y",
        default=1.0,
    )

class MaskGeneratorProperty(PropertyGroup):
    # Property for Filter "Mask Generator"
    def get_item(self,item):
        if item == "AO":
            return self.ao_resource
        elif item == "Curvature":
            return self.curv_resource
        elif item == "Position":
            return self.pos_resource
        elif item == "Object Normal":
            return self.objn_resource
        return None
    expand: BoolProperty(name="Expand", default=False)
    ao_resource: PointerProperty(type=ResourceProperty)
    curv_resource: PointerProperty(type=ResourceProperty)
    pos_resource: PointerProperty(type=ResourceProperty)
    objn_resource: PointerProperty(type=ResourceProperty)
    ao_expand: BoolProperty(name="AO",default = False)
    curv_expand: BoolProperty(name="Curvature",default = False)
    pos_expand: BoolProperty(name="Position",default = False)
    objn_expand: BoolProperty(name="Object Normal",default = False)

class FilterProperty(PropertyGroup):
    # Filter information, dynamically added to layers by user.
    def resetinputs(self):
        self.socket_in = 0
        self.socket_out = 0
    def reset_filter_name(self, context):
        if self.suppress_update:
            return
        self.suppress_update = True
        self.resetinputs()
        self.node_name = ""
        self.resource.image = None

        if self.name == "LIGHT":
            for geds in get_material_collection().bake_maps:
                geds.type == "NRMOBJ"
                if geds.image:
                    self.resource.image = geds.image
        if self.name == "PAINT":
            if not self.resource.image:
                texture_name = f'.HAS_{self.id}_paint'
                ims = bpy.data.images.get(texture_name)
                if ims:
                    self.resource.image = ims
                else:
                    self.resource.image = newimage(texture_name)
        UpdateShader()

        self.suppress_update = False
    def reset_filter(self, context):
        
        self.suppress_update = True
        self.resetinputs()
        UpdateShader()
        self.suppress_update = False
    def reset_custom_filter(self, context):
        self.suppress_update = True
        self.node_name = ""
        self.resetinputs()
        if self.custom_node_tree_p and self.custom_node_tree_p.name.startswith("."):
            self.custom_node_tree_p = None
        UpdateShader()
        self.suppress_update = False
    def update_layer(self, context):
        if not self.suppress_update:
            layer_filter(get_layer_by_id(self.layer_in), multi = True)

    def valupdate(self, context):
        if self.suppress_update:
            return
        layer_filter(get_layer_by_id(self.layer_in))

    id: StringProperty(
        name="ID",
        default="empty"
    )

    name: StringProperty(
        name="Filter",
        default="",
        update=reset_filter_name
    )
    edit: BoolProperty(
        name="Settings",
        description="Toggle filter settings",
        default=False,
    )
    in_use: BoolProperty(
        name="Visibility",
        description="Toggle filter visibility",
        default=True,
        update=update_layer
    )
    node_name: StringProperty( 
        default="",
        name="Node",
        description="Name of the node",
    )
    mixnode: StringProperty()
    #custom_node_tree: StringProperty(update = reset_filter_name)
    custom_node_tree_p: PointerProperty(type=bpy.types.NodeTree, update = reset_custom_filter)
    layer_in: StringProperty(
        default="",
    )
    node: PointerProperty(type=NodeReference)
    displnode: PointerProperty(type=NodeReference)
    socket_in: IntProperty(
        default=0,
        name="Input",
        
    )
    socket_out: IntProperty(
        default=0,
        name="Input", 
    )

    image: PointerProperty(
        name="Image",
        type=bpy.types.Image,
        update=update_layer
    )
    resource: PointerProperty(type=ResourceProperty)
    maskgen: PointerProperty(type=MaskGeneratorProperty)
    editgrunge: BoolProperty(
        name="Grunge",
        description="Toggle Grunge settings",
        default=False,
    )
    blend_mode: EnumProperty(
        name="Blend Mode",
        items=BLEND_MODES,
        description="Blend mode for mixing layers",
        default="MIX",
        update=reset_filter
    )
    def update_opacity(self, context):
        sock = self.opacity_socket.get_socket()
        if sock:
            sock.default_value = self.opacity
           
    opacity: FloatProperty(
        name="Opacity",
        description="Opacity of the layer",
        default=1.0,
        min=0.0,
        max=1.0,
        update=update_opacity
    )
    opacity_socket: PointerProperty(type=SocketReference)
    Unspval: FloatProperty(
        default=1.0,
        min=0.0,
        update=valupdate
    )
    connection_type: EnumProperty(
        name="Filter Type",
        items=[
            ('COLOR', 'Color', ''),
            ('ALPHA', 'Alpha', ''),
            ('UV', 'UV', ''),
        ],
    )
    def get_texture_types(self, context):
        return getusedmaps()
    affect_channels: EnumProperty(
        name="Channel",
        items=get_texture_types,
        description="Filter for channel",
        update=reset_filter
    )
    suppress_update: BoolProperty(default = False)

    levels: PointerProperty(type=LevelsProperty)
    
class LayerProperties(PropertyGroup):
    # Layer settings
    # Update layer node group by type
    def update_layer(self, context):
        if self.layer_type =="PBR":
            create_pbr_nodegroup(self)
            return
        elif self.layer_type =="FOLDER":
            create_folder_nodegroup(self)
            return
        else:
            name = getlayergroupname(self)
            if name in bpy.data.node_groups:
                create_layer_node(self)
                return
        UpdateShader()

    def update_opacity(self, context):
        sock = self.opacity_socket.get_socket()
        if sock:
            sock.default_value = self.opacity

    def update_color(self, context):
        sock = self.color_socket.get_socket()
        if sock:
            sock.default_value = self.default_color

    def update_shader(self, context):
        if self.suppress_update:
            return
        UpdateShader()
    
    def texturetypechanged(self, context):
        if self.suppress_update:
            return

        if self.texture_type == "HEIGHT":
            suppress_update = True
            self.blend_mode = "ADD"
            suppress_update = False
        UpdateShader()
    
    def get_texture_types(self, context):
        return getusedmaps()

    id: StringProperty(
        name="ID",
        default="empty"
    )
    blend_mode: EnumProperty(
        name="Blend Mode",
        items=BLEND_MODES,
        description="Blend mode for mixing layers",
        default="MIX",
        update=update_layer
    )
    texture_type: EnumProperty(
        name="Texture type",
        items=get_texture_types,
        description="Texture use type",
        update=texturetypechanged
    )
    opacity: FloatProperty(
        name="Opacity",
        description="Opacity of the layer",
        default=1.0,
        min=0.0,
        max=1.0,
        update=update_opacity
    )
    #mask_value: PointerProperty(type=SocketReference)
    mask_value: BoolProperty(default = False, name = "MaskBase", update=update_layer)
    opacity_socket: PointerProperty(type=SocketReference)

    use_layer: BoolProperty(
        name="Use Layer",
        description="Toggle layer visibility",
        default=True,
        update=update_shader
    )
    collapse_box: BoolProperty(default = False, name = "Compact Layer")

    def update_on_image(self, context):
        if self.suppress_update:
            return
        UpdateShader()

    resource: PointerProperty(type=ResourceProperty)
    expand_filters: BoolProperty(default = True)
    expand_sublayers: BoolProperty(default = True)
    lock: BoolProperty(default = False)
    mask: BoolProperty()
    node_name: StringProperty(
        default="",
        name="Node",
        description="Name of the node",
    )
    def renamebuttonupdate(self, context):
        self.renamebutton = False
    layer_name: StringProperty(
        default="",
        name="Layer name",
        description="Layer Name",
        update = renamebuttonupdate
    )
    attachedto: StringProperty(
        default="",
        name="Attached To Layer",
    )
    filters: CollectionProperty(type=FilterProperty)
    
    filter_show: BoolProperty(
        name="ShowFilters",
        description="Toggle Filters Visibility",
        default=True,
    )
    index: IntProperty()

    sub_layers: CollectionProperty(type=LayerReference)

    layer_type: EnumProperty(
        name="Layer Type",
        items=[
            ('SIMPLE', "", ""),
            ('PBR', "", ""),
            ('FILL', "", ""),
            ('FOLDER', "", ""),
        ],
        default='SIMPLE',
    )
    sort_color: StringProperty(default = "PANEL_CLOSE")

    renamebutton: BoolProperty()
    suppress_update: BoolProperty()

class TextureTypeProp(PropertyGroup):
    # Types for exporting textures
    def get_texture_types(self, context):
        tt = [ts for ts in TEXTURE_TYPE]
        tt.append(("EMPTY", "Empty", ""))
        return tt
    expand: BoolProperty(default = True)
    save_name: StringProperty(
        name="Save Name",
        default="Map",
        description="Name for saving texture",
    )

    type: EnumProperty(
        name="Alpha Type",
        items=[
            ('RGB', "RGB", ""),
            ('RGBA', "RGBA", ""),
            ('RGB_A', "RGB+A", ""),
            ('R_G_B_A', "R+G+B+A", ""),
            ('R', "R", ""),
        ],
        default='RGB',
    )
    RGB: EnumProperty(
        name="Texture type",
        items=get_texture_types,
        description="Texture use type",
        default = 9
    )
    RGBA: EnumProperty(
        name="Texture type",
        items=get_texture_types,
        description="Texture use type",
        default = 9
    )
    R: EnumProperty(
        name="Texture type",
        items=get_texture_types,
        description="Texture use type",
        default = 9
    )
    G: EnumProperty(
        name="Texture type",
        items=get_texture_types,
        description="Texture use type",
        default = 9
    )
    B: EnumProperty(
        name="Texture type",
        items=get_texture_types,
        description="Texture use type",
        default = 9
    )
    A: EnumProperty(
        name="Texture type",
        items=get_texture_types,
        description="Texture use type",
        default = 9
    )

class OtherProps(PropertyGroup):
    # Various information. Generally used for Addon settings
    def update_layer(self, context):
        UpdateShader()

    image: PointerProperty(
        name="Image",
        type=bpy.types.Image
    )

    expand_area_MtlSettings: BoolProperty(
        name="Expand Material Settings",
    )
    expand_area_Actions: BoolProperty(
        name="Expand Actions",
    )
    expand_area_Saving: BoolProperty(
        name="Expand Saving",
    )
    expand_area_Materials: BoolProperty(
        name="Expand Materials",
    )
    expand_area_CreateLayer: BoolProperty(
        name="Create layer options",
    )
    expand_area_MaterialCollection: BoolProperty(
        name="Material collection",
    )
    expand_area_ProjectTexture: BoolProperty(
        name="Projection",
    )
    expand_area_QuickEdit: BoolProperty(
        name="QuickEdit",
    )
    expand_area_PaintTools: BoolProperty(
        name="Paint Tools",
    )
    expand_area_Bake: BoolProperty(
        name="Bake",
    )
    expand_area_DepthSelection: BoolProperty(
        name="Depth Selection",
    )
    expand_area_FolderHidePJ: BoolProperty(
        name="Hide folder",
    )
    expand_area_butlayers: BoolProperty(
        name="Layers",
        default = True
    )
    expand_area_butfile: BoolProperty(
        name="File",
        default = True
    )
    expand_area_buttools: BoolProperty(
        name="Tools",
        default = True
    )
    expand_area_butmtl: BoolProperty(
        name="Material",
        default = True
    )
    expand_area_Prefs: BoolProperty(
        name="Preferences",
    )
    expand_area_DefaultMaterial: BoolProperty(
        name="Default Material",
    )
    bakemtl: PointerProperty(
        name="Bake Mtl",
        type=bpy.types.Material
    )
    save_path: StringProperty(
        name="Save Path",
        default="",
        description="Folder for texture export",
        subtype='DIR_PATH',
    )
    currentprefix: StringProperty(
        name="Prefix",
        default="",
        description="Prefix that will be used for exporting textures",
    )
    height_to_normal: BoolProperty(
        name="Bake height to normal",
        default=True,
    )
    invert_green_n: BoolProperty(
        name="Invert G channel for Normal",
        default=False,
    )
    layercombineactive: BoolProperty(
        name="LayerCombineActive",
        default=False,
    )
    toggle_save: BoolProperty(
        name="Save textures with file",
        default=True,
    )
    screen_capture_scale: FloatProperty(
        name="Screen capture scale",
        default=1.0,
        min=0.1,
        max=10.0,
        description="Scale capture scale"
    )
    screen_grab_size_y: IntProperty(
        name="Screen Grab Size Y",
        default=1024,
        min=1,
        description="Height of the screen grab"
    )
    screen_grab_size_x: IntProperty(
        name="Screen Grab Size Y",
        default=1024,
        min=1,
        description="Width of the screen grab"
    )
    new_texture_type_name: StringProperty(name="Name", default="")
    new_texture_type_label: StringProperty(name="Label", default="")
    new_texture_type_description: StringProperty(name="Description", default="")
    tempsavingdir: StringProperty(
        name="Save Projection Image Directory",
        description="Directory for images used in projection",
        default=bpy.app.tempdir,
        subtype='DIR_PATH'
    )
    preview_mode: EnumProperty(
        name="Preview Mode",
        items=[
            ('COMBINED', "Combined", ""),
            (None),
            ('DIFFUSE', "Diffuse", ""),
            ('ROUGHNESS', "Roughness", ""),
            ('METALLIC', "Metallic", ""),
            ('HEIGH', "Heigh", ""),
            ('NORMAL', "Normal", ""),
        ],
        default='COMBINED',
        update=update_layer
    )

    preview_image: PointerProperty(
        name="Image",
        type=bpy.types.Image
    )
    current_preset: StringProperty()
    fixed: BoolProperty()
    brush_size: FloatProperty(default = 20.0)
    HistogramRefs: CollectionProperty(type=HistrogramReference)

    inbufferfilter: StringProperty()
    emptyprop: BoolProperty()
    exportprops: CollectionProperty(type=TextureTypeProp)
    usedids: StringProperty()
    search: StringProperty()
    operator_running: BoolProperty()
    
class DebugPlaneProps(PropertyGroup):
    # Used for Mask by depth tool
    depth_distance: FloatProperty(
        name="Depth Distance",
        description="Distance from the view for depth mask selection",
        default=3.0,
        min=0.1
    )
    show_plane: BoolProperty(
        name="Show Plane",
        description="Toggle plane visibility",
        default=False
    )
    plane_color: FloatVectorProperty(
        name="Plane Color",
        description="Color of the plane (RGBA)",
        subtype='COLOR',
        size=4,
        default=(0.0, 0.15, 0.22, 0.25),
        min=0.0,
        max=1.0
    )
    plane_size: FloatProperty(
        name="Plane Size",
        description="Size of the plane",
        default=1.0,
        min=0.1,
        max=10.0
    )

class BakeMapSettings(PropertyGroup):
    # Settings for Bake maps. 
    type: EnumProperty(
        name="Bake Type",
        items = BAKE_TYPE,
        default='AO',
        update=lambda self, context: self.update_layer_action(context)
    )
    image: PointerProperty(
        name="Image",
        type=bpy.types.Image, 
    )
    use_map: BoolProperty(name="Bake Map", default=True)
    aodist: FloatProperty(default = 1.0, min = 0.0, max = 100.0)
    heightdist: FloatProperty(default = 1.0, min = 0.0)
    heightoffset: FloatProperty(default = 0.0)
    subd: IntProperty(default = 0, min = 0, max = 6)
    smsubd: BoolProperty(default = False)
  
class ObjectsColProperty(PropertyGroup):
    # Store and update Objects for Bake tool
    def Upd(self, context):
        part = get_material_collection()
        if not self.obj:
            
            for i, m in enumerate(part.baking_props.high_poly_obj):
                if self.obj == m.obj:
                    part.baking_props.high_poly_obj.remove(i)
                    break
            for i, m in enumerate(part.baking_props.low_poly_obj):
                if self.obj == m.obj:
                    part.baking_props.low_poly_obj.remove(i)
                    break
        if self.suppress_update:
            return
        self.suppress_update = True

        for i, m in enumerate(part.baking_props.high_poly_obj):
            if not m.obj:
                part.baking_props.high_poly_obj.remove(i)
        for i, m in enumerate(part.baking_props.low_poly_obj):
            if not m.obj:
                part.baking_props.low_poly_obj.remove(i)
        
        seen_high = set()
        for i in reversed(range(len(part.baking_props.high_poly_obj))):
            obj = part.baking_props.high_poly_obj[i].obj
            if obj in seen_high:
                part.baking_props.high_poly_obj.remove(i)
            else:
                seen_high.add(obj)

        seen_low = set()
        for i in reversed(range(len(part.baking_props.low_poly_obj))):
            obj = part.baking_props.low_poly_obj[i].obj
            if obj in seen_low:
                part.baking_props.low_poly_obj.remove(i)
            else:
                seen_low.add(obj)
        
        part.baking_props.high_poly_obj.add()
        part.baking_props.low_poly_obj.add()

        self.suppress_update = False

    suppress_update: BoolProperty()
    obj: PointerProperty(type=bpy.types.Object, update = Upd)

class BakingProperties(PropertyGroup):
    #Bake tool settings, 
    def hidehp(self, context):
        for ob in self.gethpobjects(context):
            ob.hide_set(not self.visible_hp)
    def hidelp(self, context):
        for ob in self.getlpobjects(context):
            ob.hide_set(not self.visible_lp)
    def hidecage(self, context):
        if self.cage:
            self.cage.hide_set(not self.visible_cage)
    def gethpobjects(self,context):
        objs = []
        for ob in self.high_poly_obj:
            if ob.obj:
                objs.append(ob.obj)
        return objs
    def getlpobjects(self,context):
        objs = []
        for ob in self.low_poly_obj:
            if ob.obj:
                objs.append(ob.obj)
        return objs
    bake_image_sizeY: IntProperty(
        name="Bake Image Size",
        description="Size of the bake image for all maps",
        default=1024,
        min=16,
        max=8192
    )
    bake_image_sizeX: IntProperty(
        name="Bake Image Size",
        description="Size of the bake image for all maps",
        default=1024,
        min=16,
        max=8192
    )
    smooth_cage: BoolProperty(
        name="Smooth Cage",
        description="Make the cage smooth shaded",
        default=True,
        update=lambda self, context: create_or_update_cage(context)
    )
    expand_hp: BoolProperty()
    expand_lp: BoolProperty()
    visible_hp: BoolProperty(default = True, update = hidehp)
    visible_lp: BoolProperty(default = True, update = hidelp)
    visible_cage: BoolProperty(default = True, update = hidecage)
    high_poly_obj: CollectionProperty(
        name="High Poly Object",
        description="Select the high poly object",
        type=ObjectsColProperty,
    )
    low_poly_obj: CollectionProperty(
        name="Low Poly Object",
        description="Select the low poly object",
        type=ObjectsColProperty
    )
    use_cage: BoolProperty(
        name="Use Cage",
        description="Automatically create cage with depth offset",
        default=False,
        update=lambda self, context: create_or_update_cage(context)
    )
    cage: PointerProperty(type=bpy.types.Object)
    cage_depth: FloatProperty(
        name="Cage Depth",
        description="Depth offset for cage using displacement modifier",
        default=0.1,
        min=0.0,
        max=10.0,
        update=lambda self, context: update_cage_depth(context)
    )
    cage_color: FloatVectorProperty(
        name="Cage Color",
        description="Color of the cage material",
        subtype='COLOR',
        size=4, 
        default=(0.1, 0.5, 0.6, 0.08),
        min=0.0,
        max=1.0,
        update=lambda self, context: update_cage_material(context)
    )
    cage_alpha: FloatProperty(
        name="Cage Alpha",
        description="Alpha transparency of the cage material",
        default=0.2,
        min=0.0,
        max=1.0,
        update=lambda self, context: update_cage_material(context)
    )
    samples: IntProperty(
        name="Bake Samples",
        default=12,
        min=1,
        max=8192
    )

class HASMaterialProperties(PropertyGroup):
    # Material Set Settings
    def update_layer(self, context):
        UpdateShader()
    layers: CollectionProperty(type=LayerProperties)
    sublayers: CollectionProperty(type=LayerProperties)
    
    base_layers: CollectionProperty(type=LayerReference)

    material: PointerProperty(
        name="Material",
        type=bpy.types.Material
    )
    name: StringProperty(
        default="Set",
        name="Set name",
    )
    shader_type: EnumProperty(
        name="Shader Type",
        items=[
            ('PRINCIPLED', "Principled BSDF", "Use Principled BSDF shader", "SHADING_RENDERED", 0),
            ('UNLIT', "Unlit", "Use Unlit shader", "SHADING_SOLID", 1),
            ('Custom', "Custom", "Use Custom shader", "SHADING_TEXTURE", 2),
        ],
        default='PRINCIPLED',
        update=update_layer
    )
    uvs: StringProperty(
        default="",
        name="UVs",
        description="Name of the UVs attribute",
        update=update_layer
    )
    height_intensity: FloatProperty(
        name="Height instensity",
        default=1.0,
        update=update_layer
    )
    bake_maps: CollectionProperty(type=BakeMapSettings)

    baking_props: PointerProperty(type=BakingProperties)
    
    texture_sizeX: IntProperty(
        name="Texture Size",
        description="Size of the new texture",
        default=1024,
        min=1,
        max=8192
    )
    texture_sizeY: IntProperty(
        name="Texture Size",
        description="Size of the new texture",
        default=1024,
        min=1,
        max=8192
    )

    opacity_mode: EnumProperty(
        name="Opacity Mode",
        items=[
            ('OPAQUE', "Opaque", ""),
            ('BLEND', "Blend", ""),
            ('HASHED', "Hashed", ""),
            ('CLIP', "Clip", ""),    
        ],
        default='OPAQUE',
        update=update_layer
    )
    diffusealpha: BoolProperty(
        default=False,
        name="Diffuse Transparency",
        description="Use Diffuse alpha for opacity",
        update=update_layer
    )
    used_maps: PointerProperty(type=UsedMaps)

    def update_mtl_action(self, context):
        if self.mtl_actions == 'COMBINELAYERS':
            self.combine_layers(context)
        elif self.mtl_actions == 'RESIZEALL':
            self.resize_all(context)
        elif self.mtl_actions == 'DELETEALL':
            self.delete_all_layers(context)
        elif self.mtl_actions == 'FIXSCENE':
            self.fixscene(context)
    def combine_layers(self, context):

        bpy.ops.paint.combine_all_layers('INVOKE_DEFAULT')
    def resize_all(self, context):
        bpy.ops.paint.resize_layers('INVOKE_DEFAULT')
    def delete_all_layers(self, context):
        bpy.ops.paint.delete_layers('INVOKE_DEFAULT')
    def fixscene(self, context):
        bpy.ops.paint.setupscene('INVOKE_DEFAULT')
        
    mtl_actions: EnumProperty(
        name="Layer Action",
        items=[
            ('COMBINELAYERS', "Combine Layers", "Combine Layers","NODE_COMPOSITING",0),
            ('RESIZEALL', "Resize All Layers", "Resize All Layers","MOD_EDGESPLIT",1),
            (None),
            ('FIXSCENE', "Setup Scene", "Setup current scene","SCENE_DATA",3),
            (None),
            ('DELETEALL', "Delete All Layers", "Remove all layers","TRASH",2),
        ],
        default='COMBINELAYERS',
        update=lambda self, context: self.update_mtl_action(context)
    )
    addtofolder: StringProperty()
    selected_layer: StringProperty()
    selected_alpha: BoolProperty()
    InvertG: BoolProperty(default = False, update=update_layer)
    move_layer: IntProperty()
    node: StringProperty()
    texture_filtering: EnumProperty(
        name="Texture filtering",
        items= TEXTURE_FILTER,
        default='Cubic',
        update=update_layer
    )
    colorfix: BoolProperty(default = True, update = update_layer)

class ViewData(PropertyGroup):
    # View Data for "Quick edit". Projection images from view
    image_name: StringProperty()
    image_path: StringProperty()
    render_sizeX: IntProperty()
    render_sizeY: IntProperty()
    crop_startX: IntProperty()
    crop_startY: IntProperty()
    crop_endX: IntProperty()
    crop_endY: IntProperty()
    view: StringProperty()
    loc: FloatVectorProperty(
        name="Location",
        description="Location of the camera",
        default=(0.0, 0.0, 0.0),  
        size=3, 
        subtype='TRANSLATION'
    )
    rot: FloatVectorProperty(
        name="Rotation",
        description="Rotation of the camera",
        default=(0.0, 0.0, 0.0),
        size=3, 
        subtype='EULER'
    )
    ortho: BoolProperty(default=False)
    ortho_scale: FloatProperty()
    focal: FloatProperty()

classes = [
UsedMaps,
LayerReference,
SocketReference,
NodeReference,
HistrogramReference,
LevelsProperty,
ResourceProperty,
TextureMappedProperty,
MaskGeneratorProperty,
FilterProperty,
LayerProperties,
TextureTypeProp,
OtherProps,
DebugPlaneProps,
BakeMapSettings,
ObjectsColProperty,
BakingProperties,
HASMaterialProperties,
ViewData,
]
def register():
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.material_props = CollectionProperty(type=HASMaterialProperties)
    bpy.types.Scene.other_props = PointerProperty(type=OtherProps)
    bpy.types.Scene.debugplane_props = PointerProperty(type=DebugPlaneProps)
    bpy.types.Scene.view_data = CollectionProperty(type=ViewData)

def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
    try:
        del bpy.types.Scene.selected_texture
        del bpy.types.Scene.other_props
        del bpy.types.Scene.debugplane_props
        del bpy.types.Scene.view_data
    except Exception:
        pass