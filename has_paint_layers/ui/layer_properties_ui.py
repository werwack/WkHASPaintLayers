from ..utils.utils import *


def drawlayerbox(self, context, layout, layers, masks, index, parent):
    # UI element. Paint layer box
    part = get_material_collection()

    layer = layers[index].get_layer()
    alt = True
    if layer.layer_type == "FOLDER":
        row, fold = drawfolderbox(self, context, layout, layer, masks, layer.index)
        if not fold:
            for subl in reversed(layer.sub_layers):
                drawlayerbox(self, context, row, layer.sub_layers, masks, subl.index, layer)
        return
    if layer.collapse_box:
        drawcompactlinelayerbox(self, context, layout, layers, masks, index)
        return

    box = layout.box()

    selected, selectedalpha, selnm, sameimg = is_selected(layer)

    if can_be_added_to(layer):
        lrfld = getbyid(part.addtofolder)
        if lrfld:
            split = box.split(factor=0.06)

            conts = layer in get_layers(getbyid(part.addtofolder).sub_layers)

            adf = split.operator("paint.layer_to_folder", text="", icon="PANEL_CLOSE" if conts else "ADD")
            adf.layer_index = layer.index
            box = split

    if selected and not selectedalpha:
        ics = "SNAP_FACE"
    else:
        ics = "SHADING_BBOX"
    if alt:
        ics = "SNAP_FACE" if selected else "SHADING_BBOX"

    msp = 0.25 if not alt else 0.2

    split = box.split(factor=msp)

    imsplit = split
    spim = imsplit.row(align=False)
    left_column = spim.column().row(align=False)
    left_column.scale_y = 3.2 if not alt else 2.0
    rw = left_column.row()
    rw.enabled = not layer.lock
    resources = layer.resource

    if resources.image:
        if resources.image.preview:
            rw.template_icon(resources.image.preview.icon_id, scale=1.0 if not alt else 1.0)
        else:
            rw.prop(resources, "default_color", text="", emboss=False)
    else:
        rw.prop(resources, "default_color", text="")
    csr = left_column.column(align=True)
    if layer.lock:
        csr.prop(layer, "lock", text="", icon="DECORATE_UNLOCKED", emboss=True, invert_checkbox=True)
    else:
        select_op = csr.operator("paint.select_texture", text="", icon=ics, depress=selected and not selectedalpha)
        select_op.texture_name = layer.resource.image.name if layer.resource.image else ""
        select_op.id = layer.id
        select_op.alpha = "Remove"

    right_column = split.column()
    right_column.enabled = not layer.lock
    row = right_column.row(align=False)

    uncheck_button = row.operator("paint.uncheck_layer", text="", icon="HIDE_OFF" if layer.use_layer else "HIDE_ON", emboss=False)
    uncheck_button.layer_index = layer.index

    act = row.operator("paint.layer_action", text="", icon="COLLAPSEMENU", emboss=False)
    act.layer_index = layer.index

    row.label(icon="BLANK1")

    if layer.renamebutton:
        row.prop(layer, "layer_name", text="")
    else:
        row.prop(layer, "renamebutton", text=f" {layer.layer_name} ", emboss=False)

    row.prop(layer, "collapse_box", text="", icon="RADIOBUT_OFF" if layer.sort_color == "PANEL_CLOSE" else layer.sort_color, emboss=False)

    row = right_column.row(align=True)

    if layer.layer_type == "PBR":
        if layer.mask:
            rowfe = row.row()
            select_op = rowfe.operator("paint.select_texture", text="", icon="CLIPUV_DEHLT", depress=selected and selectedalpha)
            select_op.texture_name = ""
            select_op.id = layer.id
            select_op.alpha = "Set"
            if selectedalpha:
                # if layer.mask_value.get_socket():
                #    rowfe.prop(layer.mask_value, "default_value", text="", slider = True)
                rowfe.prop(
                    layer,
                    "mask_value",
                    text="White Mask" if layer.mask_value else "Black Mask",
                    icon="SNAP_FACE" if layer.mask_value else "COLORSET_16_VEC",
                )
                addpaint = rowfe.operator("paint.add_layer_filter", text="Add Paint", icon="BRUSH_DATA")
                addpaint.layer_index = layer.index
                addpaint.type = "PAINT"
        if not selectedalpha:
            if layer.layer_type == "PBR" or layer.layer_type == "FOLDER":
                rowfe = row.row()
                rowfe.enabled = selected
                rowfe.prop(layer, "expand_sublayers", text="", icon="RENDERLAYERS")
            if layer.filters:
                rowfe = row.row()
                rowfe.enabled = selected
                rowfe.prop(layer, "expand_filters", text="", icon="SHADERFX")
            for foundsubl in get_layers(layer.sub_layers):
                if foundsubl:
                    select_op = row.operator("paint.uncheck_layer", text=f"{getlabel(foundsubl.texture_type)}", emboss=foundsubl.use_layer)
                    select_op.layer_index = foundsubl.index

        move_up = row.operator("paint.move_layer", text="", icon="TRIA_UP", emboss=not alt)
        move_up.layer_index = index

        move_up.direction = "UP"
    else:
        if alt:
            if layer.mask:
                rowfe = row.row()
                select_op = rowfe.operator("paint.select_texture", text="", icon="CLIPUV_DEHLT", depress=selected and selectedalpha)
                select_op.texture_name = ""
                select_op.id = layer.id
                select_op.alpha = "Set"
                if selectedalpha:
                    # if layer.mask_value.get_socket():
                    #    rowfe.prop(layer.mask_value, "default_value", text="", slider = True)
                    rowfe.prop(
                        layer,
                        "mask_value",
                        text="White Mask" if layer.mask_value else "Black Mask",
                        icon="SNAP_FACE" if layer.mask_value else "COLORSET_16_VEC",
                    )
                    addpaint = rowfe.operator("paint.add_layer_filter", text="Add Paint", icon="BRUSH_DATA")
                    addpaint.layer_index = layer.index
                    addpaint.type = "PAINT"
            if not selectedalpha:
                if layer.layer_type == "PBR" or layer.layer_type == "FOLDER":
                    rowfe = row.row()
                    rowfe.enabled = selected
                    rowfe.prop(layer, "expand_sublayers", text="", icon="RENDERLAYERS")
                if layer.filters:
                    rowfe = row.row()
                    rowfe.enabled = selected
                    rowfe.prop(layer, "expand_filters", text="", icon="SHADERFX")
                typeselect = row.operator("paint.type_select", text=getlabel(layer.texture_type), emboss=False)
                typeselect.layer_index = layer.index
                typeselect.current = layer.texture_type

        if not selectedalpha:
            # row.prop(layer, "blend_mode", text="", emboss=not alt)
            row.prop(layer, "blend_mode", text="", emboss=True)

            row.prop(layer, "opacity", text="Opacity" if not alt else "", emboss=True)

        move_up = row.operator("paint.move_layer", text="", icon="TRIA_UP", emboss=not alt)
        move_up.layer_index = index
        move_up.parent = parent.index if parent else -1
        move_up.direction = "UP"
        if not alt:
            row = right_column.row(align=True)

            if masks:
                rowfe = row.row()
                rowfe.enabled = selected
                rowfe.prop(layer, "expand_sublayers", text="", icon="RENDERLAYERS")
            if layer.filters:
                rowfe = row.row()
                rowfe.enabled = selected
                rowfe.prop(layer, "expand_filters", text="", icon="SHADERFX")

            if not selectedalpha:
                row.prop(layer, "texture_type", text="", emboss=not alt)

    #########################
    ## offset row
    embossComp = True

    right_column.prop(layer, "useTransform")
    if layer.useTransform:
        transformBox = right_column.box()
        transformBox.enabled = layer.useTransform

        offsetRow = transformBox.row(align=True)
        offsetRow.label(text="Parent Offset")
        offsetRow.prop(layer, "offsetX", text="X" if not alt else "", emboss=embossComp)
        offsetRow.prop(layer, "offsetY", text="Y" if not alt else "", emboss=embossComp)

        scaleRow = transformBox.row(align=True)
        scaleRow.label(text="Local Scale")
        scaleRow.prop(layer, "scaleX", text="X" if not alt else "", emboss=embossComp)
        scaleRow.prop(layer, "scaleY", text="Y" if not alt else "", emboss=embossComp)

        rotateRow = transformBox.row(align=True)
        rotateRow.label(text="Local Rotation")
        rotateRow.prop(layer, "rotateZ", text="Z" if not alt else "", emboss=embossComp)

    #########################

    move_down = row.operator("paint.move_layer", text="", icon="TRIA_DOWN", emboss=not alt)
    move_down.layer_index = index
    move_up.parent = parent.index if parent else -1
    move_down.direction = "DOWN"

    if layer.expand_sublayers:
        if layer.layer_type == "PBR":
            if selected:
                for foundsubl in get_layers(layer.sub_layers):
                    if foundsubl.use_layer:
                        rowbox = right_column.box()
                        compactlayerbox(self, context, rowbox, foundsubl, None, selected, layer)

    sel = False
    contalpha = False
    contcol = False
    if layer.expand_filters:
        for f in layer.filters:
            if f.resource.image:
                if f.resource.image.name == context.scene.selected_texture:
                    sel = True
            if f.connection_type == "ALPHA":
                contalpha = True
            elif f.connection_type == "COLOR":
                contcol = True
        if selectedalpha:
            if not contalpha:
                return right_column
        else:
            if not contcol:
                return right_column
        if layer.filters:
            if selected or sel:
                rowbox = right_column.column(align=True)
                for findex, filter in enumerate(reversed(layer.filters)):

                    if selectedalpha:
                        if not filter.connection_type == "ALPHA":
                            continue
                    else:
                        if not filter.connection_type == "COLOR":
                            continue
                    findex = len(layer.filters) - 1 - findex
                    uifilter(self, context, layer, filter, findex, rowbox, layer.index)

    return right_column


def drawcompactlinelayerbox(self, context, layout, layers, masks, index):
    # UI element. Collapsed version of layer box
    part = get_material_collection()
    layer = layers[index].get_layer()
    alt = True

    selnm = ""
    selected = layer.id == part.selected_layer
    selectedalpha = False
    if selected:
        selectedalpha = part.selected_alpha
    if layer.resource.image:
        selnm = layer.resource.image.name
        if not selectedalpha:
            selected = context.scene.selected_texture == layer.resource.image.name

    row = layout.box().row(align=True)
    if selected and not selectedalpha:
        ics = "SNAP_FACE"
    else:
        ics = "SHADING_BBOX"
    if alt:
        ics = "BLANK1"

    select_op = row.operator("paint.select_texture", text="", icon=ics, depress=selected and not selectedalpha)
    select_op.texture_name = selnm
    select_op.id = layer.id
    select_op.alpha = "Remove"

    uncheck_button = row.operator("paint.uncheck_layer", text="", icon="HIDE_OFF" if layer.use_layer else "HIDE_ON")
    uncheck_button.layer_index = layer.index

    row.prop(layer, "blend_mode", text="", emboss=False)
    row.prop(layer, "texture_type", text="", emboss=False)

    opas = row.operator("paint.opacity_controller", text=f"{round(layer.opacity*100)/100}", emboss=False)
    opas.layer_index = layer.index
    if layer.sort_color == "PANEL_CLOSE":
        if layer.renamebutton:
            row.prop(layer, "layer_name", text="")
        else:
            row.prop(layer, "renamebutton", text=layer.layer_name, emboss=False)
    else:
        if layer.renamebutton:
            row.prop(layer, "layer_name", text="")
        else:
            row.prop(layer, "renamebutton", text=layer.layer_name, emboss=False)

    move_up = row.operator("paint.move_layer", text="", icon="TRIA_UP")
    move_up.layer_index = layer.index
    move_up.direction = "UP"

    move_down = row.operator("paint.move_layer", text="", icon="TRIA_DOWN")
    move_down.layer_index = layer.index
    move_down.direction = "DOWN"
    row.prop(layer, "collapse_box", text="", icon="RADIOBUT_OFF" if layer.sort_color == "PANEL_CLOSE" else layer.sort_color, emboss=False)


def drawfolderbox(self, context, layout, layer, masks, index):
    # UI element. Folder layer box
    part = get_material_collection()
    if layer.lock:
        layout.prop(layer, "lock", text="", icon="DECORATE_UNLOCKED", emboss=False)
    box = layout.box()
    box.enabled = not layer.lock
    row = box.row(align=True)

    selected, selectedalpha, selnm, sameimg = is_selected(layer)
    select_op = row.operator("paint.select_texture", text="", icon="SNAP_FACE" if selected else "SHADING_BBOX", depress=selected)
    select_op.texture_name = selnm
    select_op.id = layer.id
    select_op.alpha = "Remove"
    if layer.mask:
        select_op = row.operator("paint.select_texture", text="", icon="CLIPUV_DEHLT", depress=selected and selectedalpha)
        select_op.texture_name = selnm
        select_op.id = layer.id
        select_op.alpha = "Set"
    row.prop(layer, "collapse_box", text="", icon=layer.sort_color, invert_checkbox=True, emboss=not layer.collapse_box)
    adf = row.operator(
        "paint.startaddtofolder",
        text="",
        icon="PLUS",
        depress=True if part.addtofolder == layer.id else False,
        emboss=True if part.addtofolder == layer.id else False,
    )
    adf.layer_index = layer.index

    uncheck_button = row.operator("paint.uncheck_layer", text="", icon="HIDE_OFF" if layer.use_layer else "HIDE_ON", emboss=False)
    uncheck_button.layer_index = index
    act = row.operator("paint.layer_action", text="", icon="COLLAPSEMENU", emboss=False)
    act.layer_index = layer.index

    if layer.filters:
        rowfe = row.row()
        rowfe.enabled = selected
        rowfe.prop(layer, "expand_filters", text="", icon="SHADERFX")

    row.label(icon="BLANK1")
    if layer.renamebutton:
        row.prop(layer, "layer_name", text="")
    else:
        row.prop(layer, "renamebutton", text=f" {layer.layer_name} ", emboss=False)

    row.prop(layer, "blend_mode", text="", emboss=False)

    opas = row.operator("paint.opacity_controller", text=f"{round(layer.opacity*100)/100}", emboss=False)
    opas.layer_index = layer.index

    move_up = row.operator("paint.move_layer", text="", icon="TRIA_UP", emboss=False)
    move_up.layer_index = index
    move_up.direction = "UP"

    move_down = row.operator("paint.move_layer", text="", icon="TRIA_DOWN", emboss=False)
    move_down.layer_index = index
    move_down.direction = "DOWN"
    right_column = box
    sel = False
    contalpha = False
    contcol = False
    if layer.expand_filters and not layer.collapse_box:
        for f in layer.filters:
            if f.resource.image:
                if f.resource.image.name == context.scene.selected_texture:
                    sel = True
            if f.connection_type == "ALPHA":
                contalpha = True
            elif f.connection_type == "COLOR":
                contcol = True
        if selectedalpha:
            if not contalpha:
                return box, layer.collapse_box
        else:
            if not contcol:
                return box, layer.collapse_box
        if layer.filters:
            if selected or sel:
                rowbox = right_column.column(align=True)
                for findex, filter in enumerate(reversed(layer.filters)):
                    if selectedalpha:
                        if not filter.connection_type == "ALPHA":
                            continue
                    else:
                        if not filter.connection_type == "COLOR":
                            continue
                    findex = len(layer.filters) - 1 - findex
                    uifilter(self, context, layer, filter, findex, rowbox, layer.index)

    return box, layer.collapse_box
