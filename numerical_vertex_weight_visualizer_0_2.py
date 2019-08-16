bl_info = {
    'name': 'Weight Visualiser',
    'author': 'Bartius Crouch, CoDEmanX, hikariztw',
    'version': (0, 0, 1),
    'blender': (2, 80, 0),
    'location': 'View3D > Properties panel > Mesh Display tab (edit-mode)',
    'category': '3D View'}


import bpy
import bgl
import blf
import mathutils


# calculate locations and store them as ID property in the mesh

def draw_callback_px(self, context):
    # polling

    # if context.mode != "EDIT_MESH" and context.mode != "PAINT_WEIGHT":
    #     return

    # get screen information

    region = context.region
    mid_x = region.width / 2
    mid_y = region.height / 2
    width = region.width
    height = region.height

    # get matrices

    view_mat = context.space_data.region_3d.perspective_matrix
    ob_mat = context.active_object.matrix_world
    total_mat = view_mat @ ob_mat

    blf.size(0, 13, 72)

    def draw_index(r, g, b, index, center):

        vec = total_mat @ center # order is important

        # dehomogenise

        vec = mathutils.Vector((vec[0] / vec[3], vec[1] / vec[3], vec[2] / vec[3]))
        x = int(mid_x + vec[0] * width / 2)
        y = int(mid_y + vec[1] * height / 2)

        # bgl.glColorMask(1,1,1,1)
        blf.position(0, x, y, 0)
        if isinstance(index,float):
            blf.draw(0, '{:.2f}'.format(index))
        else:
            blf.draw(0, str(index))


    scene = context.scene
    me = context.active_object.data

    if scene.live_mode:
        me.update()

    if scene.display_weight:
        vg = context.object.vertex_groups.active

        for v in me.vertices:
            try:
                weight = vg.weight(v.index)
                draw_index(1.0, 1.0, 1.0, weight, v.co.to_4d())
            except Exception as e:
                continue


# operator

class WeightVisualiser(bpy.types.Operator):
    bl_idname = "view3d.weight_visualiser"
    bl_label = "Weight Visualiser"
    bl_description = "Toggle the visualisation of Weight"

    _handle = None

    @classmethod
    def poll(cls, context):
        return True

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        # removal of callbacks when operator is called again

        if context.scene.display_weight_run == -1:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            context.scene.display_weight_run = 0
            return {"CANCELLED"}

        return {"PASS_THROUGH"}

    def invoke(self, context, event):
        if context.area.type == "VIEW_3D":
            if context.scene.display_weight_run != 1:
                # operator is called for the first time, start everything

                context.scene.display_weight_run = 1
                self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px,
                    (self, context), 'WINDOW', 'POST_PIXEL')
                context.window_manager.modal_handler_add(self)
                return {"RUNNING_MODAL"}
            else:
                # operator is called again, stop displaying

                context.scene.display_weight_run = -1
                return {'RUNNING_MODAL'}
        else:
            self.report({"WARNING"}, "View3D not found, can't run operator")
            return {"CANCELLED"}


# defining the panel

def menu_func(self, context):
    self.layout.separator()
    col = self.layout.column(align=True)
    col.operator(WeightVisualiser.bl_idname, text="Visualize Weight")
    row = col.row(align=True)
    # row.active = ((context.mode=="EDIT_MESH" or context.mode=="PAINT_WEIGHT") and \
        # context.scene.display_weight_run==1)
    row.prop(context.scene, "display_weight", toggle=True)
    row = col.row(align=True)
    row.active = context.scene.display_weight_run == 1
    row.prop(context.scene, "display_sel_only")
    #row.prop(context.scene, "live_mode")



def register_properties():
    bpy.types.Scene.display_weight_run = bpy.props.IntProperty(
        name="Display Weight",
        default=0)
    bpy.types.Scene.display_sel_only = bpy.props.BoolProperty(
        name="Selected only",
        description="Only display indices of selected vertices/edges/faces",
        default=True)
    bpy.types.Scene.display_weight = bpy.props.BoolProperty(
        name="Weight",
        description="Display vertex weight", default=True)
    bpy.types.Scene.live_mode = bpy.props.BoolProperty(
        name="Live",
        description="Toggle live update of the selection, can be slow",
        default=False)

def unregister_properties():
    del bpy.types.Scene.display_weight_run
    del bpy.types.Scene.display_sel_only
    del bpy.types.Scene.display_weight
    del bpy.types.Scene.live_mode


def register():
    register_properties()
    bpy.utils.register_class(WeightVisualiser)
    bpy.types.VIEW3D_PT_view3d_properties.append(menu_func)


def unregister():
    bpy.utils.unregister_class(WeightVisualiser)
    unregister_properties()
    bpy.types.VIEW3D_PT_view3d_properties.remove(menu_func)


if __name__ == "__main__":
    register()