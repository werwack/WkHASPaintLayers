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

from .class_LayerReference import (
    LayerReference,
    NodeReference,
    HistrogramReference,
    ResourceProperty,
    TextureMappedProperty,
    MaskGeneratorProperty,
    SocketReference,
    LevelsProperty,
)

from ..utils.utils import *
from ..has_enum import *


class FilterProperties(PropertyGroup):
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
                texture_name = f".HAS_{self.id}_paint"
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
            layer_filter(get_layer_by_id(self.layer_in), multi=True)

    def valupdate(self, context):
        if self.suppress_update:
            return
        layer_filter(get_layer_by_id(self.layer_in))

    id: StringProperty(name="ID", default="empty")

    name: StringProperty(name="Filter", default="", update=reset_filter_name)
    edit: BoolProperty(
        name="Settings",
        description="Toggle filter settings",
        default=False,
    )
    in_use: BoolProperty(name="Visibility", description="Toggle filter visibility", default=True, update=update_layer)
    node_name: StringProperty(
        default="",
        name="Node",
        description="Name of the node",
    )
    mixnode: StringProperty()
    # custom_node_tree: StringProperty(update = reset_filter_name)
    custom_node_tree_p: PointerProperty(type=bpy.types.NodeTree, update=reset_custom_filter)
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

    image: PointerProperty(name="Image", type=bpy.types.Image, update=update_layer)
    resource: PointerProperty(type=ResourceProperty)
    maskgen: PointerProperty(type=MaskGeneratorProperty)
    editgrunge: BoolProperty(
        name="Grunge",
        description="Toggle Grunge settings",
        default=False,
    )
    blend_mode: EnumProperty(
        name="Blend Mode", items=BLEND_MODES, description="Blend mode for mixing layers", default="MIX", update=reset_filter
    )

    def update_opacity(self, context):
        sock = self.opacity_socket.get_socket()
        if sock:
            invGamma = 1.0 / 0.45
            opacity = pow(self.opacity, invGamma)
            # sock.default_value = self.opacity
            sock.default_value = opacity

    opacity: FloatProperty(name="Opacity", description="Opacity of the layer", default=1.0, min=0.0, max=1.0, update=update_opacity)
    opacity_socket: PointerProperty(type=SocketReference)
    Unspval: FloatProperty(default=1.0, min=0.0, update=valupdate)
    connection_type: EnumProperty(
        name="Filter Type",
        items=[
            ("COLOR", "Color", ""),
            ("ALPHA", "Alpha", ""),
            ("UV", "UV", ""),
        ],
    )

    def get_texture_types(self, context):
        return getusedmaps()

    affect_channels: EnumProperty(name="Channel", items=get_texture_types, description="Filter for channel", update=reset_filter)
    suppress_update: BoolProperty(default=False)

    levels: PointerProperty(type=LevelsProperty)


# classes = [
#     FilterProperties,
# ]


# def register():
#     for cls in classes:
#         register_class(cls)


# def unregister():
#     for cls in reversed(classes):
#         unregister_class(cls)
