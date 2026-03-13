/**
 * 媒体库页面
 */
import { useState, useEffect, useRef } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  Card,
  Typography,
  Upload,
  Image,
  App,
  Modal,
  InputNumber,
} from 'antd';
import {
  UploadOutlined,
  DeleteOutlined,
  ReloadOutlined,
  DownloadOutlined,
  RedoOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { UploadRequestOption } from 'rc-upload/lib/interface';
import type { MediaFile } from '../types';
import {
  getMediaList,
  uploadMedia,
  deleteMedia,
  downloadMedia,
  retryConversion,
  getThumbnail,
} from '../api/media';

const { Title } = Typography;

const MediaListPage: React.FC = () => {
  const { message, modal } = App.useApp();
  const [mediaFiles, setMediaFiles] = useState<MediaFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  // PPT 幻灯片间隔时长设置
  const [pptSlideDuration, setPptSlideDuration] = useState(5);
  const [pptUploadModalVisible, setPptUploadModalVisible] = useState(false);
  const [pendingPptFile, setPendingPptFile] = useState<File | null>(null);
  const uploadRef = useRef<any>(null);

  const fetchMedia = async () => {
    setLoading(true);
    try {
      const response = await getMediaList({ limit: 100 });
      if (response.items) {
        setMediaFiles(response.items);
      }
    } catch (error: unknown) {
      console.error('Fetch media error:', error);
      message.error('获取媒体列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMedia();
  }, []);

  const handleUpload = async (file: File, fileType: string, slideDuration?: number) => {
    setUploading(true);

    try {
      const response = await uploadMedia(file, fileType as 'image' | 'video' | 'ppt', slideDuration);

      if (response && response.media) {
        message.success(`${fileType === 'ppt' ? 'PPT' : '文件'}上传成功`);
        await fetchMedia();
      }
    } catch (error: unknown) {
      console.error('Upload error:', error);
      message.error('文件上传失败');
    } finally {
      setUploading(false);
    }
  };

  // 处理 PPT 上传确认
  const handlePptUploadConfirm = async () => {
    if (!pendingPptFile) return;
    setPptUploadModalVisible(false);
    await handleUpload(pendingPptFile, 'ppt', pptSlideDuration);
    setPendingPptFile(null);
    setPptSlideDuration(5); // 重置为默认值
  };

  // 取消 PPT 上传
  const handlePptUploadCancel = () => {
    setPptUploadModalVisible(false);
    setPendingPptFile(null);
    setPptSlideDuration(5);
  };

  const handleDelete = async (media: MediaFile) => {
    modal.confirm({
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
        } catch (error: unknown) {
          console.error('Delete error:', error);
          message.error('删除失败');
        }
      },
    });
  };

  const handleRetry = async (media: MediaFile) => {
    try {
      await retryConversion(media.id);
      message.success('已重新提交转换任务');
      await fetchMedia();
    } catch (error: unknown) {
      console.error('Retry error:', error);
      const err = error as { response?: { data?: { detail?: string } } };
      const errorMsg = err.response?.data?.detail || '重试失败';
      message.error(errorMsg);
    }
  };

  const columns: ColumnsType<MediaFile> = [
    {
      title: '预览',
      dataIndex: 'thumbnail_path',
      key: 'thumbnail',
      width: 120,
      render: (_path: string, record: MediaFile) => {
        // 图片类型：显示缩略图，支持点击预览原图
        if (record.file_type === 'image') {
          const thumbnailUrl = getThumbnail(record.id);
          const previewUrl = `/api/media/${record.id}/download`;
          return (
            <Image
              src={thumbnailUrl}
              alt={record.file_name}
              width={80}
              height={60}
              style={{ borderRadius: 4, objectFit: 'cover', cursor: 'pointer' }}
              fallback="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='60' viewBox='0 0 80 60'%3E%3Crect fill='%23f0f0f0' width='80' height='60'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23999' font-size='12'%3E加载中%3C/text%3E%3C/svg%3E"
              preview={{
                src: previewUrl,
              }}
            />
          );
        }

        // PPT 类型：显示缩略图，点击预览缩略图大图
        if (record.file_type === 'ppt') {
          const thumbnailUrl = getThumbnail(record.id);
          return (
            <Image
              src={thumbnailUrl}
              alt={record.file_name}
              width={80}
              height={60}
              style={{ borderRadius: 4, objectFit: 'cover', cursor: 'pointer' }}
              fallback="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='60' viewBox='0 0 80 60'%3E%3Crect fill='%23f0f0f0' width='80' height='60'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23999' font-size='12'%3E加载中%3C/text%3E%3C/svg%3E"
              preview={{
                src: thumbnailUrl,
              }}
            />
          );
        }

        // 视频类型：显示图标（后端未生成缩略图）
        const typeConfig: Record<string, { color: string; icon: string }> = {
          image: { color: '#52c41a', icon: '🖼️' },
          video: { color: '#1890ff', icon: '🎬' },
          ppt: { color: '#fa8c16', icon: '📊' },
        };
        const config = typeConfig[record.file_type] || { color: '#999', icon: '📄' };

        return (
          <div
            style={{
              width: 80,
              height: 60,
              backgroundColor: config.color,
              borderRadius: 4,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '24px',
              color: '#fff',
            }}
            title={record.file_name}
          >
            {config.icon}
          </div>
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
        const colors = {
          image: 'green',
          video: 'blue',
          ppt: 'orange',
        } as const;
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
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => {
        if (!time) return '-';
        const date = new Date(time.replace(' ', 'T'));
        return isNaN(date.getTime()) ? '-' : date.toLocaleString('zh-CN');
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: MediaFile) => (
        <Space>
          {record.file_type === 'ppt' && record.status === 'failed' && (
            <Button
              type="link"
              icon={<RedoOutlined />}
              size="small"
              onClick={() => handleRetry(record)}
            >
              重试
            </Button>
          )}
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
    accept: 'image/*,video/*,.ppt,.pptx',
    beforeUpload: (file: File) => {
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
            ref={uploadRef}
            disabled={uploading}
            showUploadList={false}
            customRequest={(options: UploadRequestOption) => {
              const { file } = options;
              const uploadFile = file as File;
              const fileExt = uploadFile.name.split('.').pop()?.toLowerCase();
              let fileType = 'image';
              if (['jpg', 'jpeg', 'png', 'gif', 'bmp'].includes(fileExt || '')) {
                fileType = 'image';
              } else if (['mp4', 'avi', 'mov', 'mkv', 'flv'].includes(fileExt || '')) {
                fileType = 'video';
              } else if (['ppt', 'pptx'].includes(fileExt || '')) {
                fileType = 'ppt';
              }

              // PPT 文件先弹出设置对话框
              if (fileType === 'ppt') {
                setPendingPptFile(uploadFile);
                setPptUploadModalVisible(true);
              } else {
                handleUpload(uploadFile, fileType);
              }
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

      {/* PPT 幻灯片间隔设置对话框 */}
      <Modal
        title="PPT 上传设置"
        open={pptUploadModalVisible}
        onOk={handlePptUploadConfirm}
        onCancel={handlePptUploadCancel}
        okText="开始上传"
        cancelText="取消"
        confirmLoading={uploading}
      >
        <div style={{ marginBottom: 16 }}>
          <p style={{ marginBottom: 8 }}>请设置每页幻灯片的显示时长：</p>
          <Space>
            <InputNumber
              min={1}
              max={60}
              value={pptSlideDuration}
              onChange={(value) => setPptSlideDuration(value || 5)}
              addonAfter="秒"
              style={{ width: 120 }}
            />
          </Space>
          <p style={{ marginTop: 8, color: '#666', fontSize: 12 }}>
            提示：PPT 将转换为视频，每页幻灯片按设定的时长显示
          </p>
        </div>
      </Modal>
    </div>
  );
};

export default MediaListPage;
