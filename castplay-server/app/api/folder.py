"""Media Folder API Routes"""
import logging
from typing import List, Dict, Any

from flask import Blueprint, request, jsonify

from app import db
from app.auth import jwt_required
from app.models import MediaFolder, MediaFile
from app.api.validators import validate_json_data, max_length, is_list_of, positive_number

logger = logging.getLogger(__name__)

bp = Blueprint('folder', __name__)


@bp.route('', methods=['POST'])
@jwt_required
@validate_json_data(
    required_fields=['name'],
    field_types={'name': str, 'parent_id': int},
    field_validators={'name': max_length(128)}
)
def create_folder():
    """创建文件夹"""
    data = request.get_json()

    name = data.get('name')
    if not name:
        return jsonify({'error': 'name is required'}), 400

    parent_id = data.get('parent_id')

    # 检查父文件夹是否存在
    if parent_id:
        parent = MediaFolder.query.get(parent_id)
        if not parent:
            return jsonify({'error': 'Parent folder not found'}), 404

    # 检查同名文件夹
    existing = MediaFolder.query.filter_by(
        name=name, parent_id=parent_id).first()
    if existing:
        return jsonify({'error': 'Folder with this name already exists'}), 400

    folder = MediaFolder(name=name, parent_id=parent_id)
    db.session.add(folder)
    db.session.commit()

    return jsonify({
        'message': 'Folder created successfully',
        'folder': folder.to_dict()
    }), 201


@bp.route('', methods=['GET'])
@jwt_required
def list_folders():
    """获取文件夹列表"""
    parent_id = request.args.get('parent_id', type=int)

    if parent_id:
        folders = MediaFolder.query.filter_by(
            parent_id=parent_id).order_by(MediaFolder.name).all()
    else:
        # 获取根级文件夹
        folders = MediaFolder.query.filter_by(
            parent_id=None).order_by(MediaFolder.name).all()

    return jsonify({
        'folders': [folder.to_dict() for folder in folders]
    }), 200


@bp.route('/tree', methods=['GET'])
@jwt_required
def get_folder_tree():
    """获取完整的文件夹树"""
    root_folders = MediaFolder.query.filter_by(
        parent_id=None).order_by(MediaFolder.name).all()

    def build_tree(folder):
        result = folder.to_dict()
        result['children'] = [build_tree(child) for child in folder.children]
        return result

    tree = [build_tree(folder) for folder in root_folders]

    return jsonify({
        'tree': tree
    }), 200


@bp.route('/<int:folder_id>', methods=['GET'])
@jwt_required
def get_folder(folder_id):
    """获取文件夹详情"""
    folder = MediaFolder.query.get_or_404(folder_id)

    result = folder.to_dict()
    result['children'] = [child.to_dict() for child in folder.children]
    result['files'] = [f.to_dict() for f in folder.media_files.all()]

    return jsonify(result), 200


@bp.route('/<int:folder_id>', methods=['PUT'])
@jwt_required
@validate_json_data(
    field_types={'name': str, 'parent_id': int},
    field_validators={'name': max_length(128)}
)
def update_folder(folder_id: int):
    """更新文件夹"""
    folder = MediaFolder.query.get_or_404(folder_id)
    data = request.get_json()

    if 'name' in data:
        # 检查同名文件夹
        existing = MediaFolder.query.filter(
            MediaFolder.name == data['name'],
            MediaFolder.parent_id == folder.parent_id,
            MediaFolder.id != folder_id
        ).first()
        if existing:
            return jsonify({'error': 'Folder with this name already exists'}), 400
        folder.name = data['name']

    if 'parent_id' in data:
        # 防止循环引用
        new_parent_id = data['parent_id']
        if new_parent_id:
            # 检查是否是自己的子文件夹
            def is_descendant(parent_id, check_id):
                parent = MediaFolder.query.get(parent_id)
                if not parent:
                    return False
                if parent.id == check_id:
                    return True
                for child in parent.children:
                    if is_descendant(child.id, check_id):
                        return True
                return False

            if new_parent_id == folder_id or is_descendant(folder_id, new_parent_id):
                return jsonify({'error': 'Cannot move folder into its own subfolder'}), 400

        folder.parent_id = new_parent_id

    db.session.commit()

    return jsonify({
        'message': 'Folder updated successfully',
        'folder': folder.to_dict()
    }), 200


@bp.route('/<int:folder_id>', methods=['DELETE'])
@jwt_required
def delete_folder(folder_id):
    """删除文件夹"""
    folder = MediaFolder.query.get_or_404(folder_id)

    # 检查是否有子文件夹
    if folder.children:
        return jsonify({'error': 'Cannot delete folder with subfolders'}), 400

    # 检查是否有文件
    if folder.media_files.count() > 0:
        return jsonify({'error': 'Cannot delete folder with files'}), 400

    db.session.delete(folder)
    db.session.commit()

    return jsonify({'message': 'Folder deleted successfully'}), 200


@bp.route('/<int:folder_id>/move-files', methods=['POST'])
@jwt_required
@validate_json_data(
    required_fields=['file_ids'],
    field_types={'file_ids': list},
    field_validators={'file_ids': is_list_of(int)}
)
def move_files_to_folder(folder_id: int):
    """将文件移动到文件夹"""
    if folder_id == 0:
        # 移动到根目录
        target_folder = None
    else:
        target_folder = MediaFolder.query.get_or_404(folder_id)

    data = request.get_json()
    file_ids = data.get('file_ids', [])

    if not file_ids:
        return jsonify({'error': 'file_ids is required'}), 400

    moved_count = 0
    for file_id in file_ids:
        media_file = MediaFile.query.get(file_id)
        if media_file:
            media_file.folder_id = folder_id if folder_id != 0 else None
            moved_count += 1

    db.session.commit()

    return jsonify({
        'message': f'Moved {moved_count} files successfully'
    }), 200
