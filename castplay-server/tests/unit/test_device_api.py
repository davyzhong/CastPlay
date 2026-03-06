"""
Device API 单元测试
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from tests.conftest import _generate_unique_id


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def test_device(db):
    """创建测试设备"""
    from app.models.device import Device

    unique_id = _generate_unique_id()
    device = Device(
        device_id=f'test-device-{unique_id}',
        device_name='Test Device',
        timezone='Asia/Shanghai',
        status='offline'
    )
    db.session.add(device)
    db.session.commit()
    db.session.refresh(device)
    return device


class TestDeviceAPI:
    """Device API 测试类"""

    def test_list_devices(self, client, db, test_device):
        """测试获取设备列表"""
        response = client.get('/api/v1/devices')

        assert response.status_code == 200
        data = response.json()

        assert 'devices' in data
        assert len(data['devices']) > 0

        # 验证设备字段
        device_data = data['devices'][0]
        assert device_data['device_id'] == test_device.device_id
        assert device_data['device_name'] == test_device.device_name
        assert device_data['timezone'] == test_device.timezone

    def test_get_device(self, client, db, test_device):
        """测试获取单个设备"""
        response = client.get(f'/api/v1/devices/{test_device.id}')

        assert response.status_code == 200
        data = response.json()

        assert data['id'] == test_device.id
        assert data['device_id'] == test_device.device_id
        assert data['device_name'] == test_device.device_name

    def test_get_device_not_found(self, client, db):
        """测试获取不存在的设备"""
        response = client.get('/api/v1/devices/99999')

        assert response.status_code == 404
        data = response.json()
        assert 'detail' in data

    def test_create_device(self, client, db):
        """测试创建设备"""
        unique_id = _generate_unique_id()
        payload = {
            'device_id': f'test-create-{unique_id}',
            'device_name': 'New Test Device',
            'timezone': 'Asia/Shanghai'
        }

        response = client.post('/api/v1/devices', json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data['message'] == 'Device created successfully'
        assert 'device' in data
        assert data['device']['device_id'] == payload['device_id']
        assert data['device']['device_name'] == payload['device_name']

    def test_update_device(self, client, db, test_device):
        """测试更新设备"""
        payload = {
            'device_name': 'Updated Device Name',
            'status': 'online'
        }

        response = client.put(
            f'/api/v1/devices/{test_device.id}', json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data['message'] == 'Device updated successfully'

        # 验证数据库中的更新
        from sqlalchemy import select
        from app.models.device import Device

        result = db.execute(select(Device).where(Device.id == test_device.id))
        updated_device = result.scalar_one()

        assert updated_device.device_name == 'Updated Device Name'
        assert updated_device.status == 'online'

    def test_delete_device(self, client, db, test_device):
        """测试删除设备"""
        response = client.delete(f'/api/v1/devices/{test_device.id}')

        assert response.status_code == 200
        data = response.json()

        assert data['message'] == 'Device deleted successfully'

        # 验证软删除
        from sqlalchemy import select
        from app.models.device import Device

        result = db.execute(select(Device).where(Device.id == test_device.id))
        deleted_device = result.scalar_one()

        assert deleted_device.is_deleted is True
        assert deleted_device.deleted_at is not None

    def test_register_device(self, client, db):
        """测试设备注册"""
        unique_id = _generate_unique_id()
        payload = {
            'device_id': f'register-{unique_id}',
            'hardware_id': f'hw-{unique_id}',
            'device_name': 'Registered Device',
            'timezone': 'Asia/Shanghai'
        }

        response = client.post('/api/v1/devices/register', json=payload)

        assert response.status_code == 200
        data = response.json()

        assert 'access_token' in data
        assert 'device' in data
        assert data['device']['device_id'] == payload['device_id']


class TestDeviceSchedule:
    """设备定时任务测试"""

    def test_create_schedule(self, client, db, test_device):
        """测试创建定时任务"""
        payload = {
            'power_on_time': '08:00',
            'power_off_time': '20:00',
            'is_enabled': True
        }

        response = client.post(
            f'/api/v1/devices/{test_device.id}/schedule',
            json=payload
        )

        assert response.status_code == 200
        data = response.json()

        assert data['message'] == 'Schedule created successfully'
        assert 'schedule' in data
        assert data['schedule']['power_on_time'] == '08:00'
        assert data['schedule']['power_off_time'] == '20:00'

    def test_get_schedule(self, client, db, test_device):
        """测试获取定时任务"""
        from app.models.device import DeviceSchedule

        schedule = DeviceSchedule(
            device_id=test_device.id,
            power_on_time='09:00',
            power_off_time='18:00',
            is_enabled=True
        )
        db.session.add(schedule)
        db.session.commit()

        response = client.get(f'/api/v1/devices/{test_device.id}/schedule')

        assert response.status_code == 200
        data = response.json()

        assert 'schedules' in data
        assert len(data['schedules']) > 0
