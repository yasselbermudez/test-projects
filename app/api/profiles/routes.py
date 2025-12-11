from fastapi import APIRouter, Depends, HTTPException
from app.api.users.service import get_current_user, get_current_user_id
from app.database.database import get_database
from .schemas import Profile, ProfileUpdate,InitProfile
from .service import initialize_profile_data,initialize_summary_data

router = APIRouter()

@router.get("/groups/{group_id}",response_model = list[Profile])
async def get_profiles_data(group_id:str,db=Depends(get_database)):
    group = await db.groups.find_one({"id":group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    members = group["members"]
    user_ids = [member["user_id"] for member in members]

    profiles = await db.profiles.find({"user_id": {"$in": user_ids}}).to_list(len(members))
    return [Profile(**profile) for profile in profiles]


@router.post("/")
async def initialize_data(profile_data:InitProfile,user_id:str=Depends(get_current_user_id),db=Depends(get_database),current_user = Depends(get_current_user)):
    
    profile = await initialize_profile_data(user_id,profile_data.email,db)
    sumary = await initialize_summary_data(user_id,profile_data.email,db)
    
    return {"message": f"{profile} and {sumary}"}
 

@router.get("/{user_id}",response_model = Profile)
async def get_profile(user_id: str,db=Depends(get_database)) -> Profile:
    result = await db.profiles.find_one({"user_id": user_id})
    if not result:
        return HTTPException(status_code=404,detail="Profile not found")
    return result


@router.put("/")
async def update_profile_info(profile_info: ProfileUpdate,user_id:str=Depends(get_current_user_id), db=Depends(get_database)):
    
    update_data = profile_info.dict(exclude_none=True)
    
    try:
        result = await db.profiles.update_one(
            {"user_id": user_id}, 
            {"$set": update_data}
        )
    except Exception as e:
        print(f"Error durante la actualizacion: {type(e).__name__}: {e}")
        raise HTTPException(status_code=400, detail="Update error")
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Profile with name '{user_id}' not found")
    
    return {"message": "profile info updated successfully"}

