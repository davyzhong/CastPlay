import React, { useEffect, useState, useRef } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  message,
  Modal,
  Upload,
  Select,
  Image,
  Row,
  Col,
  Progress,
  List,
  Tree,
  Card,
  Input,
  Breadcrumb,
  Checkbox,
} from 'antd';
import {
  UploadOutlined,
  DeleteOutlined,
  DownloadOutlined,
  ReloadOutlined,
  InboxOutlined,
  FileImageOutlined,
  VideoCameraOutlined,
  FileOutlined,
  CloseCircleOutlined,
  FolderOutlined,
  FolderAddOutlined,
  FolderOpenOutlined,
  EditOutlined,
  HomeOutlined,
} from '@ant-design/icons';
import { mediaApi, MediaFile } from '../api/media';
import { folderApi, MediaFolder } from '../api/folder';
import { getMediaUrl } from '../api/client';
import type { UploadFile } from 'antd';
import type { DataNode } from 'antd/es/tree';
import dayjs from 'dayjs';

const { Dragger } = Upload;

const MediaList: React.FC = () => {
  const [mediaList, setMediaList] = useState<MediaFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [fileType, setFileType] = useState<'image' | 'video' | 'ppt'>('image');
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [filterType, setFilterType] = useState<string>('all');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{[key: string]: number}>({});
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewFile, setPreviewFile] = useState<{url: string; type: string; name: string} | null>(null);

  // 文件夹相关状态
  const [folders, setFolders] = useState<MediaFolder[]>([]);
  const [currentFolderId, setCurrentFolderId] = useState<number | null>(null);
  const [folderPath, setFolderPath] = useState<{id: number | null; name: string}[]>([{ id: null, name: '根目录' }]);
  const [folderModalVisible, setFolderModalVisible] = useState(false);
  const [folderModalMode, setFolderModalMode] = useState<'create' | 'edit'>('create');
  const [editingFolder, setEditingFolder] = useState<MediaFolder | null>(null);
  const [folderName, setFolderName] = useState('');
  const [selectedFileIds, setSelectedFileIds] = useState<number[]>([]);
  const [moveModalVisible, setMoveModalVisible] = useState(false);
  const [targetFolderId, setTargetFolderId] = useState<number | null>(null);
  const [folderTree, setFolderTree] = useState<DataNode[]>([]);
  const [uploadMode, setUploadMode] = useState<'files' | 'folder'>('files');
  const folderInputRef = useRef<HTMLInputElement>(null);

  // 加载文件夹列表
  const loadFolders = async (parentId: number | null = null) => {
    try {
      const response = await folderApi.list(parentId);
      setFolders(response.folders || []);
    } catch (error) {
      console.error('加载文件夹失败', error);
    }
  };

  // 加载文件夹树
  const loadFolderTree = async () => {
    try {
      const response = await folderApi.getTree();
      const tree = response.tree || [];

      const convertToTreeData = (folders: MediaFolder[]): DataNode[] => {
        return folders.map(folder => ({
          key: folder.id,
          title: folder.name,
          icon: <FolderOutlined />,
          children: folder.children ? convertToTreeData(folder.children) : [],
        }));
      };

      setFolderTree([
        { key: 0, title: '根目录', icon: <HomeOutlined />, children: convertToTreeData(tree) }
      ]);
    } catch (error) {
      console.error('加载文件夹树失败', error);
    }
  };

  const loadMedia = async (page = 1, per_page = 10, file_type?: string, folder_id?: number | null) => {
    setLoading(true);
    try {
      const params: any = { page, per_page };
      if (file_type && file_type !== 'all') {
        params.file_type = file_type;
      }
      // 使用当前文件夹ID
      const folderId = folder_id !== undefined ? folder_id : currentFolderId;
      if (folderId !== null) {
        params.folder_id = folderId;
      }
      const response = await mediaApi.list(params);
      setMediaList(response.media || []);
      setPagination({
        current: response.page || 1,
        pageSize: response.per_page || 10,
        total: response.total || 0,
      });
    } catch (error) {
      message.error('加载媒体列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMedia(1, pagination.pageSize, filterType, currentFolderId);
    loadFolders(currentFolderId);
  }, [currentFolderId]);

  useEffect(() => {
    loadFolderTree();
  }, []);

  // 进入文件夹
  const enterFolder = (folder: MediaFolder) => {
    setCurrentFolderId(folder.id);
    setFolderPath(prev => [...prev, { id: folder.id, name: folder.name }]);
    setSelectedFileIds([]);
  };

  // 面包屑导航
  const navigateToFolder = (folderId: number | null, index: number) => {
    setCurrentFolderId(folderId);
    setFolderPath(prev => prev.slice(0, index + 1));
    setSelectedFileIds([]);
  };

  // 创建文件夹
  const handleCreateFolder = async () => {
    if (!folderName.trim()) {
      message.error('请输入文件夹名称');
      return;
    }

    try {
      await folderApi.create(folderName, currentFolderId);
      message.success('创建成功');
      setFolderModalVisible(false);
      setFolderName('');
      loadFolders(currentFolderId);
      loadFolderTree();
    } catch (error: any) {
      message.error(error.response?.data?.error || '创建失败');
    }
  };

  // 编辑文件夹
  const handleEditFolder = async () => {
    if (!folderName.trim() || !editingFolder) {
      message.error('请输入文件夹名称');
      return;
    }

    try {
      await folderApi.update(editingFolder.id, { name: folderName });
      message.success('修改成功');
      setFolderModalVisible(false);
      setFolderName('');
      setEditingFolder(null);
      loadFolders(currentFolderId);
      loadFolderTree();
    } catch (error: any) {
      message.error(error.response?.data?.error || '修改失败');
    }
  };

  // 删除文件夹
  const handleDeleteFolder = async (folder: MediaFolder) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除文件夹 "${folder.name}" 吗？`,
      onOk: async () => {
        try {
          await folderApi.delete(folder.id);
          message.success('删除成功');
          loadFolders(currentFolderId);
          loadFolderTree();
        } catch (error: any) {
          message.error(error.response?.data?.error || '删除失败');
        }
      },
    });
  };

  // 移动文件到文件夹
  const handleMoveFiles = async () => {
    if (selectedFileIds.length === 0) {
      message.error('请选择要移动的文件');
      return;
    }

    try {
      await folderApi.moveFiles(targetFolderId || 0, selectedFileIds);
      message.success('移动成功');
      setMoveModalVisible(false);
      setSelectedFileIds([]);
      setTargetFolderId(null);
      loadMedia(pagination.current, pagination.pageSize, filterType, currentFolderId);
    } catch (error) {
      message.error('移动失败');
    }
  };

  // 检测文件类型
  const detectFileType = (file: File): 'image' | 'video' | 'ppt' => {
    const name = file.name.toLowerCase();
    if (/\.(jpg|jpeg|png|gif|bmp|webp)$/.test(name)) return 'image';
    if (/\.(mp4|avi|mov|mkv|flv|wmv)$/.test(name)) return 'video';
    if (/\.(ppt|pptx)$/.test(name)) return 'ppt';
    return 'image'; // 默认
  };

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.error('请选择文件');
      return;
    }

    setUploading(true);
    const results: {success: number; failed: number} = { success: 0, failed: 0 };

    for (const file of fileList) {
      const fileObj = file.originFileObj as File;
      const uid = file.uid;

      // 自动检测文件类型（文件夹上传模式）
      const detectedType = uploadMode === 'folder' ? detectFileType(fileObj) : fileType;

      try {
        setUploadProgress(prev => ({ ...prev, [uid]: 0 }));

        const progressInterval = setInterval(() => {
          setUploadProgress(prev => {
            const current = prev[uid] || 0;
            if (current < 90) {
              return { ...prev, [uid]: current + 10 };
            }
            return prev;
          });
        }, 200);

        await mediaApi.upload(fileObj, detectedType, currentFolderId);

        clearInterval(progressInterval);
        setUploadProgress(prev => ({ ...prev, [uid]: 100 }));
        results.success++;
      } catch (error: any) {
        setUploadProgress(prev => ({ ...prev, [uid]: -1 }));
        results.failed++;
      }
    }

    setUploading(false);

    if (results.success > 0) {
      message.success(`成功上传 ${results.success} 个文件${results.failed > 0 ? `，${results.failed} 个失败` : ''}`);
    } else {
      message.error('上传失败');
    }

    if (results.success > 0) {
      setTimeout(() => {
        setUploadModalVisible(false);
        setFileList([]);
        setUploadProgress({});
        loadMedia(pagination.current, pagination.pageSize, filterType, currentFolderId);
      }, 1000);
    }
  };

  // 文件夹上传处理
  const handleFolderSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const validExtensions = /\.(jpg|jpeg|png|gif|bmp|webp|mp4|avi|mov|mkv|flv|ppt|pptx)$/i;
    const validFiles: UploadFile[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (validExtensions.test(file.name)) {
        validFiles.push({
          uid: `folder-${Date.now()}-${i}`,
          name: file.name,
          status: 'done',
          originFileObj: file as any,
          size: file.size,
          type: file.type,
        });
      }
    }

    if (validFiles.length > 0) {
      setFileList(validFiles);
      message.success(`已选择 ${validFiles.length} 个有效文件`);
    } else {
      message.warning('文件夹中没有支持的媒体文件');
    }

    // 重置input
    e.target.value = '';
  };

  const handleDelete = async (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个媒体文件吗？',
      onOk: async () => {
        try {
          await mediaApi.delete(id);
          message.success('删除成功');
          loadMedia(pagination.current, pagination.pageSize, filterType, currentFolderId);
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  const handleTableChange = (pag: any) => {
    loadMedia(pag.current, pag.pageSize, filterType, currentFolderId);
  };

  const handleFilterChange = (value: string) => {
    setFilterType(value);
    loadMedia(1, pagination.pageSize, value, currentFolderId);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'green';
      case 'processing': return 'blue';
      case 'failed': return 'red';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'ready': return '就绪';
      case 'processing': return '处理中';
      case 'failed': return '失败';
      default: return status;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getFileIcon = (file: UploadFile) => {
    const type = file.type || '';
    if (type.startsWith('image/')) return <FileImageOutlined style={{ fontSize: 32, color: '#1890ff' }} />;
    if (type.startsWith('video/')) return <VideoCameraOutlined style={{ fontSize: 32, color: '#52c41a' }} />;
    return <FileOutlined style={{ fontSize: 32, color: '#faad14' }} />;
  };

  const handlePreview = (file: UploadFile) => {
    const fileObj = file.originFileObj as File;
    const url = URL.createObjectURL(fileObj);
    const type = fileObj.type.startsWith('image/') ? 'image' :
                 fileObj.type.startsWith('video/') ? 'video' : 'other';
    setPreviewFile({ url, type, name: fileObj.name });
    setPreviewVisible(true);
  };

  const handleRemoveFile = (uid: string) => {
    setFileList(prev => prev.filter(f => f.uid !== uid));
    setUploadProgress(prev => {
      const newProgress = { ...prev };
      delete newProgress[uid];
      return newProgress;
    });
  };

  const columns = [
    {
      title: (
        <Checkbox
          checked={selectedFileIds.length === mediaList.length && mediaList.length > 0}
          indeterminate={selectedFileIds.length > 0 && selectedFileIds.length < mediaList.length}
          onChange={(e) => {
            if (e.target.checked) {
              setSelectedFileIds(mediaList.map(m => m.id));
            } else {
              setSelectedFileIds([]);
            }
          }}
        />
      ),
      key: 'select',
      width: 50,
      render: (_: any, record: MediaFile) => (
        <Checkbox
          checked={selectedFileIds.includes(record.id)}
          onChange={(e) => {
            if (e.target.checked) {
              setSelectedFileIds(prev => [...prev, record.id]);
            } else {
              setSelectedFileIds(prev => prev.filter(id => id !== record.id));
            }
          }}
        />
      ),
    },
    {
      title: '缩略图',
      dataIndex: 'thumbnail_path',
      key: 'thumbnail',
      width: 150,
      render: (_thumbnail: string | null, record: MediaFile) => (
        <Image
          src={getMediaUrl(record.id, 'thumbnail')}
          alt={record.file_name}
          width={120}
          height={120}
          style={{ objectFit: 'cover' }}
          fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAI0lEQVR4nO3BMQEAAADCoPVPbQwfoAAAAAAAAAAAAAAAAIC3AR8AADjSAWsAAAAASUVORK5CYII="
        />
      ),
    },
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      ellipsis: true,
    },
    {
      title: '类型',
      dataIndex: 'file_type',
      key: 'file_type',
      width: 80,
      render: (type: string) => (
        <Tag color={type === 'image' ? 'blue' : type === 'video' ? 'green' : 'orange'}>
          {type === 'image' ? '图片' : type === 'video' ? '视频' : 'PPT'}
        </Tag>
      ),
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      ),
    },
    {
      title: '上传时间',
      dataIndex: 'upload_time',
      key: 'upload_time',
      width: 160,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: MediaFile) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<DownloadOutlined />}
            href={getMediaUrl(record.id, 'download')}
            target="_blank"
          />
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          />
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* 面包屑导航 */}
      <Breadcrumb style={{ marginBottom: 16 }}>
        {folderPath.map((item, index) => (
          <Breadcrumb.Item key={item.id ?? 'root'}>
            {index === folderPath.length - 1 ? (
              <span>{item.name}</span>
            ) : (
              <a onClick={() => navigateToFolder(item.id, index)}>{item.name}</a>
            )}
          </Breadcrumb.Item>
        ))}
      </Breadcrumb>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col>
          <Space>
            <Button type="primary" icon={<UploadOutlined />} onClick={() => setUploadModalVisible(true)}>
              上传文件
            </Button>
            <Button icon={<FolderAddOutlined />} onClick={() => {
              setFolderModalMode('create');
              setFolderName('');
              setFolderModalVisible(true);
            }}>
              新建文件夹
            </Button>
            {selectedFileIds.length > 0 && (
              <Button onClick={() => {
                loadFolderTree();
                setMoveModalVisible(true);
              }}>
                移动到 ({selectedFileIds.length})
              </Button>
            )}
            <Button icon={<ReloadOutlined />} onClick={() => {
              loadMedia(pagination.current, pagination.pageSize, filterType, currentFolderId);
              loadFolders(currentFolderId);
            }}>
              刷新
            </Button>
          </Space>
        </Col>
        <Col flex="auto">
          <div style={{ textAlign: 'right' }}>
            <Select
              style={{ width: 120 }}
              value={filterType}
              onChange={handleFilterChange}
              options={[
                { label: '全部', value: 'all' },
                { label: '图片', value: 'image' },
                { label: '视频', value: 'video' },
                { label: 'PPT', value: 'ppt' },
              ]}
            />
          </div>
        </Col>
      </Row>

      {/* 文件夹列表 */}
      {folders.length > 0 && (
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          {folders.map(folder => (
            <Col key={folder.id}>
              <Card
                size="small"
                hoverable
                style={{ width: 150 }}
                onClick={() => enterFolder(folder)}
                actions={[
                  <EditOutlined key="edit" onClick={(e) => {
                    e.stopPropagation();
                    setFolderModalMode('edit');
                    setEditingFolder(folder);
                    setFolderName(folder.name);
                    setFolderModalVisible(true);
                  }} />,
                  <DeleteOutlined key="delete" onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteFolder(folder);
                  }} />,
                ]}
              >
                <div style={{ textAlign: 'center' }}>
                  <FolderOpenOutlined style={{ fontSize: 36, color: '#faad14' }} />
                  <div style={{ marginTop: 8, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {folder.name}
                  </div>
                  <div style={{ fontSize: 12, color: '#999' }}>{folder.file_count} 个文件</div>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      )}

      <Table
        columns={columns}
        dataSource={mediaList}
        loading={loading}
        rowKey="id"
        pagination={pagination}
        onChange={handleTableChange}
        size="small"
      />

      {/* 上传弹窗 */}
      <Modal
        title="上传媒体文件"
        open={uploadModalVisible}
        onOk={handleUpload}
        onCancel={() => {
          if (!uploading) {
            setUploadModalVisible(false);
            setFileList([]);
            setUploadProgress({});
            setUploadMode('files');
          }
        }}
        okText={uploading ? '上传中...' : '开始上传'}
        cancelText="取消"
        okButtonProps={{ disabled: uploading || fileList.length === 0 }}
        cancelButtonProps={{ disabled: uploading }}
        width={650}
        maskClosable={false}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          {/* 上传模式选择 */}
          <div>
            <label>上传模式：</label>
            <Select
              style={{ width: '100%', marginTop: 8 }}
              value={uploadMode}
              onChange={(v) => {
                setUploadMode(v);
                setFileList([]);
                setUploadProgress({});
              }}
              disabled={uploading}
              options={[
                { label: '选择文件', value: 'files' },
                { label: '上传文件夹', value: 'folder' },
              ]}
            />
          </div>

          {uploadMode === 'files' && (
            <div>
              <label>文件类型：</label>
              <Select
                style={{ width: '100%', marginTop: 8 }}
                value={fileType}
                onChange={setFileType}
                disabled={uploading}
                options={[
                  { label: '图片 (JPG, PNG, GIF, BMP)', value: 'image' },
                  { label: '视频 (MP4, AVI, MOV, MKV)', value: 'video' },
                  { label: 'PPT (PPTX, PPT)', value: 'ppt' },
                ]}
              />
            </div>
          )}

          {uploadMode === 'files' ? (
            <Dragger
              multiple
              fileList={fileList}
              onChange={({ fileList }) => setFileList(fileList)}
              beforeUpload={() => false}
              disabled={uploading}
              accept={fileType === 'image' ? '.jpg,.jpeg,.png,.gif,.bmp' :
                      fileType === 'video' ? '.mp4,.avi,.mov,.mkv,.flv' : '.ppt,.pptx'}
              showUploadList={false}
            >
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p className="ant-upload-text">点击或拖拽文件到此区域</p>
              <p className="ant-upload-hint">支持多文件同时上传</p>
            </Dragger>
          ) : (
            <div style={{ border: '1px dashed #d9d9d9', borderRadius: 8, padding: 24, textAlign: 'center' }}>
              <input
                ref={folderInputRef}
                type="file"
                // @ts-ignore - webkitdirectory is a non-standard attribute
                webkitdirectory=""
                // @ts-ignore
                directory=""
                multiple
                style={{ display: 'none' }}
                onChange={handleFolderSelect}
              />
              <FolderOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              <div style={{ marginTop: 16 }}>
                <Button type="primary" onClick={() => folderInputRef.current?.click()}>
                  选择文件夹
                </Button>
              </div>
              <p style={{ marginTop: 8, color: '#999' }}>
                将自动过滤并上传文件夹中的图片、视频和PPT文件
              </p>
            </div>
          )}

          {fileList.length > 0 && (
            <div style={{ maxHeight: 250, overflowY: 'auto' }}>
              <List
                size="small"
                dataSource={fileList}
                renderItem={(file) => {
                  const progress = uploadProgress[file.uid];
                  const fileObj = file.originFileObj as File;
                  return (
                    <List.Item
                      style={{ padding: '6px 0' }}
                      actions={[
                        !uploading && (
                          <Button type="text" size="small" icon={<CloseCircleOutlined />}
                            onClick={() => handleRemoveFile(file.uid)} />
                        ),
                        (fileObj?.type?.startsWith('image/') || fileObj?.type?.startsWith('video/')) && (
                          <Button type="link" size="small" onClick={() => handlePreview(file)}>预览</Button>
                        ),
                      ].filter(Boolean)}
                    >
                      <List.Item.Meta
                        avatar={getFileIcon(file)}
                        title={<span style={{ fontSize: 12 }}>{file.name}</span>}
                        description={
                          <div>
                            <span style={{ fontSize: 11, color: '#888' }}>{formatFileSize(fileObj?.size || 0)}</span>
                            {progress !== undefined && progress >= 0 && (
                              <Progress percent={progress} size="small" status={progress === 100 ? 'success' : 'active'} style={{ marginTop: 4 }} />
                            )}
                            {progress === -1 && <Tag color="red" style={{ marginTop: 4 }}>上传失败</Tag>}
                          </div>
                        }
                      />
                    </List.Item>
                  );
                }}
              />
              <div style={{ textAlign: 'right', marginTop: 8, color: '#888', fontSize: 12 }}>
                共 {fileList.length} 个文件
              </div>
            </div>
          )}

          {currentFolderId && (
            <div style={{ color: '#1890ff', fontSize: 12 }}>
              文件将上传到当前文件夹：{folderPath[folderPath.length - 1]?.name}
            </div>
          )}
        </Space>
      </Modal>

      {/* 文件夹创建/编辑弹窗 */}
      <Modal
        title={folderModalMode === 'create' ? '新建文件夹' : '编辑文件夹'}
        open={folderModalVisible}
        onOk={folderModalMode === 'create' ? handleCreateFolder : handleEditFolder}
        onCancel={() => {
          setFolderModalVisible(false);
          setFolderName('');
          setEditingFolder(null);
        }}
        okText="确定"
        cancelText="取消"
      >
        <Input
          placeholder="请输入文件夹名称"
          value={folderName}
          onChange={(e) => setFolderName(e.target.value)}
          onPressEnter={folderModalMode === 'create' ? handleCreateFolder : handleEditFolder}
        />
      </Modal>

      {/* 移动文件弹窗 */}
      <Modal
        title="移动文件到"
        open={moveModalVisible}
        onOk={handleMoveFiles}
        onCancel={() => {
          setMoveModalVisible(false);
          setTargetFolderId(null);
        }}
        okText="移动"
        cancelText="取消"
      >
        <Tree
          showIcon
          defaultExpandAll
          treeData={folderTree}
          selectedKeys={targetFolderId !== null ? [targetFolderId] : [0]}
          onSelect={(keys) => {
            const key = keys[0] as number;
            setTargetFolderId(key === 0 ? null : key);
          }}
        />
      </Modal>

      {/* 预览弹窗 */}
      <Modal
        title={previewFile?.name}
        open={previewVisible}
        footer={null}
        onCancel={() => {
          setPreviewVisible(false);
          if (previewFile?.url) URL.revokeObjectURL(previewFile.url);
          setPreviewFile(null);
        }}
        width={800}
      >
        {previewFile?.type === 'image' && <img src={previewFile.url} alt="preview" style={{ width: '100%' }} />}
        {previewFile?.type === 'video' && <video src={previewFile.url} controls style={{ width: '100%' }} />}
      </Modal>
    </div>
  );
};

export default MediaList;
