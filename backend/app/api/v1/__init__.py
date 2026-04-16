from fastapi import APIRouter

from app.api.v1 import attendance, auth, businesses, dashboard, employees, roles


router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(businesses.router)
router.include_router(employees.router)
router.include_router(attendance.router)
router.include_router(dashboard.router)
router.include_router(roles.router)
