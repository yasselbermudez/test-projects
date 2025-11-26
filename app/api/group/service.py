from datetime import datetime
from fastapi import  HTTPException
from .schemas import Group,EventResponse,Member, UpdateGroup,UpdateMembers,CreateGroup

async def create_group(group_data: CreateGroup, db):
    try:
        # Crear el primer miembro (el creador)
        creator_member = Member(user_id=group_data.current_user_id, user_name=group_data.current_user_name)
        
        # Crear el grupo
        new_group = Group(
            group_name=group_data.group_name,
            members=[creator_member],
            created=datetime.now(),
            created_by=group_data.current_user_name,
            creator_id=group_data.current_user_id,
            password=group_data.password
        )
        
        # Insertar en la base de datos
        result = await db.groups.insert_one(new_group.dict())
        print("********* insert aid:",result.inserted_id)
        if result.inserted_id:
            # actualizar el grupo de el usuario

            update_result = await db.users.update_one(
                {"id": group_data.current_user_id}, 
                {"$set": {"group_id": new_group.id}}
            )
            if update_result.modified_count == 0:
                raise HTTPException(status_code=500, detail="Grupo creado pero usuario no actualizado")
            return new_group
        else: 
            raise HTTPException(status_code=404, detail="No se pudo crear el grupo")
        
    except: 
        raise HTTPException(status_code=404, detail="Error al crear el grupo")
    

async def update_members(group_id: str, update_data: UpdateMembers, db):
    # Buscar el grupo existente
    
    existing_group = await db.groups.find_one({"id": group_id})
    if not existing_group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    
    group = Group(**existing_group)
    
    # Operación de ELIMINAR miembro
    if update_data.remove:
        # Verificar que no se está intentando eliminar al creador
        if update_data.user_id == group.creator_id:
            raise HTTPException(status_code=400, detail="No se puede eliminar al creador del grupo")
        
        # Verificar que el usuario a eliminar existe en el grupo
        member_exists = any(member.user_id == update_data.user_id for member in group.members)
        if not member_exists:
            raise HTTPException(status_code=404, detail="Usuario no encontrado en el grupo")
        
        # Eliminar el miembro
        updated_members = [member for member in group.members if member.user_id != update_data.user_id]
        new_group = None
    
    # Operación de AGREGAR miembro
    else:
        # Validar que no haya más de 5 miembros
        if len(group.members) >= 5:
            raise HTTPException(status_code=400, detail="No puede haber más de 5 miembros en el grupo")
        
        # Verificar que el usuario no esté ya en el grupo
        member_exists = any(member.user_id == update_data.user_id for member in group.members)
        if member_exists:
            raise HTTPException(status_code=400, detail="El usuario ya es miembro del grupo")
        
        # Agregar el nuevo miembro
        new_member = Member(user_id=update_data.user_id, user_name=update_data.user_name)
        updated_members = group.members + [new_member]
        new_group = group_id
    
    # Actualizar el grupo en la base de datos
    await db.groups.update_one(
        {"id": group_id}, 
        {"$set": {"members": [member.dict() for member in updated_members]}}
    )
    # actualizar el grupo de el usuario
    await db.users.update_one(
        {"id": update_data.user_id}, 
        {"$set": {"group_id": new_group}}
    )
    
    # Obtener el grupo actualizado
    updated_group = await db.groups.find_one({"id": group_id})
    return Group(**updated_group)

async def update_group(group_id: str, update_data: UpdateGroup, db):
    # Buscar el grupo existente
    existing_group = await db.groups.find_one({"id": group_id})
    if not existing_group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    
    group = Group(**existing_group)
    update_dict = {}
    # Actualizar nombre si se proporciona
    #if update_data.group_name:
    #    update_dict["group_name"] = update_data.group_name
    
    # Actualizar miembros si se proporcionan
    if update_data.members:
        # Validar que no haya más de 5 miembros
        if len(update_data.members) > 5:
            raise HTTPException(status_code=400, detail="No puede haber más de 5 miembros en el grupo")
        
        # Verificar que el creador siga en el grupo
        creator_still_member = any(member.user_id == group.creator_id for member in update_data.members)
        if not creator_still_member:
            raise HTTPException(status_code=400, detail="El creador del grupo debe permanecer como miembro")
        
        update_dict["members"] = [member.dict() for member in update_data.members]
    
    # Realizar la actualización
    if update_dict:
        await db.groups.update_one({"id": group_id}, {"$set": update_dict})
        # Obtener el grupo actualizado
        updated_group = await db.groups.find_one({"id": group_id})
        return Group(**updated_group)
    
    return group

async def delete_group_by_id(group_id: str,db):
    try:
        result = await db.groups.delete_one({"id": group_id})
        
        if result.deleted_count == 1:
            return {
                "success": True,
                "message": "Grupo eliminado exitosamente",
                "deleted_id": group_id
            }
        else:
            raise HTTPException(status_code=404, detail="Grupo no encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar el grupo: {str(e)}")

async def delete_group_in_cascade(group_id: str,db):
    try:
        """
        if not ObjectId.is_valid(group_id):
            raise HTTPException(status_code=400, detail="ID de grupo inválido")
        
        object_id = ObjectId(group_id)
        """
        # 1. Verificar que el grupo existe
        grupo = await db.groups.find_one({"id": group_id})
        if not grupo:
            raise HTTPException(status_code=404, detail="Grupo no encontrado")
        
        # 2. Eliminar el grupo
        delete_result = await db.groups.delete_one({"id": group_id})
        
        if delete_result.deleted_count != 1:
            raise HTTPException(status_code=500, detail="Error al eliminar el grupo")
        
        # 3. Actualizar usuarios que tenían este group_id (eliminar referencia)
        update_result = await db.users.update_many(
            {"group_id": group_id},
            {"$set": {"group_id": None}}
        )
        
        return {
            "success": True,
            "message": "Grupo eliminado y usuarios actualizados",
            "deleted_group_id": group_id,
            "usuarios_actualizados": update_result.modified_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en eliminación: {str(e)}")