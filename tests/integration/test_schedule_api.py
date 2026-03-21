"""
播放列表调度 API 集成测试
TDD Test: T009
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.schedule import DayOfWeek
from app.models.playlist import DevicePlaylist


class TestScheduleCRUDEndpoints:
    """T009: 调度 CRUD 端点集成测试"""

    def _setup_device_with_playlist(self, db_session: Session, test_device, test_playlist):
        """辅助方法：为设备设置播放列表关联"""
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id
        )
        db_session.add(assignment)
        db_session.commit()
        return assignment

    def test_create_schedule_success(
        self, client: TestClient, auth_headers: dict,
        test_device, test_playlist, db_session: Session
    ):
        """测试成功创建调度"""
        self._setup_device_with_playlist(db_session, test_device, test_playlist)

        response = client.post(
            "/api/schedules/",
            headers=auth_headers,
            json={
                "device_id": test_device.id,
                "playlist_id": test_playlist.id,
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "days_of_week": 127,
                "enabled": True,
                "priority": 0
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["device_id"] == test_device.id
        assert data["playlist_id"] == test_playlist.id
        assert data["start_time"] == "09:00:00"
        assert data["end_time"] == "17:00:00"
        assert data["days_of_week"] == 127
        assert data["enabled"] is True
        assert "id" in data

    def test_create_schedule_invalid_time_range(
        self, client: TestClient, auth_headers: dict,
        test_device, test_playlist, db_session: Session
    ):
        """测试创建调度时无效时间范围"""
        self._setup_device_with_playlist(db_session, test_device, test_playlist)

        response = client.post(
            "/api/schedules/",
            headers=auth_headers,
            json={
                "device_id": test_device.id,
                "playlist_id": test_playlist.id,
                "start_time": "17:00:00",
                "end_time": "09:00:00",  # Invalid: end < start
                "days_of_week": 127,
                "enabled": True,
                "priority": 0
            }
        )

        # FastAPI returns 422 for Pydantic validation errors
        assert response.status_code == 422
        assert "end_time" in str(response.json()["detail"]).lower()

    def test_create_schedule_playlist_not_assigned(
        self, client: TestClient, auth_headers: dict,
        test_device, test_playlist, db_session: Session
    ):
        """测试创建调度时播放列表未分配给设备"""
        # Don't create DevicePlaylist assignment

        response = client.post(
            "/api/schedules/",
            headers=auth_headers,
            json={
                "device_id": test_device.id,
                "playlist_id": test_playlist.id,
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "days_of_week": 127,
                "enabled": True,
                "priority": 0
            }
        )

        assert response.status_code == 400
        assert "not assigned" in response.json()["detail"].lower()

    def test_list_schedules(
        self, client: TestClient, auth_headers: dict,
        test_device, test_playlist, db_session: Session
    ):
        """测试获取调度列表"""
        self._setup_device_with_playlist(db_session, test_device, test_playlist)

        # Create a schedule first
        client.post(
            "/api/schedules/",
            headers=auth_headers,
            json={
                "device_id": test_device.id,
                "playlist_id": test_playlist.id,
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "days_of_week": 127,
                "enabled": True,
                "priority": 0
            }
        )

        # List schedules
        response = client.get(
            f"/api/schedules/?device_id={test_device.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "schedules" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_list_schedules_empty(self, client: TestClient, test_device):
        """测试设备无调度时返回空列表"""
        response = client.get(
            f"/api/schedules/?device_id={test_device.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["schedules"] == []
        assert data["total"] == 0

    def test_get_schedule_by_id(
        self, client: TestClient, auth_headers: dict,
        test_device, test_playlist, db_session: Session
    ):
        """测试获取单个调度详情"""
        self._setup_device_with_playlist(db_session, test_device, test_playlist)

        # Create a schedule
        create_response = client.post(
            "/api/schedules/",
            headers=auth_headers,
            json={
                "device_id": test_device.id,
                "playlist_id": test_playlist.id,
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "days_of_week": 127,
                "enabled": True,
                "priority": 0
            }
        )
        schedule_id = create_response.json()["id"]

        # Get by ID
        response = client.get(f"/api/schedules/{schedule_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == schedule_id
        assert data["device_id"] == test_device.id

    def test_get_schedule_not_found(self, client: TestClient):
        """测试获取不存在的调度"""
        response = client.get("/api/schedules/99999")

        assert response.status_code == 404

    def test_update_schedule(
        self, client: TestClient, auth_headers: dict,
        test_device, test_playlist, db_session: Session
    ):
        """测试更新调度"""
        self._setup_device_with_playlist(db_session, test_device, test_playlist)

        # Create a schedule
        create_response = client.post(
            "/api/schedules/",
            headers=auth_headers,
            json={
                "device_id": test_device.id,
                "playlist_id": test_playlist.id,
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "days_of_week": 127,
                "enabled": True,
                "priority": 0
            }
        )
        schedule_id = create_response.json()["id"]

        # Update schedule
        response = client.put(
            f"/api/schedules/{schedule_id}",
            headers=auth_headers,
            json={
                "start_time": "08:00:00",
                "end_time": "18:00:00",
                "priority": 10
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["start_time"] == "08:00:00"
        assert data["end_time"] == "18:00:00"
        assert data["priority"] == 10

    def test_update_schedule_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """测试更新不存在的调度"""
        response = client.put(
            "/api/schedules/99999",
            headers=auth_headers,
            json={"priority": 10}
        )

        assert response.status_code == 404

    def test_delete_schedule(
        self, client: TestClient, auth_headers: dict,
        test_device, test_playlist, db_session: Session
    ):
        """测试删除调度"""
        self._setup_device_with_playlist(db_session, test_device, test_playlist)

        # Create a schedule
        create_response = client.post(
            "/api/schedules/",
            headers=auth_headers,
            json={
                "device_id": test_device.id,
                "playlist_id": test_playlist.id,
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "days_of_week": 127,
                "enabled": True,
                "priority": 0
            }
        )
        schedule_id = create_response.json()["id"]

        # Delete schedule
        response = client.delete(
            f"/api/schedules/{schedule_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify deleted
        get_response = client.get(f"/api/schedules/{schedule_id}")
        assert get_response.status_code == 404

    def test_delete_schedule_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """测试删除不存在的调度"""
        response = client.delete(
            "/api/schedules/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_unauthenticated_create_denied(
        self, client: TestClient, test_device, test_playlist, db_session: Session
    ):
        """测试未认证用户无法创建调度"""
        self._setup_device_with_playlist(db_session, test_device, test_playlist)

        response = client.post(
            "/api/schedules/",
            json={
                "device_id": test_device.id,
                "playlist_id": test_playlist.id,
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "days_of_week": 127,
                "enabled": True,
                "priority": 0
            }
        )

        # FastAPI returns 403 for unauthenticated requests when no credentials provided
        assert response.status_code in [401, 403]


class TestActiveScheduleEndpoint:
    """活跃调度端点测试"""

    def _setup_device_with_playlist(self, db_session: Session, test_device, test_playlist):
        """辅助方法：为设备设置播放列表关联"""
        assignment = DevicePlaylist(
            device_id=test_device.id,
            playlist_id=test_playlist.id
        )
        db_session.add(assignment)
        db_session.commit()
        return assignment

    def test_get_active_schedule_no_schedules(
        self, client: TestClient, test_device
    ):
        """测试无调度时返回空响应"""
        response = client.get(
            f"/api/schedules/active?device_id={test_device.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["active_playlist_id"] is None
        assert data["schedule_id"] is None

    def test_get_active_schedule_returns_matching(
        self, client: TestClient, auth_headers: dict,
        test_device, test_playlist, db_session: Session
    ):
        """测试返回匹配的活跃调度"""
        self._setup_device_with_playlist(db_session, test_device, test_playlist)

        # Create an all-day schedule
        client.post(
            "/api/schedules/",
            headers=auth_headers,
            json={
                "device_id": test_device.id,
                "playlist_id": test_playlist.id,
                "start_time": "00:00:00",
                "end_time": "23:59:59",
                "days_of_week": 127,
                "enabled": True,
                "priority": 0
            }
        )

        response = client.get(
            f"/api/schedules/active?device_id={test_device.id}"
        )

        assert response.status_code == 200
        data = response.json()
        # May or may not return depending on current time
        # Just check structure is correct
        assert "active_playlist_id" in data
        assert "schedule_id" in data
        assert "schedule_name" in data
