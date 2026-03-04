"""
Device API Tests (Flask 版本)

测试设备相关的 API 端点
"""
import pytest
import json


class TestDeviceRegistration:
    """测试设备注册 API"""

    def test_register_device_new(self, client):
        """测试新设备注册"""
        response = client.post(
            '/api/devices/register',
            data=json.dumps({
                'hardware_id': 'test_hardware_123',
                'device_name': 'Test Device',
                'timezone': 'Asia/Shanghai'
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['is_new'] is True
        assert 'device' in data
        assert data['device']['device_name'] == 'Test Device'
        assert data['device']['device_id'].startswith('CAS-')

    def test_register_device_existing(self, client):
        """测试已有设备重新注册"""
        # 先注册一次
        response1 = client.post(
            '/api/devices/register',
            data=json.dumps({'hardware_id': 'test_hardware_456'}),
            content_type='application/json'
        )
        device_id = response1.get_json()['device']['device_id']

        # 再次注册
        response2 = client.post(
            '/api/devices/register',
            data=json.dumps({
                'device_id': device_id,
                'device_name': 'Updated Name'
            }),
            content_type='application/json'
        )

        assert response2.status_code == 200
        data = response2.get_json()
        assert data['is_new'] is False
        assert data['device']['device_name'] == 'Updated Name'


class TestDeviceList:
    """测试设备列表 API"""

    def test_list_devices(self, client):
        """测试设备列表"""
        # 先创建一些设备
        for i in range(3):
            client.post(
                '/api/devices/register',
                data=json.dumps({'hardware_id': f'list_test_{i}'}),
                content_type='application/json'
            )

        response = client.get('/api/devices')

        assert response.status_code == 200
        data = response.get_json()
        assert 'devices' in data
        assert 'total' in data
        assert data['total'] >= 3

    def test_list_devices_empty(self, client):
        """测试空设备列表"""
        response = client.get('/api/devices')

        assert response.status_code == 200
        data = response.get_json()
        assert 'devices' in data
        assert data['total'] == 0


class TestDeviceDetail:
    """测试设备详情 API"""

    def test_get_device_not_found(self, client):
        """测试获取不存在的设备"""
        response = client.get('/api/devices/99999')

        assert response.status_code == 404

    def test_get_device_success(self, client, sample_device):
        """测试获取设备详情"""
        response = client.get(f'/api/devices/{sample_device.id}')

        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == sample_device.id
        assert data['device_id'] == sample_device.device_id


class TestDeviceHeartbeat:
    """测试设备心跳 API"""

    def test_heartbeat(self, client):
        """测试心跳"""
        # 先注册设备
        reg_response = client.post(
            '/api/devices/register',
            data=json.dumps({'hardware_id': 'heartbeat_test'}),
            content_type='application/json'
        )
        device_id = reg_response.get_json()['device']['id']

        # 发送心跳
        response = client.put(f'/api/devices/{device_id}/heartbeat')

        assert response.status_code == 200
        data = response.get_json()
        assert data['device']['status'] == 'online'

    def test_heartbeat_device_not_found(self, client):
        """测试不存在设备的心跳"""
        response = client.put('/api/devices/99999/heartbeat')

        assert response.status_code == 404
