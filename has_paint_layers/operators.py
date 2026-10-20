import bpy
from bpy.utils import register_class, unregister_class
from bpy.props import  StringProperty, IntProperty, BoolProperty, EnumProperty
from bpy.types import Operator
import webbrowser
from .utils import *
from .has_enum import *

class TextureSizeAddSubtract(Operator):
    bl_idname = "paint.texture_size_add_subtract"
    bl_label = "Add or subtract from texture size"
    bl_options = {'REGISTER', 'UNDO'}

    add: BoolProperty(name="AddSubtract", default=True)
    isbake: BoolProperty()
    
    def execute(self, context):
        part = get_material_collection()
        if self.isbake:
            part.baking_props.bake_image_sizeX, part.baking_props.bake_image_sizeY = texture_size_p2(self.add, part.baking_props.bake_image_sizeX, part.baking_props.bake_image_sizeY)
        else:
            part.texture_sizeX, part.texture_sizeY = texture_size_p2(self.add, part.texture_sizeX, part.texture_sizeY)  
        return {'FINISHED'}

class SetupMaterial(Operator):
    bl_idname = "paint.setup_material"
    bl_label = "Setup Material"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        setup_material(bpy.context.active_object)
        return {'FINISHED'}

class HASRemoveMaterial(Operator):
    bl_idname = "paint.remove_material"
    bl_label = "Remove Material"
    bl_options = {'REGISTER', 'UNDO'}
    index: IntProperty()
    def execute(self, context):
        context.scene.material_props.remove(self.index)
        return {'FINISHED'}

class WM_OT_OpenWebsite(Operator):
    bl_idname = "paint.open_website"
    bl_label = "Help"
    bl_description = "Open Documentation for HAS Paint Layers"
    link: StringProperty()
    def execute(self, context):
        webbrowser.open(self.link)
        return {'FINISHED'}

class CustomNewImageOperator(Operator):
    bl_idname = "paint.custom_new"
    bl_label = "Add Layer"
    bl_options = {'REGISTER', 'UNDO'}

    fill: BoolProperty(default=False)

    def execute(self, context):
        new_layer(fill = self.fill)
        return {'FINISHED'}

class CreatePBRLayer(Operator):
    bl_idname = "paint.create_pbr"
    bl_label = "PBR Layer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        new_pbr_layer()

        return {'FINISHED'}

class IsolateImage(Operator):
    bl_idname = "paint.isolate_image"
    bl_label = "Isolate Image"
    bl_options = {'REGISTER', 'UNDO'}

    texture_name: StringProperty()

    def execute(self, context):
        isolate_image(self.texture_name)
        return {'FINISHED'}

    def invoke(self, context, event):
        close_panel(event)
        return self.execute(context)

class CreateFolderOperator(Operator):
    bl_idname = "paint.create_folder"
    bl_label = "Folder"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        new_folder_layer()
        return {'FINISHED'}

class UncheckLayerOperator(Operator):
    bl_idname = "paint.uncheck_layer"
    bl_label = "Uncheck Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    def execute(self, context):

        layer = getlayer(self.layer_index)

        if layer:
            layer.use_layer = not layer.use_layer
            return {'FINISHED'}
        return {'FINISHED'}

class MoveLayerOperator(Operator):
    bl_idname = "paint.move_layer"
    bl_label = "Move Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    direction: EnumProperty(items=[('UP', 'Up', ''), ('DOWN', 'Down', '')])
    parent: IntProperty(default = -1)

    def execute(self, context):
        
        part = get_material_collection()
        index = self.layer_index
        if self.parent == -1:
            alt = False
            layers =part.base_layers
        else:
            alt= True
            layers = part.base_layers[self.parent].get_layer().sub_layers
        
        new_index = index + 1 if self.direction == 'UP' else index - 1

        if 0 <= new_index < len(layers):
            layers.move(index, new_index)
            UpdateShader()
        return {'FINISHED'}

class MoveFilterOperator(Operator):
    bl_idname = "paint.move_filter"
    bl_label = "Move Filter"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    filter_index: IntProperty()
    direction: EnumProperty(items=[('UP', 'Up', ''), ('DOWN', 'Down', '')])

    def execute(self, context):
        layer = getlayer(self.layer_index)
        filter = getfilter(self.layer_index, self.filter_index)
        ind = self.filter_index
        new_index = ind + 1 if self.direction == 'UP' else ind - 1
        if 0 <= new_index < len(layer.filters):
            layer.filters.move(ind, new_index)
            UpdateShader()
        return {'FINISHED'}

class SelectTextureOperator(Operator):
    bl_idname = "paint.select_texture"
    bl_label = "Select Texture"
    bl_options = {'REGISTER', 'UNDO'}

    texture_name: StringProperty()
    id: StringProperty()
    alpha: StringProperty(default = "Skip")
    def execute(self, context):
        part = get_material_collection()
        if self.texture_name:
            SelectTexture(self.texture_name)
            part.selected_layer = self.id
        elif self.id:
            SelectLayer(self.id)
        if self.alpha == "Set":
            part.selected_alpha = True
        if self.alpha == "Remove":
            part.selected_alpha = False
        
        return {'FINISHED'}
        
class SetStandardVT(Operator):
    bl_idname = "paint.setstandardvt"
    bl_label = "Set Standard View Transform"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.context.scene.view_settings.view_transform = 'Standard'
        return {'FINISHED'}

class SetupScene(Operator):
    bl_idname = "paint.setupscene"
    bl_label = "Setup Scene"
    bl_options = {'REGISTER', 'UNDO'}

    viewtransform: BoolProperty(name="Set View Transform to 'Standart'", default=True)

    mat: BoolProperty(name="Switch To Material Preview", default=True)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        
        bs = layout.box()
        bsr = bs.row()
        bsr.label(text= "Recommended for precise color output.")
        bsr.operator("paint.open_website", text="", icon="QUESTION")
        bs.prop(self, "viewtransform")
        
        bs = layout.box()
        bs.prop(self, "mat")

    def execute(self, context):

        if self.viewtransform:
            bpy.context.scene.view_settings.view_transform = 'Standard'
        if self.mat:
            bpy.context.space_data.shading.type = 'MATERIAL'
        bpy.context.scene.other_props.fixed = True
        return {'FINISHED'}

class SaveLayersOperators(Operator):
    bl_idname = "paint.save_layers"
    bl_label = "Save Layers"
    bl_description = "Save all textures"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        modified_images = [img for img in bpy.data.images if img.is_dirty]
        if modified_images:
            bpy.ops.image.save_all_modified()
        else:
            self.report({'INFO'}, "No images are modified.")
        return {'FINISHED'}

class DeleteLayersOperator(Operator):
    bl_idname = "paint.delete_layers"
    bl_label = "Delete layers"
    bl_description = "Delete layers from material"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Are you sure you want to delete all layers?")

    def execute(self, context):
        part = get_material_collection()
        part.base_layers.clear()
        part.layers.clear()
        UpdateShader()

        self.report({'INFO'}, "Layers deleted successfully.")
        return {'FINISHED'}

class AddLayerToFolderOperator(Operator):
    bl_idname = "paint.layer_to_folder"
    bl_label = "Add Layer To Folder"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()

    def execute(self, context):
        part = get_material_collection()

        curlayer = part.layers[self.layer_index]

        folderlayer = getbyid(part.addtofolder)
        
        subls = get_layers(folderlayer.sub_layers)

        folditem = get_layer_in_list(part.base_layers, folderlayer.id)
        curitem = get_layer_in_list(part.base_layers, curlayer.id)
        
        contains = curlayer in subls
        if not contains:
            reassign_layer(part.base_layers, folderlayer.sub_layers, curlayer.id, parent = folderlayer)
            if folditem.index < curitem.index:
                folderlayer.sub_layers.move(len(folderlayer.sub_layers)-1,0)
        else:
            for i, l in enumerate(reversed(subls)):
                if curlayer==l:
                    reassign_layer(folderlayer.sub_layers, part.base_layers, curlayer.id)
                    part.base_layers.move(len(part.base_layers)-1,folditem.index)
                    break

        UpdateShader()
        return {'FINISHED'}

class StartAddToFolderOperator(Operator):
    bl_idname = "paint.startaddtofolder"
    bl_label = "Add Layer To Folder"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()

    def execute(self, context):
        part = get_material_collection()
        if not part.addtofolder:
            part.addtofolder = part.layers[self.layer_index].id
        else:
            part.addtofolder = ''

        return {'FINISHED'}

class DuplicateLayerOperator(Operator):
    bl_idname = "paint.duplicate_layer"
    bl_label = "Duplicate Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()

    def execute(self, context):
        part = get_material_collection()
        
        for i, l in enumerate(get_layers(part.base_layers)):
            if i==self.layer_index:
                nwl = part.layers.add()

                col_copy(l, nwl)
                nwlf = part.base_layers.add()
                nwlf.id = nwl.id

                UpdateShader()
                return {'FINISHED'}
        return {'CANCELLED'}
    
class OpenImageOperator(Operator):
    bl_idname = "paint.open_image_file"
    bl_label = "Open Image File"
    bl_description = "Open file browser to select an image"

    filepath: StringProperty(
        name="File Path",
        description="Path to the image file",
        maxlen=1024,
        subtype='FILE_PATH'
    )
    layer_index: IntProperty()
    def execute(self, context):
        get_material_collection().layers[self.layer_index].resource.image = bpy.data.images.load(self.filepath)
        
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class UnlinkImageOperator(Operator):
    bl_idname = "paint.unlinkimage"
    bl_label = "Unlink"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    def execute(self, context):

        layer = getlayer(self.layer_index)

        if layer:
            layer.resource.image = None
            return {'FINISHED'}
        return {'FINISHED'}

class SetUsedMaps(Operator):
    bl_idname = "paint.setusedmaps"
    bl_label = "Select used maps"
    bl_description = "Maps that will be used in material and layers"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):

        part = get_material_collection()
        layout = self.layout
        column = layout.column(align=True)
        column.prop(part.used_maps, "Diffuse", toggle=True)
        column.prop(part.used_maps, "Roughness", toggle=True)
        column.prop(part.used_maps, "Metallic", toggle=True)
        column.prop(part.used_maps, "Normal", toggle=True)
        column.prop(part.used_maps, "Height", toggle=True)
        column.prop(part.used_maps, "Emission", toggle=True)
        column.prop(part.used_maps, "Alpha", toggle=True)
        column.prop(part.used_maps, "AO", toggle=True)
        column.prop(part.used_maps, "Custom", toggle=True)

    def execute(self, context):
        return {'FINISHED'}

class RenameLayer(Operator):
    bl_idname = "paint.rename_layer"
    bl_label = "Rename Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    new_name: StringProperty(name="New Name", default="")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "new_name")

    def execute(self, context):
        layer = getlayer(self.layer_index)
        if layer and layer.resource.image:
            layer.resource.image.name = self.new_name
            self.report({'INFO'}, f"Layer renamed to '{self.new_name}'")
        else:
            self.report({'WARNING'}, "Layer or image not found")
        return {'FINISHED'}

    def invoke(self, context, event):
        layer = getlayer(self.layer_index)
        if layer:
            self.new_name = layer.resource.image.name
        return context.window_manager.invoke_props_dialog(self)

class RemoveLayer(Operator):
    bl_idname = "paint.remove_layer"
    bl_label = "Remove Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    deletetexture: BoolProperty(default= True)

    def execute(self, context):
        part = get_material_collection()
        layer = part.layers[self.layer_index]
        if layer:
            remove_references(layer)
            part.addtofolder = ""
            UpdateShader()
        return {'FINISHED'}
    def invoke(self, context, event):
        close_panel(event)
        return self.execute(context)

class SetSortColorOperator(Operator):
    bl_idname = "paint.set_color"
    bl_label = "Uncheck Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    color: StringProperty(default = "PANEL_CLOSE")
    def execute(self, context):
        layer = getlayer(self.layer_index)
        layer.sort_color = self.color
        return {'FINISHED'}

class OtherActionsOperator(Operator):
    bl_idname = "paint.otheractions"
    bl_label = "Action"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    action: StringProperty()
    def execute(self, context):
        layer = getlayer(self.layer_index)
        part = get_material_collection()
        if layer:
            if self.action == "ADDFILTER":
                fil = layer.filters.add()
                fil.id = shortid()
                fil.connection_type = "ALPHA" if part.selected_alpha else 'COLOR'
                UpdateShader()

            if self.action == "ADDPAINT":
                fil = layer.filters.add()
                fil.suppress_update = True
                fil.id = shortid()
                fil.connection_type = "ALPHA" if part.selected_alpha else 'COLOR'
                fil.name = 'PAINT'
                if not fil.resource.image:
                    texture_name = f'.HAS_{fil.id}_paint'
                    ims = bpy.data.images.get(texture_name)
                    if ims:
                        fil.resource.image = ims
                    else:
                        fil.resource.image = newimage(texture_name)
                fil.suppress_update = False
                UpdateShader()
            if self.action == "ADDFILL":
                fil = layer.filters.add()
                fil.suppress_update = True
                fil.id = shortid()
                fil.connection_type = "ALPHA" if part.selected_alpha else 'COLOR'
                fil.resource.grayscale = part.selected_alpha
                fil.name = 'FILL'
                fil.suppress_update = False
                UpdateShader()
            elif self.action == "DUPL":
                new_layer = part.layers.add()
                new_layer.suppress_update = True
                new_layer.id = shortid()
                nef = part.base_layers.add()
                nef.id = new_layer.id
                
                copy_layer(layer, new_layer)
                node_group = bpy.data.node_groups.get(f"{getlayergroupname(layer)}_filters")

                node_group_copy = node_group.copy()
                node_group_copy.name = f"{getlayergroupname(new_layer)}_filters"

                new_layer.layer_name = f"{layer.layer_name}_copy"

                new_layer.suppress_update = False
                UpdateShader()
            elif self.action == "ADDMASK":
                layer.mask = True
                UpdateShader()

            elif self.action == "REMOVEMASK":
                layer.mask = False
                for ind, filter in reversed(list(enumerate(layer.filters))):
                    if filter.connection_type == "ALPHA":
                        layer.filters.remove(ind)
                UpdateShader()
                
        return {'FINISHED'}
    def invoke(self, context, event):
        close_panel(event)
        return self.execute(context)
    
class SetFilterOperator(Operator):
    bl_idname = "paint.setfilter"
    bl_label = "Action"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    filter_index: IntProperty()
    action: StringProperty()
    def execute(self, context):
        layer = getlayer(self.layer_index)
        filter = layer.filters[self.filter_index]
        filter.name = self.action
        return {'FINISHED'}
    def invoke(self, context, event):
        close_panel(event)
        return self.execute(context)

class SetTypeOperator(Operator):
    bl_idname = "paint.settype"
    bl_label = "Action"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    action: StringProperty()
    def execute(self, context):
        layer = getlayer(self.layer_index)
        layer.texture_type = self.action
        return {'FINISHED'}
    def invoke(self, context, event):
        close_panel(event)
        return self.execute(context)

class CleanupData(Operator):
    bl_idname = "paint.cleanup"
    bl_label = "Cleanup HAS Data"
    bl_options = {'REGISTER', 'UNDO'}

    remove_all_has_data: BoolProperty(default = False)
    clear_unused_blocks: BoolProperty(default = True)

    def draw(self, context):
        layout = self.layout

        rsb = layout.column()

        rsbr = rsb.row()
        rsbr.prop(self, "clear_unused_blocks", text = "Clear Unused HAS Data", icon = 'FAKE_USER_ON')
        rsbr.enabled = not self.remove_all_has_data
        rsbr = rsb.row()
        rsbr.prop(self, "remove_all_has_data", text = "Remove All HAS Data", icon = 'TRASH')
        sda = ""
        if self.clear_unused_blocks:
            sda = "Clear Unused HAS Data"
        if self.remove_all_has_data:
            sda = "Remove All HAS Data"
        if sda:
            bsrs = rsb.box().column(align = True)
            bsrs.label(icon = 'ERROR', text = f"Will {sda}!")
            bsrs.label(text = "including textures, node groups and materials")
            bsrs = rsb.box().column(align = True)
            bsrs.label(text = "Affects only data blocks that start with")
            bsrs.label(text = "'.HAS_' or 'HASM'")
    def execute(self, context):
        if self.clear_unused_blocks or self.remove_all_has_data:
            if self.clear_unused_blocks:
                clear_unused_layers()
            for ng in bpy.data.node_groups:
                if ng.name.startswith(".HAS_"):
                    if ng.users == 0 or self.remove_all_has_data:
                        bpy.data.node_groups.remove(ng)
            for img in bpy.data.images:
                if img.name.startswith(".HAS_"):
                    if img.users == 0 or self.remove_all_has_data:
                        bpy.data.images.remove(img)
            if self.remove_all_has_data:
                curscene = bpy.context.scene
                mtlprops = curscene.material_props
                while len(mtlprops) > 0:
                    mtlprops.remove(0)
            
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class SaveImageOperator(bpy.types.Operator):
    bl_idname = "paint.save_image"
    bl_label = "Save Image"
    bl_description = "Save the active image"

    image_name: StringProperty()

    def execute(self, context):
        try:
            image = bpy.data.images.get(self.image_name)
            if image:
                image.pack()
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save image: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}

class AddHASImage(Operator):
    bl_idname = "paint.add_has_image"
    bl_label = "Add HAS Image"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()

    def execute(self, context):
        part = get_material_collection()
        layer = getlayer(self.layer_index)
        layer.resource.image = newimage(newimagename(layer.name))
        return {'FINISHED'}

### Filters

class RemoveTextureTypeProp(Operator):
    bl_idname = "paint.remove_texture_type_prop"
    bl_label = "Remove Texture Type"
    bl_options = {'REGISTER', 'UNDO'}
    index: IntProperty()

    def execute(self, context):
        context.scene.other_props.exportprops.remove(self.index)

        return {'FINISHED'}

class RemoveFilter(Operator):
    bl_idname = "paint.remove_layer_filter"
    bl_label = "Remove Layer Filter"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    filter_index: IntProperty()
    def execute(self, context):
        layer = getlayer(self.layer_index)
        for ind, filter in enumerate(layer.filters):
            if ind == self.filter_index:
                layer.filters.remove(ind)
                UpdateShader()
                return {'FINISHED'}

class ShowHideFilter(Operator):
    bl_idname = "paint.showhidefilter"
    bl_label = "Remove Layer Filter"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    filter_index: IntProperty()
    compfilter: BoolProperty()

    def execute(self, context):
        part = get_material_collection()

        layer = part.layers[self.layer_index]

        filters = layer.filters

        for ind, filter in enumerate(filters):
            
            if ind == self.filter_index:
               
                filter.in_use = not filter.in_use
                
                UpdateShader()
                return {'FINISHED'}
        return {'CANCELLED'}

class ActivateTab(Operator):
    bl_idname = "paint.activate_tab"
    bl_label = "Tab"

    activate_tab: IntProperty()

    def execute(self, context):
        
        context.scene.other_props.expand_area_QuickEdit = False
        context.scene.other_props.expand_area_DepthSelection = False
        context.scene.other_props.expand_area_PaintTools = False
        context.scene.other_props.expand_area_Bake = False
        if self.activate_tab == 0:
            context.scene.other_props.expand_area_QuickEdit = True
        if self.activate_tab == 1:
            context.scene.other_props.expand_area_DepthSelection = True
        if self.activate_tab == 2:
            context.scene.other_props.expand_area_PaintTools = True
        if self.activate_tab == 3:
            context.scene.other_props.expand_area_Bake = True
        return {'FINISHED'}

class AddFilter(Operator):
    bl_idname = "paint.add_layer_filter"
    bl_label = "Add Filter"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    type: StringProperty()

    def execute(self, context):
        part = get_material_collection()
        layer = part.layers[self.layer_index]
        fil = layer.filters.add()
        fil.suppress_update = True
        fil.id = shortid()
        fil.name = self.type
        fil.connection_type = "ALPHA"
        if self.type == "PAINT":
            
            if not fil.resource.image:
                texture_name = f'.HAS_{fil.id}_paint'
                ims = bpy.data.images.get(texture_name)
                if ims:
                    fil.resource.image = ims
                else:
                    fil.resource.image = newimage(texture_name)
        fil.resource.grayscale = True
        
        fil.suppress_update = False

        UpdateShader()
        return {'FINISHED'}

class AddMaskGenBlock(Operator):
    bl_idname = "paint.addmaskgenblock"
    bl_label = "Add Mask Generator Block"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    filter_index: IntProperty()

    def execute(self, context):
        layer = getlayer(self.layer_index)
        for ind, filter in enumerate(layer.filters):
            if ind == self.filter_index:
                filter.maskgen.add()
                UpdateShader()
                return {'FINISHED'}

class RemoveMaskGenBlock(Operator):
    bl_idname = "paint.removemaskgenblock"
    bl_label = "Add Mask Generator Block"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    filter_index: IntProperty()
    mask_index: IntProperty()
    def execute(self, context):
        layer = getlayer(self.layer_index)
        for ind, filter in enumerate(layer.filters):
            if ind == self.filter_index:
                filter.maskgen.remove(self.mask_index)
                UpdateShader()
                return {'FINISHED'}                

class FilterChangeInOut(Operator):
    bl_idname = "paint.filter_inout"
    bl_label = "Change Filter Input/Output"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    filter_index: IntProperty()
    inpout: BoolProperty()
    inputind: IntProperty()
    def execute(self, context):
        layer = getlayer(self.layer_index)
        for ind, filter in enumerate(layer.filters):
            if ind == self.filter_index:
                if self.inpout:
                    filter.socket_in=self.inputind
                else:
                    filter.socket_out=self.inputind
                UpdateShader()
                return {'FINISHED'}

class UpdateHist(Operator):
    bl_idname = "paint.update_hist"
    bl_label = "Update Histogram"
    bl_options = {'REGISTER', 'UNDO'}

    texture_name: StringProperty()

    def execute(self, context):
        set_histogram(self.texture_name, get_image_histogram(self.texture_name, num_bins=20, sample_rate=0.01))
        update_hist_display(self.texture_name)
        return {'FINISHED'}

classes = [
TextureSizeAddSubtract,
SetupMaterial,
HASRemoveMaterial,
WM_OT_OpenWebsite,
CustomNewImageOperator,
CreatePBRLayer,
IsolateImage,
CreateFolderOperator,
UncheckLayerOperator,
MoveLayerOperator,
MoveFilterOperator,
SelectTextureOperator,
SetStandardVT,
SetupScene,
SaveLayersOperators,
DeleteLayersOperator,
AddLayerToFolderOperator,
StartAddToFolderOperator,
DuplicateLayerOperator,
OpenImageOperator,
UnlinkImageOperator,
SetUsedMaps,
RenameLayer,
RemoveLayer,
SetSortColorOperator,
OtherActionsOperator,
SetFilterOperator,
SetTypeOperator,
CleanupData,
SaveImageOperator,
AddHASImage,
RemoveTextureTypeProp,
RemoveFilter,
ShowHideFilter,
ActivateTab,
AddFilter,
AddMaskGenBlock,
RemoveMaskGenBlock,
FilterChangeInOut,
UpdateHist,
]

def register():
    for cls in classes:
        register_class(cls)

def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
