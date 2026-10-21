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
)
from .class_FilterProperties import FilterProperties

from ..utils.utils import *
from ..has_enum import *


class LayerProperties(PropertyGroup):
    # Layer settings
    # Update layer node group by type
    def update_layer(self, context):
        if self.layer_type == "PBR":
            create_pbr_nodegroup(self)
            return
        elif self.layer_type == "FOLDER":
            create_folder_nodegroup(self)
            return
        else:
            name = getlayergroupname(self)
            if name in bpy.data.node_groups:
                create_layer_node(self)
                return
        UpdateShader()

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

    id: StringProperty(name="ID", default="empty")
    blend_mode: EnumProperty(
        name="Blend Mode", items=BLEND_MODES, description="Blend mode for mixing layers", default="MIX", update=update_layer
    )
    texture_type: EnumProperty(name="Texture type", items=get_texture_types, description="Texture use type", update=texturetypechanged)

    def update_opacity(self, context):
        sock = self.opacity_socket.get_socket()
        if sock:
            invGamma = 1.0 / 0.45
            opacity = pow(self.opacity, invGamma)
            # sock.default_value = self.opacity
            sock.default_value = opacity

    ## layer opacity
    opacity_socket: PointerProperty(type=SocketReference)

    opacity: FloatProperty(
        name="Opacity",
        description="Opacity of the layer 2",
        default=1.0,
        min=0.0,
        max=1.0,
        step=0.1,
        update=update_opacity,
    )

    ## layer offset
    offsetX_socket: PointerProperty(type=SocketReference)
    offsetY_socket: PointerProperty(type=SocketReference)
    scaleX_socket: PointerProperty(type=SocketReference)
    scaleY_socket: PointerProperty(type=SocketReference)
    rotateZ_socket: PointerProperty(type=SocketReference)
    textureTile_socket: PointerProperty(type=SocketReference)

    # def update_offsetX(self, context):
    #     sock = self.offsetX_socket.get_socket()
    #     if sock:
    #         # sock.default_value = [0] = self.offsetX
    #         sock.default_value[0] = self.offsetX
    #         # sock.default_value = [0, 20, 2]
    #         print(f"tot: sock name: {sock.name}, sock.default_value: {sock.default_value}")
    def update_transform(self, context):

        if self.useTransform:
            # self.textureTile_socket.get_socket().default_value[0] = self.textureTile
            self.offsetX_socket.get_socket().default_value[0] = self.offsetX - 0.5
            self.offsetY_socket.get_socket().default_value[1] = self.offsetY - 0.5
            self.scaleX_socket.get_socket().default_value[0] = self.scaleX
            self.scaleX_socket.get_socket().default_value[1] = self.scaleY
            self.rotateZ_socket.get_socket().default_value[2] = self.rotateZ
        else:
            # self.textureTile_socket.get_socket().default_value[0] = self.textureTile
            self.offsetX_socket.get_socket().default_value[0] = -0.5
            self.offsetY_socket.get_socket().default_value[1] = -0.5
            self.scaleX_socket.get_socket().default_value[0] = 1.0
            self.scaleX_socket.get_socket().default_value[1] = 1.0
            self.rotateZ_socket.get_socket().default_value[2] = 0.0

        # print(f"tot: sock name: {sock.name}, sock.default_value: {sock.default_value}")

    useTransform: BoolProperty(name="Use Transform", description="Use Transform", update=update_transform, default=False)
    textureTile: BoolProperty(name="Texture Tile", update=update_transform, default=False)

    offsetX: FloatProperty(
        name="offsetX",
        description="Offset X of the layer",
        default=0.0,
        step=0.1,
        update=update_transform,
    )
    offsetY: FloatProperty(
        name="offsetY",
        description="Offset Y of the layer",
        default=0.0,
        step=0.1,
        update=update_transform,
    )
    scaleX: FloatProperty(
        name="scaleX",
        description="Scale X of the layer",
        default=1.0,
        step=0.1,
        update=update_transform,
    )
    scaleY: FloatProperty(
        name="scaleY",
        description="Scale Y of the layer",
        default=1.0,
        step=0.1,
        update=update_transform,
    )
    rotateZ: FloatProperty(
        name="Rotate Z",
        description="Rotation of the layer",
        default=0.0,
        step=0.1,
        update=update_transform,
    )

    # mask_value: PointerProperty(type=SocketReference)
    mask_value: BoolProperty(default=False, name="MaskBase", update=update_layer)

    use_layer: BoolProperty(name="Use Layer", description="Toggle layer visibility", default=True, update=update_shader)
    collapse_box: BoolProperty(default=False, name="Compact Layer")

    def update_on_image(self, context):
        if self.suppress_update:
            return
        UpdateShader()

    resource: PointerProperty(type=ResourceProperty)
    expand_filters: BoolProperty(default=True)
    expand_sublayers: BoolProperty(default=True)
    lock: BoolProperty(default=False)
    mask: BoolProperty()
    node_name: StringProperty(
        default="",
        name="Node",
        description="Name of the node",
    )

    def renamebuttonupdate(self, context):
        self.renamebutton = False

    layer_name: StringProperty(default="", name="Layer name", description="Layer Name", update=renamebuttonupdate)
    attachedto: StringProperty(
        default="",
        name="Attached To Layer",
    )
    filters: CollectionProperty(type=FilterProperties)

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
            ("SIMPLE", "", ""),
            ("PBR", "", ""),
            ("FILL", "", ""),
            ("FOLDER", "", ""),
        ],
        default="SIMPLE",
    )
    sort_color: StringProperty(default="PANEL_CLOSE")

    renamebutton: BoolProperty()
    suppress_update: BoolProperty()
