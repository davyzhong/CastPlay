"""
Integration Tests for Device API
"""
import pytest
import json
from app.models import Device, DeviceSchedule


class TestDeviceRegistration:
    """测试设备注册 API"""

    def test_register_new_device(self, client, app):
        """测试注册新设备 - API 会自动生成 device_id (CAS-XXXX 格式)"""
        data = {
            'device_name': 'New Device',
            'timezone': 'Asia/Shanghai'
        }

        response = client.post('/api/devices/register',
                               data=json.dumps(data),
                               content_type='application/json')

        assert response.status_code == 200
        json_data = response.get_json()
        assert 'device' in json_data
        # API 自动生成 CAS-XXXX 格式的 device_id
        assert json_data['device']['device_id'].startswith('CAS-')
        assert json_data['device']['device_name'] == 'New Device'
        assert json_data['device']['status'] == 'online'
        assert json_data['is_new'] is True

    def test_register_existing_device(self, client, app, sample_device):
        """测试重新注册已存在的设备"""
        data = {
            'device_id': sample_device.device_id,  # 使用已存在的 device_id
            'device_name': 'Updated Device',
            'timezone': 'Asia/Tokyo'
        }

        response = client.post('/api/devices/register',
                               data=json.dumps(data),
                               content_type='application/json')

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['device']['device_name'] == 'Updated Device'
        assert json_data['device']['timezone'] == 'Asia/Tokyo'
        assert json_data['is_new'] is False

    def test_register_device_without_device_id(self, client):
        """测试不传 device_id 时自动生成"""
        data = {
            'device_name': 'Auto ID Device'
        }

        response = client.post('/api/devices/register',
                               data=json.dumps(data),
                               content_type='application/json')

        # 不传 device_id 时应该成功并自动生成
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['device']['device_id'].startswith('CAS-')
        assert json_data['is_new'] is True


class TestDeviceList:
    """测试设备列表 API"""

    def test_list_devices_empty(self, client):
        """测试空设备列表"""
        response = client.get('/api/devices')

        assert response.status_code == 200
        json_data = response.get_json()
        assert 'devices' in json_data
        assert len(json_data['devices']) == 0
        assert json_data['total'] == 0

    def test_list_devices_with_data(self, client, app, sample_device):
        """测试有数据的设备列表"""
        response = client.get('/api/devices')

        assert response.status_code == 200
        json_data = response.get_json()
        assert len(json_data['devices']) == 1
        assert json_data['total'] == 1
        assert json_data['devices'][0]['device_id'] == sample_device.device_id

    def test_list_devices_pagination(self, client, app):
        """测试分页功能"""
        # 创建多个设备
        with app.app_context():
            from app import db
            for i in range(5):
                device = Device(
                    device_id=f'device-{i}',
                    device_name=f'Device {i}'
                )
                db.session.add(device)
            db.session.commit()

        response = client.get('/api/devices?page=1&per_page=2')

        assert response.status_code == 200
        json_data = response.get_json()
        assert len(json_data['devices']) == 2
        assert json_data['total'] == 5
        assert json_data['pages'] == 3

    def test_list_devices_filter_by_status(self, client, app):
        """测试按状态过滤"""
        with app.app_context():
            from app import db
            device1 = Device(device_id='online-1', status='online')
            device2 = Device(device_id='offline-1', status='offline')
            db.session.add_all([device1, device2])
            db.session.commit()

        response = client.get('/api/devices?status=online')

        assert response.status_code == 200
        json_data = response.get_json()
        assert len(json_data['devices']) == 1
        assert json_data['devices'][0]['status'] == 'online'


class TestDeviceDetail:
    """测试设备详情 API"""

    def test_get_device_detail(self, client, app, sample_device):
        """测试获取设备详情"""
        response = client.get(f'/api/devices/{sample_device.id}')

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['id'] == sample_device.id
        assert json_data['device_id'] == sample_device.device_id

    def test_get_device_not_found(self, client):
        """测试获取不存在的设备"""
        response = client.get('/api/devices/9999')

        assert response.status_code == 404


class TestDeviceUpdate:
    """测试设备更新 API"""

    def test_update_device(self, client, app, sample_device):
        """测试更新设备"""
        data = {
            'device_name': 'Updated Name',
            'timezone': 'Asia/Tokyo'
        }

        response = client.put(f'/api/devices/{sample_device.id}',
                              data=json.dumps(data),
                              content_type='application/json')

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['device']['device_name'] == 'Updated Name'
        assert json_data['device']['timezone'] == 'Asia/Tokyo'

    def test_update_device_not_found(self, client):
        """测试更新不存在的设备"""
        data = {'device_name': 'Test'}

        response = client.put('/api/devices/9999',
                              data=json.dumps(data),
                              content_type='application/json')

        assert response.status_code == 404


class TestDeviceDelete:
    """测试设备删除 API"""

    def test_delete_device(self, client, app, sample_device):
        """测试删除设备"""
        response = client.delete(f'/api/devices/{sample_device.id}')

        assert response.status_code == 200
        json_data = response.get_json()
        assert 'message' in json_data

        # 验证设备已删除
        with app.app_context():
            device = Device.query.get(sample_device.id)
            assert device is None

    def test_delete_device_not_found(self, client):
        """测试删除不存在的设备"""
        response = client.delete('/api/devices/9999')

        assert response.status_code == 404


class TestDeviceSchedule:
    """测试设备定时配置 API"""

    def test_set_schedule(self, client, app, sample_device):
        """测试设置定时配置"""
        data = {
            'power_on_time': '08:00',
            'power_off_time': '18:00',
            'is_enabled': True,
            'weekdays': [1, 2, 3, 4, 5]
        }

        response = client.post(f'/api/devices/{sample_device.id}/schedule',
                               data=json.dumps(data),
                               content_type='application/json')

        assert response.status_code == 200
        json_data = response.get_json()
        assert 'schedule' in json_data
        assert json_data['schedule']['power_on_time'] == '08:00'
        assert json_data['schedule']['is_enabled'] is True

    def test_update_schedule(self, client, app, sample_device):
        """测试更新已有的定时配置"""
        # 先创建配置
        with app.app_context():
            from app import db
            from datetime import time
            schedule = DeviceSchedule(
                device_id=sample_device.id,
                power_on_time=time(8, 0),
                power_off_time=time(18, 0)
            )
            db.session.add(schedule)
            db.session.commit()

        # 更新配置
        data = {
            'power_on_time': '09:00',
            'power_off_time': '17:00',
            'weekdays': [1, 2, 3]
        }

        response = client.post(f'/api/devices/{sample_device.id}/schedule',
                               data=json.dumps(data),
                               content_type='application/json')

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['schedule']['power_on_time'] == '09:00'

    def test_get_schedule(self, client, app, sample_device):
        """测试获取定时配置"""
        # 先创建配置
        with app.app_context():
            from app import db
            from datetime import time
            schedule = DeviceSchedule(
                device_id=sample_device.id,
                power_on_time=time(9, 30),
                power_off_time=time(17, 30)
            )
            db.session.add(schedule)
            db.session.commit()

        response = client.get(f'/api/devices/{sample_device.id}/schedule')

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['power_on_time'] == '09:30'
        assert json_data['power_off_time'] == '17:30'

    def test_get_schedule_not_configured(self, client, app, sample_device):
        """测试获取未配置的定时"""
        response = client.get(f'/api/devices/{sample_device.id}/schedule')

        assert response.status_code == 404
        json_data = response.get_json()
        assert 'message' in json_data


class TestDeviceHeartbeat:
    """测试设备心跳 API"""

    def test_heartbeat(self, client, app, sample_device):
        """测试心跳上报"""
        response = client.put(f'/api/devices/{sample_device.id}/heartbeat')

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['device']['status'] == 'online'

        # 验证 last_online 已更新
        with app.app_context():
            device = Device.query.get(sample_device.id)
            assert device.last_online is not None

    def test_heartbeat_device_not_found(self, client):
        """测试不存在设备的心跳"""
        response = client.put('/api/devices/9999/heartbeat')

        assert response.status_code == 404
