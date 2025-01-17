bl_info = {
    "name": "Сhillbase_env_helper",
    "blender": (4, 0, 0),
    "category": "Object",
    "version": (1, 0, 6),
    "author": "Golubev_Dmitriy",
    "description": "Addon to help work with chillbase",
}

import bpy
import bmesh
import math
import os
import re
from mathutils import Vector

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


# Оператор для Long Triangles
class OBJECT_OT_long_triangles(bpy.types.Operator):
    bl_idname = "object.long_triangles"
    bl_label = "Long Triangles"
    
    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'WARNING'}, "Выберите объект типа MESH.")
            return {'CANCELLED'}
        
        if context.mode != 'EDIT_MESH':
            self.report({'WARNING'}, "Перейдите в режим редактирования.")
            return {'CANCELLED'}
        
        angle_threshold = math.radians(140)
        bm = bmesh.from_edit_mesh(obj.data)
        bpy.ops.mesh.select_all(action='DESELECT')
        
        for face in bm.faces:
            if len(face.verts) == 3:
                verts = face.verts
                edges = face.edges
                
                # Вычисляем углы между вершинами
                angles = []
                for i in range(3):
                    v1 = verts[i].co
                    v2 = verts[(i + 1) % 3].co
                    v3 = verts[(i + 2) % 3].co
                    
                    vec1 = (v1 - v2).normalized()
                    vec2 = (v3 - v2).normalized()
                    angle = vec1.angle(vec2)
                    angles.append(angle)
                
                if any(angle > angle_threshold for angle in angles):
                    face.select = True
        
        bmesh.update_edit_mesh(obj.data)
        self.report({'INFO'}, "Выделены треугольники с большими углами.")
        return {'FINISHED'}

# Оператор для удаления материалов
class OBJECT_OT_delete_materials(bpy.types.Operator):
    bl_idname = "object.delete_materials"
    bl_label = "Delete All Materials"
    bl_description = "Delete all materials from selected objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        
        for obj in selected_objects:
            if obj.type == 'MESH':
                obj.data.materials.clear()
        
        self.report({'INFO'}, "All materials removed from selected objects")
        return {'FINISHED'}

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Материалы для назначения
# Словарь материалов с ключами, представляющими цвета, и их соответствующими названиями в Blender
materials = {
    "green": "id100_r_land_02",
    "red": "id231_stn_03",
    "blue": "id55_sand_01",
    "default": "id165_wild_grass_5",
}

# Переменная для хранения пути к текстурам
# Создаем свойство сцены для ввода пути к папке с текстурами через UI
bpy.types.Scene.texture_folder_path = bpy.props.StringProperty(
    name="Texture Folder",
    description="Path to the folder with textures",
    default="",
    subtype='DIR_PATH'
)

# Функция для вычисления UDIM на основе UV-координат
# UDIM - это система, используемая для текстурирования с использованием плиток

def get_udim_from_uv(uv):
    udim_base = 1001  # Базовый индекс UDIM
    udim_x = int(uv.x)  # Координата X
    udim_y = int(uv.y)  # Координата Y
    return udim_base + udim_x + (udim_y * 10)

# Функция для извлечения UDIM из имени текстуры
# Например, из имени '1002_BC' будет извлечено 1002

def get_udim_from_texture_name(name):
    parts = name.split("_")
    if len(parts) > 0 and parts[0].isdigit():
        return int(parts[0])
    return None

# Функция для получения цвета пикселя из текстуры на основе UV-координат

def get_pixel_color(image, uv):
    x = int(uv.x * image.size[0]) % image.size[0]  # Координата X пикселя
    y = int(uv.y * image.size[1]) % image.size[1]  # Координата Y пикселя
    pixel_index = (y * image.size[0] + x) * 4  # Индекс пикселя в массиве
    return image.pixels[pixel_index:pixel_index + 3]  # Возвращаем только RGB

# Функция для назначения материалов на основе цвета текстуры

def assign_materials_to_mesh(mesh_obj, images_by_udim, material_map):
    bm = bmesh.new()
    bm.from_mesh(mesh_obj.data)

    # Получаем второй UV-канал
    uv_layer = bm.loops.layers.uv.get("UVChannel_2")
    if not uv_layer:
        print(f"UVChannel_2 не найден на меше {mesh_obj.name}.")
        bm.free()
        return

    # Создаем словарь для быстрого доступа к индексам материалов
    material_index_map = {key: mesh_obj.data.materials.find(mat.name) for key, mat in material_map.items()}

    # Обрабатываем каждый полигон
    for face in bm.faces:
        center_uv = Vector((0.0, 0.0))
        for loop in face.loops:
            center_uv += loop[uv_layer].uv
        center_uv /= len(face.loops)

        udim = get_udim_from_uv(center_uv)
        image = images_by_udim.get(udim)

        if not image:
            print(f"Текстура для UDIM {udim} не найдена. Пропуск полигона.")
            continue

        # Получаем цвет пикселя
        color = get_pixel_color(image, center_uv)
        if color[0] > 0.5 and color[1] < 0.5 and color[2] < 0.5:
            material_key = "red"
        elif color[0] < 0.5 and color[1] > 0.5 and color[2] < 0.5:
            material_key = "green"
        elif color[0] < 0.5 and color[1] < 0.5 and color[2] > 0.5:
            material_key = "blue"
        else:
            material_key = "default"

        # Назначаем материал полигону
        if material_index_map[material_key] != -1:
            face.material_index = material_index_map[material_key]
        else:
            print(f"Материал '{material_key}' не найден для объекта {mesh_obj.name}.")

    bm.to_mesh(mesh_obj.data)
    bm.free()

# Функция для назначения текстур на основе UDIM

def assign_textures_to_meshes_from_folder(folder_path):
    if not os.path.exists(folder_path):
        print(f"Папка {folder_path} не найдена.")
        return

    texture_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.bmp'))]
    images_by_udim = {}
    for texture_file in texture_files:
        udim = get_udim_from_texture_name(texture_file)
        if udim:
            texture_path = os.path.join(folder_path, texture_file)
            try:
                image = bpy.data.images.load(texture_path, check_existing=True)
                images_by_udim[udim] = image
            except RuntimeError:
                print(f"Ошибка загрузки текстуры: {texture_path}")

    for obj in bpy.context.selected_objects:
        if obj.type != 'MESH':
            continue

        material_map = {}
        for key, mat_name in materials.items():
            mat = bpy.data.materials.get(mat_name)
            if not mat:
                mat = bpy.data.materials.new(name=mat_name)
            if mat.name not in [m.name for m in obj.data.materials]:
                obj.data.materials.append(mat)
            material_map[key] = mat

        assign_materials_to_mesh(obj, images_by_udim, material_map)
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Функция для назначения материалов на основе альфа-канала
def assign_materials_based_on_alpha(obj):
    # Проверяем, является ли объект мешем
    if obj.type != 'MESH':
        print(f"Объект {obj.name} не является типом 'MESH'. Пропуск.")
        return

    # Проверяем, есть ли атрибут цвета
    if not obj.data.color_attributes:
        print(f"Объект {obj.name} не имеет атрибутов цвета. Пропуск.")
        return

    # Переключаем объект в Object Mode, если он в Edit Mode
    if obj.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Получаем первый цветовой слой
    color_layer_name = obj.data.color_attributes[0].name

    # Работаем с полигонами объекта
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    # Добавляем цветовой слой в BMesh
    color_layer = bm.loops.layers.color.get(color_layer_name)
    if not color_layer:
        print(f"Не удалось найти Color Attribute '{color_layer_name}' в BMesh. Пропуск объекта {obj.name}.")
        bm.free()
        return

    # Проверяем, есть ли материалы в объекте
    materials = obj.data.materials
    if not materials:
        print(f"У объекта {obj.name} нет назначенных материалов. Пропуск.")
        bm.free()
        return

    # Создаём словарь материалов с ключом, равным ID материала
    material_map = {}
    for mat in materials:
        match = re.match(r"id(\d+)_", mat.name)
        if match:
            material_id = int(match.group(1))
            material_map[material_id] = mat

    if not material_map:
        print(f"Не удалось найти материалы с корректным форматом имени 'idX_' для объекта {obj.name}. Пропуск.")
        bm.free()
        return

    # Назначаем материалы полигонам на основе альфа-канала
    for face in bm.faces:
        # Получаем значение альфа-канала из первой вершины (допущение: оно одинаково для всех вершин полигона)
        alpha_value = face.loops[0][color_layer][3]

        # Вычисляем ближайший материал ID
        material_id = round(alpha_value / 0.003906)

        # Проверяем, есть ли соответствующий материал
        if material_id in material_map:
            face.material_index = materials.find(material_map[material_id].name)
        else:
            print(f"Для альфа-значения {alpha_value:.6f} не найден соответствующий материал (ID: {material_id}).")

    # Обновляем меш и освобождаем BMesh
    bm.to_mesh(obj.data)
    bm.free()

    print(f"Материалы успешно назначены для объекта {obj.name}.")


# Оператор для кнопки
class OBJECT_OT_AssignMaterialsByAlpha(bpy.types.Operator):
    bl_idname = "object.assign_materials_by_alpha"
    bl_label = "Assign materials based on Alpha"
    bl_description = "Assign materials to selected objects based on alpha channel"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "Нет выбранных объектов.")
            return {'CANCELLED'}

        for obj in selected_objects:
            assign_materials_based_on_alpha(obj)
        
        self.report({'INFO'}, f"Материалы назначены для {len(selected_objects)} объектов.")
        return {'FINISHED'}

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Панель с кнопками
class OBJECT_PT_my_panel(bpy.types.Panel):
    bl_label = "Сhillbase env helper"
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
        
        # Кнопка для Long Triangles
        layout.operator("object.long_triangles")
        
        # Кнопка для удаления материалов
        layout.operator("object.delete_materials", icon='MATERIAL')

        # Кнопка для назначения материалов и путь к текстурам
        layout.prop(context.scene, "texture_folder_path")
        layout.operator("object.assign_materials_from_color", text="Assign Materials from Color", icon='MATERIAL')
        
         # Кнопка для назначения материалов из альфы
        layout.operator("object.assign_materials_by_alpha", icon='MATERIAL')

        # Оператор для кнопки
class OBJECT_OT_AssignMaterials(bpy.types.Operator):
    bl_idname = "object.assign_materials_from_color"
    bl_label = "Assign Materials from Color"
    
    def execute(self, context):
        folder_path = context.scene.texture_folder_path
        assign_textures_to_meshes_from_folder(folder_path)
        return {'FINISHED'}

     
# Регистрация классов и свойств
def register():
    bpy.utils.register_class(OBJECT_OT_my_button)
    bpy.utils.register_class(OBJECT_OT_rename_uv)
    bpy.utils.register_class(OBJECT_OT_rename_vc)
    bpy.utils.register_class(OBJECT_OT_clean_collision)
    bpy.utils.register_class(OBJECT_OT_long_triangles)
    bpy.utils.register_class(OBJECT_OT_delete_materials)
    bpy.utils.register_class(OBJECT_OT_AssignMaterials)
    bpy.utils.register_class(OBJECT_OT_AssignMaterialsByAlpha)
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
    bpy.types.Scene.texture_folder_path = bpy.props.StringProperty(
        name="Texture Folder",
        description="Path to the folder with textures",
        default="",
        subtype='DIR_PATH'
    )


# Удаление классов и свойств при отключении аддона
def unregister():
    bpy.utils.unregister_class(OBJECT_OT_my_button)
    bpy.utils.unregister_class(OBJECT_OT_rename_uv)
    bpy.utils.unregister_class(OBJECT_OT_rename_vc)
    bpy.utils.unregister_class(OBJECT_OT_clean_collision)
    bpy.utils.unregister_class(OBJECT_OT_long_triangles)
    bpy.utils.unregister_class(OBJECT_OT_delete_materials)
    bpy.utils.unregister_class(OBJECT_OT_AssignMaterials)
    bpy.utils.unregister_class(OBJECT_OT_AssignMaterialsByAlpha)
    bpy.utils.unregister_class(OBJECT_PT_my_panel)

    del bpy.types.Scene.obj_from
    del bpy.types.Scene.obj_to
    del bpy.types.Scene.texture_folder_path

# Точка входа в аддон
if __name__ == "__main__":
    register()
