import bpy
from bpy.utils import register_class, unregister_class
from bpy.props import (
    CollectionProperty,
    StringProperty,
    IntProperty,
    PointerProperty,
    BoolProperty,
    FloatVectorProperty,
    FloatProperty,
    EnumProperty,
)
from bpy.types import PropertyGroup

from ..utils.utils import *
from ..has_enum import *


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

    default_value: FloatProperty(update=updatesocket, min=0.0, max=1.0)
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
    # Store node similar to Pointer
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

    val01: FloatProperty(default=0.0, min=0.0, max=1.0, update=valupdate)
    val02: FloatProperty(default=0.5, min=0.0, max=1.0, update=valupdate)
    val03: FloatProperty(default=1.0, min=0.0, max=1.0, update=valupdate)
    val04: FloatProperty(default=0.0, min=0.0, max=1.0, update=valupdate)
    val05: FloatProperty(default=1.0, min=0.0, max=1.0, update=valupdate)

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
            ("COL", "Color", "", "EVENT_C", 0),
            (None),
            ("R", "R Channel", "", "EVENT_R", 1),
            ("G", "G Channel", "", "EVENT_G", 2),
            ("B", "B Channel", "", "EVENT_B", 3),
        ],
        update=channelswitch,
    )
    expand: BoolProperty(default=False)
    expand_levels: BoolProperty(default=False)
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
            set_default(mapping, "Location", (self.mapx, self.mapy, 0.0))
            set_default(mapping, "Rotation", (0.0, 0.0, self.maprot))
            set_default(mapping, "Scale", (self.mapscalex, self.mapscaley, 1.0))

    suppress_update: BoolProperty()
    expand: BoolProperty(default=False)
    grayscale: BoolProperty(default=False)
    image: PointerProperty(name="Image", type=bpy.types.Image, update=update)
    mapping_node: PointerProperty(type=NodeReference)
    histogram: StringProperty()

    def default_value_socket_update(self, context):
        if self.suppress_update:
            return
        self.default_color = (self.default_value, self.default_value, self.default_value, self.default_value)

    def default_color_socket_update(self, context):
        if self.suppress_update:
            return
        if self.grayscale:
            self.suppress_update = True
            self.default_color = (self.default_color[0], self.default_color[0], self.default_color[0], 1.0)
            self.suppress_update = False
        if self.default_color_socket.get_socket():
            self.default_color_socket.get_socket().default_value = self.default_color
        else:
            UpdateShader()

    default_color: FloatVectorProperty(
        name="Default Color",
        description="Default color",
        subtype="COLOR",
        size=4,
        default=(0.5, 0.5, 0.5, 1.0),
        min=0.0,
        max=1.0,
        update=default_color_socket_update,
    )
    default_color_socket: PointerProperty(type=SocketReference)

    default_value: FloatProperty(name="Default Value", default=0.5, min=0.0, max=1.0, update=default_value_socket_update)
    mapx: FloatProperty(name="Mapping Offset X", default=0, update=MappingUpdate, subtype="DISTANCE")
    mapy: FloatProperty(
        name="Mapping Offset Y",
        default=0,
        update=MappingUpdate,
        subtype="DISTANCE",
    )
    mapscalex: FloatProperty(name="Mapping Scale X", default=1.0, update=MappingUpdate)
    mapscaley: FloatProperty(name="Mapping Scale Y", default=1.0, update=MappingUpdate)
    maprot: FloatProperty(name="Mapping Rotation", default=0, update=MappingUpdate, subtype="ANGLE")

    repeat: EnumProperty(
        name="Repeat",
        items=[
            ("TILE", "Repeat XY", "Repeat Texture in All Directions"),
            ("X", "Repeat X", "Repeat Texture Horizontally"),
            ("Y", "Repeat Y", "Repeat Texture Vertically"),
            ("CLIP", "Clip", "Texture will be Clipped"),
        ],
        default="TILE",
        update=update,
    )
    expand_mapping: BoolProperty(default=False)
    levels: PointerProperty(type=LevelsProperty)


class TextureMappedProperty(PropertyGroup):
    # Mapping attached to each texture
    texture_type: EnumProperty(
        name="Type",
        items=[
            ("PAINT", "Paint Layer", ""),
            ("TEXTURE", "Texture", ""),
            ("PROC", "Procedural", ""),
        ],
        description="Texture use type",
        default="PAINT",
    )
    proc_node_type: EnumProperty(
        name="Type",
        items=[
            ("PAINT", "Paint Layer", ""),
            ("TEXTURE", "Texture", ""),
            ("PROC", "Procedural", ""),
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
    def get_item(self, item):
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
    ao_expand: BoolProperty(name="AO", default=False)
    curv_expand: BoolProperty(name="Curvature", default=False)
    pos_expand: BoolProperty(name="Position", default=False)
    objn_expand: BoolProperty(name="Object Normal", default=False)
