/**
 * Folder API
 */
import client from './client';

export interface MediaFolder {
  id: number;
  name: string;
  parent_id: number | null;
  created_at: string;
  file_count: number;
  children?: MediaFolder[];
}

export interface FolderListResponse {
  folders: MediaFolder[];
}

export interface FolderTreeResponse {
  tree: MediaFolder[];
}

export const folderApi = {
  /**
   * 创建文件夹
   */
  create: (name: string, parentId?: number | null): Promise<{ message: string; folder: MediaFolder }> => {
    return client.post('/folders', { name, parent_id: parentId });
  },

  /**
   * 获取文件夹列表
   */
  list: (parentId?: number | null): Promise<FolderListResponse> => {
    const params = parentId !== undefined ? { parent_id: parentId } : {};
    return client.get('/folders', { params });
  },

  /**
   * 获取文件夹树
   */
  getTree: (): Promise<FolderTreeResponse> => {
    return client.get('/folders/tree');
  },

  /**
   * 获取文件夹详情
   */
  get: (id: number): Promise<MediaFolder> => {
    return client.get(`/folders/${id}`);
  },

  /**
   * 更新文件夹
   */
  update: (id: number, data: { name?: string; parent_id?: number | null }): Promise<{ message: string; folder: MediaFolder }> => {
    return client.put(`/folders/${id}`, data);
  },

  /**
   * 删除文件夹
   */
  delete: (id: number): Promise<{ message: string }> => {
    return client.delete(`/folders/${id}`);
  },

  /**
   * 移动文件到文件夹
   */
  moveFiles: (folderId: number, fileIds: number[]): Promise<{ message: string }> => {
    return client.post(`/folders/${folderId}/move-files`, { file_ids: fileIds });
  },
};
