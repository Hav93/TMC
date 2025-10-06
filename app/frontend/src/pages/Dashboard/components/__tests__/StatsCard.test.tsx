import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/utils'
import StatsCard from '../StatsCard'
import { MessageOutlined } from '@ant-design/icons'

describe('StatsCard', () => {
  it('should render with basic props', () => {
    render(
      <StatsCard
        title="今日消息"
        value={100}
        icon={<MessageOutlined />}
        color="#1890ff"
      />
    )

    expect(screen.getByText('今日消息')).toBeInTheDocument()
    expect(screen.getByText('100')).toBeInTheDocument()
  })

  it('should render with suffix', () => {
    render(
      <StatsCard
        title="成功率"
        value={95}
        suffix="%"
        icon={<MessageOutlined />}
        color="#52c41a"
      />
    )

    expect(screen.getByText('95')).toBeInTheDocument()
    expect(screen.getByText('%')).toBeInTheDocument()
  })

  it('should show loading state', () => {
    render(
      <StatsCard
        title="加载中"
        value={0}
        icon={<MessageOutlined />}
        color="#1890ff"
        loading={true}
      />
    )

    // Ant Design的Spin组件会有loading相关的class
    const card = screen.getByText('加载中').closest('.ant-card')
    expect(card).toBeInTheDocument()
  })
})

