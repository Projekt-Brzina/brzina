from fastapi import APIRouter

router = APIRouter()

@router.get("/bookings", tags=["bookings"])
def get_bookings():
    return {"message": "Bookings endpoint"}
