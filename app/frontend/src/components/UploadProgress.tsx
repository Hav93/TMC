/**
 * 上传进度组件
 * 
 * 实时显示文件上传进度
 */
import React from 'react';
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  Chip,
  Stack,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Upload as UploadIcon,
  Speed as SpeedIcon,
  Timer as TimerIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { useUploadProgress, UploadProgress as UploadProgressType } from '../hooks/useUploadProgress';

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatTime = (seconds: number | null): string => {
  if (seconds === null || seconds === 0) return '--';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}小时${minutes}分${secs}秒`;
  } else if (minutes > 0) {
    return `${minutes}分${secs}秒`;
  } else {
    return `${secs}秒`;
  }
};

interface UploadItemProps {
  upload: UploadProgressType;
}

const UploadItem: React.FC<UploadItemProps> = ({ upload }) => {
  const [expanded, setExpanded] = React.useState(true);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
      case 'quick_success':
        return 'success';
      case 'failed':
        return 'error';
      case 'uploading':
        return 'primary';
      case 'hashing':
      case 'checking':
        return 'info';
      default:
        return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending':
        return '待上传';
      case 'hashing':
        return '计算哈希';
      case 'checking':
        return '检查秒传';
      case 'quick_success':
        return '秒传成功';
      case 'uploading':
        return '上传中';
      case 'success':
        return '上传成功';
      case 'failed':
        return '上传失败';
      case 'cancelled':
        return '已取消';
      default:
        return status;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
      case 'quick_success':
        return <SuccessIcon />;
      case 'failed':
        return <ErrorIcon />;
      case 'uploading':
      case 'hashing':
      case 'checking':
        return <UploadIcon />;
      default:
        return null;
    }
  };

  return (
    <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
      <Stack spacing={1}>
        {/* 文件名和状态 */}
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" alignItems="center" spacing={1} flex={1}>
            <Typography variant="body1" fontWeight="bold" noWrap>
              {upload.file_name}
            </Typography>
            <Chip
              icon={getStatusIcon(upload.status)}
              label={getStatusText(upload.status)}
              color={getStatusColor(upload.status)}
              size="small"
            />
            {upload.is_quick_upload && (
              <Chip label="秒传" color="success" size="small" variant="outlined" />
            )}
          </Stack>
          <IconButton size="small" onClick={() => setExpanded(!expanded)}>
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Stack>

        {/* 进度条 */}
        <Box>
          <LinearProgress
            variant="determinate"
            value={upload.percentage}
            color={
              upload.status === 'failed' ? 'error' :
              upload.status === 'success' || upload.status === 'quick_success' ? 'success' :
              'primary'
            }
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
            {upload.percentage.toFixed(2)}% ({formatFileSize(upload.uploaded_bytes)} / {formatFileSize(upload.total_bytes)})
          </Typography>
        </Box>

        {/* 详细信息 */}
        <Collapse in={expanded}>
          <Stack spacing={1} sx={{ mt: 1 }}>
            {/* 分片信息 */}
            {upload.total_parts > 0 && (
              <Stack direction="row" alignItems="center" spacing={1}>
                <Typography variant="caption" color="text.secondary">
                  分片进度:
                </Typography>
                <Typography variant="caption">
                  {upload.uploaded_parts} / {upload.total_parts}
                </Typography>
              </Stack>
            )}

            {/* 速度和时间 */}
            {upload.status === 'uploading' && (
              <Stack direction="row" spacing={2}>
                <Stack direction="row" alignItems="center" spacing={0.5}>
                  <SpeedIcon fontSize="small" color="action" />
                  <Typography variant="caption" color="text.secondary">
                    {upload.speed_mbps.toFixed(2)} MB/s
                  </Typography>
                </Stack>
                <Stack direction="row" alignItems="center" spacing={0.5}>
                  <TimerIcon fontSize="small" color="action" />
                  <Typography variant="caption" color="text.secondary">
                    已用时: {formatTime(upload.elapsed_seconds)}
                  </Typography>
                </Stack>
                {upload.eta_seconds !== null && (
                  <Stack direction="row" alignItems="center" spacing={0.5}>
                    <TimerIcon fontSize="small" color="action" />
                    <Typography variant="caption" color="text.secondary">
                      剩余: {formatTime(upload.eta_seconds)}
                    </Typography>
                  </Stack>
                )}
              </Stack>
            )}

            {/* 错误信息 */}
            {upload.error_message && (
              <Typography variant="caption" color="error">
                错误: {upload.error_message}
              </Typography>
            )}

            {/* 文件ID */}
            {upload.file_id && (
              <Typography variant="caption" color="text.secondary">
                文件ID: {upload.file_id}
              </Typography>
            )}
          </Stack>
        </Collapse>
      </Stack>
    </Paper>
  );
};

export const UploadProgressList: React.FC = () => {
  const { uploads, connected } = useUploadProgress();

  if (!connected) {
    return (
      <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
        <Typography variant="body2" color="warning.main">
          ⚠️ 未连接到上传进度服务器
        </Typography>
      </Paper>
    );
  }

  if (uploads.length === 0) {
    return (
      <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          暂无上传任务
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>
        上传任务 ({uploads.length})
      </Typography>
      {uploads.map((upload, index) => (
        <UploadItem key={`${upload.file_name}-${index}`} upload={upload} />
      ))}
    </Box>
  );
};

export default UploadProgressList;

