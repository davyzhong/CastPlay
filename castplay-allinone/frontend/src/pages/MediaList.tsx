/**
 * 媒体库页面
 */
import { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Space,
  Modal,
  Tag,
  Progress,
  message,
  Card,
  Typography,
  Upload,
  Image,
  Dropdown,
} from 'antd';
import {
  UploadOutlined,
  DeleteOutlined,
  ReloadOutlined,
  DownloadOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { MediaFile } from '../types';
import {
  getMediaList,
  uploadMedia,
  deleteMedia,
  getThumbnail,
  downloadMedia,
} from '../api/media';
import { useStore } from '../store';

const { Dragger } = Upload;

const { Title } = Typography;

const MediaListPage: React.FC = () => {
  const [mediaFiles, setMediaFiles] = useState<MediaFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewMedia, setPreviewMedia] = useState<MediaFile | null>(null);
  const setNotification = useStore((state) => state.setNotification);

  const fetchMedia = async () => {
    setLoading(true);
    try {
      const response = await getMediaList({ limit: 100 });
      if (response.items) {
        setMediaFiles(response.items);
      }
    } catch (error: any) {
      console.error('Fetch media error:', error);
      message.error('获取媒体列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMedia();
  }, []);

  const handleUpload = async (file: File, fileType: string) => {
    setUploading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await uploadMedia(formData as any, fileType);

      if (response.media) {
        message.success(`${fileType === 'ppt' ? 'PPT' : '文件'}上传成功`);
        // 刷新列表
        await fetchMedia();
      }
    } catch (error: any) {
      console.error('Upload error:', error);
      message.error('文件上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (media: MediaFile) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除 "${media.file_name}" 吗？`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await deleteMedia(media.id);
          message.success('媒体文件已删除');
          await fetchMedia();
        } catch (error: any) {
          console.error('Delete error:', error);
          message.error('删除失败');
        }
      },
    });
  };

  const handlePreview = (media: MediaFile) => {
    setPreviewMedia(media);
    setPreviewVisible(true);
  };

  const columns: ColumnsType<MediaFile> = [
    {
      title: '缩略图',
      dataIndex: 'thumbnail_path',
      key: 'thumbnail',
      width: 100,
      render: (path: string, record: MediaFile) => {
        if (record.file_type === 'video' && path) {
          return (
            <Image
              src={path}
              alt={record.file_name}
              preview={false}
              width={60}
              height={40}
              style={{ borderRadius: 4, objectFit: 'cover' }}
            />
          );
        } else if (record.file_type === 'ppt' && path) {
          return (
            <div
              style={{
                width: 60,
                height: 40,
                backgroundColor: '#1890ff',
                borderRadius: 4,
                display: 'flex',
                alignItems: 'center',
                color: '#fff',
                fontSize: '10px',
              }}
            >
              PPT
            </div>
          );
        }
        return (
          <Button
            icon={<EyeOutlined />}
            size="small"
            onClick={() => handlePreview(record)}
          >
            预览
          </Button>
        );
      },
    },
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      width: 200,
    },
    {
      title: '类型',
      dataIndex: 'file_type',
      key: 'file_type',
      width: 100,
      render: (type: string) => {
        const colors: {
          image: 'green',
          video: 'blue',
          ppt: 'orange',
        };
        return <Tag color={colors[type as keyof typeof colors]}>{type.toUpperCase()}</Tag>;
      },
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 120,
      render: (size: number) => {
        if (!size) return '-';
        const mb = size / 1024 / 1024;
        return `${mb.toFixed(2)} MB`;
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const statusConfig = {
          ready: { color: 'success', text: '就绪' },
          processing: { color: 'processing', text: '转换中' },
          failed: { color: 'error', text: '失败' },
        };
        const config = statusConfig[status as keyof typeof statusConfig];
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '上传时间',
      dataIndex: 'upload_time',
      key: 'upload_time',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: MediaFile) => (
        <Space>
          {record.file_type === 'video' && (
            <Button
              type="link"
              icon={<DownloadOutlined />}
              size="small"
              href={downloadMedia(record.id)}
              target="_blank"
            >
              下载
            </Button>
          )}
          <Button
            danger
            icon={<DeleteOutlined />}
            size="small"
            onClick={() => handleDelete(record)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const uploadProps = {
    name: 'file',
    accept:
      'image/*,video/*,.ppt,.pptx',
    beforeUpload: (file) => {
      const isLt50M = file.size / 1024 / 1024 < 500;
      if (!isLt50M) {
        message.error('文件大小不能超过 500MB');
        return Upload.LIST_IGNORE;
      }
      return true;
    },
  };

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Title level={4}>媒体库</Title>
      </div>

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Upload.Dragger
            {...uploadProps}
            loading={uploading}
            showUploadList={false}
            customRequest={({ file, onSuccess }) => {
              const fileExt = file.name.split('.').pop()?.toLowerCase();
              let fileType = 'image';
              if (['jpg', 'jpeg', 'png', 'gif', 'bmp'].includes(fileExt)) {
                fileType = 'image';
              } else if (['mp4', 'avi', 'mov', 'mkv', 'flv'].includes(fileExt)) {
                fileType = 'video';
              } else if (['ppt', 'pptx'].includes(fileExt)) {
                fileType = 'ppt';
              }
              handleUpload(file, fileType);
            }}
          >
            <p className="ant-upload-drag-icon">
              <UploadOutlined style={{ fontSize: 48 }} />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此处上传</p>
            <p className="ant-upload-hint">
              支持图片、视频和 PPT 文件
            </p>
          </Upload.Dragger>
          <Button
            icon={<ReloadOutlined />}
            loading={loading}
            onClick={fetchMedia}
          >
            刷新列表
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={mediaFiles}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      {/* 预览模态框 */}
      <Modal
        title={previewMedia ? previewMedia.file_name : '预览'}
        open={previewVisible}
        footer={null}
        onCancel={() => setPreviewVisible(false)}
        width={800}
      >
        {previewMedia && (
          <div style={{ textAlign: 'center' }}>
            {previewMedia.file_type === 'image' && previewMedia.thumbnail_path && (
              <Image
                src={previewMedia.thumbnail_path}
                alt={previewMedia.file_name}
                style={{ maxWidth: '100%' }}
              />
            )}
            {previewMedia.file_type === 'video' && (
              <video
                controls
                src={downloadMedia(previewMedia.id)}
                style={{ maxWidth: '100%', maxHeight: 600 }}
              />
            )}
            {previewMedia.file_type === 'ppt' && (
              <div>
                <Image
                  src={previewMedia.thumbnail_path}
                  alt={previewMedia.file_name}
                  style={{ maxWidth: '100%', marginBottom: 16 }}
                />
                <p style={{ color: '#888' }}>
                  PPT 文件预览暂不可用，请下载后查看
                </p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default MediaListPage;
