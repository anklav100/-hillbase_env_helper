bl_info = {
    "name": "Сhillbase_env_helper",
    "blender": (4, 0, 0),
    "category": "Object",
    "version": (1, 0, 3),
    "author": "Golubev_Dmitriy",
    "description": "Addon to help work with chillbase",
}

import bpy

# Операция для переноса материалов
class OBJECT_OT_my_button(bpy.types.Operator):
    bl_idname = "object.my_button"
    bl_label = "Transfer Materials"
    
    def execute(self, context):
        obj_1 = context.scene.obj_from
        obj_2 = context.scene.obj_to

        if not obj_1 or not obj_2:
            self.report({'WARNING'}, "Выберите оба объекта!")
            return {'CANCELLED'}
        
        if obj_1.type != 'MESH' or obj_2.type != 'MESH':
            self.report({'WARNING'}, "Оба объекта должны быть мешами!")
            return {'CANCELLED'}
        
        bpy.ops.object.mode_set(mode='OBJECT')
        
        material_indices = {}

        for poly in obj_1.data.polygons:
            material_indices[poly.index] = poly.material_index
        
        if len(obj_1.data.polygons) != len(obj_2.data.polygons):
            self.report({'WARNING'}, "Оба объекта должны иметь одинаковое количество полигонов!")
            return {'CANCELLED'}
        
        obj_2.data.materials.clear()

        for mat in obj_1.data.materials:
            if mat.name not in [m.name for m in obj_2.data.materials]:
                obj_2.data.materials.append(mat)
        
        for poly in obj_2.data.polygons:
            material_index = material_indices.get(poly.index, 0)
            poly.material_index = material_index
        
        self.report({'INFO'}, "Материалы успешно перенесены!")
        return {'FINISHED'}

# Операция для переименования UV-каналов для всех выделенных мешей
class OBJECT_OT_rename_uv(bpy.types.Operator):
    bl_idname = "object.rename_uv"
    bl_label = "Rename UV"
    
    def execute(self, context):
        selected_objects = context.selected_objects

        if not selected_objects:
            self.report({'WARNING'}, "Нет выбранных объектов!")
            return {'CANCELLED'}
        
        renamed_count = 0

        for obj in selected_objects:
            if obj.type != 'MESH':
                continue

            uv_layers = obj.data.uv_layers
            
            if len(uv_layers) == 0:
                self.report({'WARNING'}, f"У объекта {obj.name} нет UV-каналов!")
                continue
            
            for i, uv_layer in enumerate(uv_layers):
                uv_layer.name = f"UVChannel_{i + 1}"
            
            renamed_count += len(uv_layers)
        
        if renamed_count > 0:
            self.report({'INFO'}, f"Переименовано {renamed_count} UV-каналов для выбранных объектов.")
        else:
            self.report({'WARNING'}, "Ни у одного из выбранных объектов нет UV-каналов.")
        
        return {'FINISHED'}

# Операция для переименования Color Attributes для всех выделенных мешей
class OBJECT_OT_rename_vc(bpy.types.Operator):
    bl_idname = "object.rename_vc"
    bl_label = "Rename VC"
    
    def execute(self, context):
        selected_objects = context.selected_objects

        if not selected_objects:
            self.report({'WARNING'}, "Нет выбранных объектов!")
            return {'CANCELLED'}
        
        renamed_count = 0

        for obj in selected_objects:
            if obj.type != 'MESH':
                continue

            color_attributes = obj.data.color_attributes
            
            if len(color_attributes) == 0:
                self.report({'WARNING'}, f"У объекта {obj.name} нет Color Attributes!")
                continue
            
            for i, color_attr in enumerate(color_attributes):
                new_name = f"VCC Colour_{i + 1}" if len(color_attributes) > 1 else "VCC Colour"
                color_attr.name = new_name
            
            renamed_count += len(color_attributes)
        
        if renamed_count > 0:
            self.report({'INFO'}, f"Переименовано {renamed_count} Color Attributes для выбранных объектов.")
        else:
            self.report({'WARNING'}, "Ни у одного из выбранных объектов нет Color Attributes.")
        
        return {'FINISHED'}

# Операция для очистки объекта от UV, Vertex Color, sharp_edge, sharp_face и неиспользованных материалов для всех выбранных объектов
class OBJECT_OT_clean_collision(bpy.types.Operator):
    bl_idname = "object.clean_collision"
    bl_label = "Clean Collision"
    
    def execute(self, context):
        selected_objects = context.selected_objects
        
        if not selected_objects:
            self.report({'WARNING'}, "Нет выбранных объектов!")
            return {'CANCELLED'}
        
        for obj in selected_objects:
            if obj.type != 'MESH':
                continue
            
            # Удаление всех UV-каналов
            uv_layers = obj.data.uv_layers
            while uv_layers:
                uv_layers.remove(uv_layers[0])
            
            # Удаление всех Vertex Colors
            color_attributes = obj.data.color_attributes
            while color_attributes:
                color_attributes.remove(color_attributes[0])
            
            # Удаление атрибутов sharp_edge и sharp_face, если они существуют
            if "sharp_edge" in obj.data.attributes:
                obj.data.attributes.remove(obj.data.attributes["sharp_edge"])
            
            if "sharp_face" in obj.data.attributes:
                obj.data.attributes.remove(obj.data.attributes["sharp_face"])
            
            # Удаление неиспользуемых материалов
            obj.data.use_fake_user = False  # Убираем фейковое использование материалов
            used_materials = set(poly.material_index for poly in obj.data.polygons)
            
            for i in reversed(range(len(obj.data.materials))):
                if i not in used_materials:
                    obj.data.materials.pop(index=i)
            
            # Проверка на количество оставшихся материалов
            if len(obj.data.materials) > 1:
                self.report({'INFO'}, f"На объекте {obj.name} осталось больше одного материала.")
        
        self.report({'INFO'}, "Все выбранные объекты успешно очищены.")
        return {'FINISHED'}

# Панель с кнопками
class OBJECT_PT_my_panel(bpy.types.Panel):
    bl_label = "Material, UV, VC Rename, and Cleaning Panel"
    bl_idname = "OBJECT_PT_my_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Пикеры для объектов
        layout.prop(scene, "obj_from", text="Source Object")
        layout.prop(scene, "obj_to", text="Target Object")
        
        # Кнопка для переноса материалов
        layout.operator("object.my_button")
        
        # Кнопка для переименования UV
        layout.operator("object.rename_uv")
        
        # Кнопка для переименования Color Attributes
        layout.operator("object.rename_vc")
        
        # Кнопка для очистки объектов
        layout.operator("object.clean_collision")

# Регистрация классов и свойств
def register():
    bpy.utils.register_class(OBJECT_OT_my_button)
    bpy.utils.register_class(OBJECT_OT_rename_uv)
    bpy.utils.register_class(OBJECT_OT_rename_vc)
    bpy.utils.register_class(OBJECT_OT_clean_collision)
    bpy.utils.register_class(OBJECT_PT_my_panel)
    
    # Свойства для выбора объектов
    bpy.types.Scene.obj_from = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Source Object",
        description="Object to transfer materials from",
    )
    bpy.types.Scene.obj_to = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Target Object",
        description="Object to transfer materials to",
    )

# Удаление классов и свойств при отключении аддона
def unregister():
    bpy.utils.unregister_class(OBJECT_OT_my_button)
    bpy.utils.unregister_class(OBJECT_OT_rename_uv)
    bpy.utils.unregister_class(OBJECT_OT_rename_vc)
    bpy.utils.unregister_class(OBJECT_OT_clean_collision)
    bpy.utils.unregister_class(OBJECT_PT_my_panel)
    
    del bpy.types.Scene.obj_from
    del bpy.types.Scene.obj_to

# Точка входа в аддон
if __name__ == "__main__":
    register()
