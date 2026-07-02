import { useEffect, useState } from 'react'
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  ConfigProvider,
  Form,
  Input,
  Layout,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  theme,
} from 'antd'
import {
  FileTextOutlined,
  LogoutOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import ptBR from 'antd/locale/pt_BR'

const { Header, Sider, Content } = Layout
const { Title, Text } = Typography

const darkTheme = {
  algorithm: [theme.darkAlgorithm],
  token: {
    colorPrimary: '#1677ff',
    colorBgBase: '#0b1020',
    colorBgContainer: '#111827',
    colorBorder: '#243044',
    borderRadius: 14,
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },
  components: {
    Layout: {
      headerBg: '#111827',
      siderBg: '#111827',
      bodyBg: '#0b1020',
    },
    Table: { headerBg: '#172033' },
    Card: { headerFontSize: 15 },
  },
}

function authHeaders(token) {
  return { Authorization: `Bearer ${token}` }
}

function formatDate(value) {
  if (!value) return '-'
  const [date] = String(value).split('T')
  const parts = date.split('-')
  if (parts.length !== 3) return value
  return `${parts[2]}/${parts[1]}/${parts[0]}`
}

function formatNumber(value) {
  if (value === null || value === undefined) return '-'
  return Number(value).toLocaleString('pt-BR')
}

function formatCurrency(value) {
  if (value === null || value === undefined) return '-'
  return Number(value).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })
}

function App() {
  const [token, setToken] = useState(null)
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin')
  const [loginError, setLoginError] = useState(null)
  const [loadingLogin, setLoadingLogin] = useState(false)
  const [contracts, setContracts] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState({ q: '', service: [] })
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 })

  async function handleLogin(event) {
    event.preventDefault()
    setLoginError(null)
    setLoadingLogin(true)
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || 'Erro ao autenticar')
      }
      const data = await response.json()
      setToken(data.access_token)
    } catch (err) {
      setLoginError(err.message)
    } finally {
      setLoadingLogin(false)
    }
  }

  async function loadContracts(page = pagination.current, pageSize = pagination.pageSize) {
    if (!token) return
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ page, page_size: pageSize })
      if (filters.q) params.set('q', filters.q)
      if (filters.service?.length) params.set('service', filters.service.join(','))

      const response = await fetch(`/api/contracts?${params.toString()}`, {
        headers: authHeaders(token),
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || 'Erro ao carregar contratos')
      }
      const data = await response.json()
      setContracts(data.items)
      setTotal(data.total)
      setPagination({ current: data.page, pageSize: data.page_size })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (token) loadContracts(1, pagination.pageSize)
  }, [token])

  const columns = [
    {
      title: '#',
      key: 'row_number',
      width: 70,
      align: 'right',
      render: (_, __, index) => (pagination.current - 1) * pagination.pageSize + index + 1,
    },
    {
      title: 'Instituição',
      dataIndex: 'nome_instituicao',
      key: 'nome_instituicao',
      render: (value, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{value}</Text>
          <Text type="secondary">{record.codigo_instituicao}</Text>
        </Space>
      ),
    },
    { title: 'Contrato', dataIndex: 'numero_contrato', key: 'numero_contrato', width: 150 },
    {
      title: 'Serviços',
      dataIndex: 'servicos_contratados',
      key: 'servicos_contratados',
      render: (value) => (
        <Space wrap size={[4, 4]}>
          {String(value || '')
            .split(',')
            .map((item) => item.trim())
            .filter(Boolean)
            .map((item) => (
              <Tag color={item === 'API' ? 'blue' : item === 'Lote' ? 'cyan' : 'purple'} key={item}>
                {item}
              </Tag>
            ))}
        </Space>
      ),
    },
    { title: 'Corte inicial', dataIndex: 'dt_corte_inicial', render: formatDate, width: 130 },
    { title: 'Frequência', dataIndex: 'frequencia_corte', width: 120 },
    {
      title: 'Qtde Acessos Contratados',
      dataIndex: 'num_ac_contratados',
      align: 'right',
      width: 190,
      render: (value, record) => (record.fl_acessos_ilimitados ? '∞' : formatNumber(value)),
    },
    {
      title: 'Valor Excedente',
      dataIndex: 'valor_excedente',
      align: 'right',
      width: 150,
      render: formatCurrency,
    },
  ]

  if (!token) {
    return (
      <ConfigProvider locale={ptBR} theme={darkTheme}>
        <AntApp>
          <div className="login-page">
            <Card className="login-card" variant="borderless">
              <Space direction="vertical" size={22} style={{ width: '100%' }}>
                <div>
                  <div className="brand-mark">MC</div>
                  <Title level={2} style={{ margin: 0 }}>
                    Monitor de Contratos
                  </Title>
                  <Text type="secondary">Manutenção de contratos monitorados</Text>
                </div>
                <Form layout="vertical" requiredMark={false} onSubmitCapture={handleLogin}>
                  <Form.Item label="Usuário">
                    <Input value={username} onChange={(e) => setUsername(e.target.value)} size="large" autoFocus />
                  </Form.Item>
                  <Form.Item label="Senha">
                    <Input.Password value={password} onChange={(e) => setPassword(e.target.value)} size="large" />
                  </Form.Item>
                  <Button type="primary" htmlType="submit" block size="large" loading={loadingLogin}>
                    Entrar
                  </Button>
                </Form>
                {loginError && <Alert type="error" message={loginError} showIcon />}
                <Text type="secondary" style={{ textAlign: 'center' }}>
                  Usuário padrão: <b>admin</b> / Senha: <b>admin</b>
                </Text>
              </Space>
            </Card>
          </div>
        </AntApp>
      </ConfigProvider>
    )
  }

  return (
    <ConfigProvider locale={ptBR} theme={darkTheme}>
      <AntApp>
        <Layout className="app-shell">
          <Sider width={252} className="app-sider" breakpoint="lg" collapsedWidth="0">
            <div className="brand-block">
              <div className="brand-mark">MC</div>
              <h1 className="brand-title">Monitor de Contratos</h1>
              <p className="brand-subtitle">Contract operations</p>
            </div>
            <div className="side-item active">
              <FileTextOutlined />
              <span>Contratos</span>
            </div>
          </Sider>
          <Layout>
            <Header className="app-header">
              <div>
                <Title level={3} style={{ margin: 0 }}>
                  Contratos
                </Title>
                <Text type="secondary">Manutenção e consulta de contratos monitorados.</Text>
              </div>
              <Space>
                <Button icon={<ReloadOutlined />} onClick={() => loadContracts()}>
                  Atualizar
                </Button>
                <Button type="primary" icon={<PlusOutlined />} disabled>
                  Novo contrato
                </Button>
                <Button icon={<LogoutOutlined />} onClick={() => setToken(null)}>
                  Sair
                </Button>
              </Space>
            </Header>
            <Content className="page-content">
              <div className="page-container">
                <Card className="panel-card" title="Busca e filtros">
                  <Form
                    layout="vertical"
                    onFinish={() => loadContracts(1, pagination.pageSize)}
                    className="filter-grid"
                  >
                    <Form.Item label="Buscar">
                      <Input
                        placeholder="Instituição, código ou contrato"
                        prefix={<SearchOutlined />}
                        value={filters.q}
                        onChange={(e) => setFilters({ ...filters, q: e.target.value })}
                      />
                    </Form.Item>
                    <Form.Item label="Serviço">
                      <Select
                        mode="multiple"
                        allowClear
                        placeholder="Todos"
                        value={filters.service}
                        onChange={(value) => setFilters({ ...filters, service: value })}
                        options={['Individual', 'Lote', 'API'].map((value) => ({ value, label: value }))}
                      />
                    </Form.Item>
                    <Form.Item label=" ">
                      <Space>
                        <Button type="primary" htmlType="submit">
                          Aplicar filtros
                        </Button>
                        <Button
                          onClick={() => {
                            setFilters({ q: '', service: [] })
                            setTimeout(() => loadContracts(1, pagination.pageSize), 0)
                          }}
                        >
                          Limpar
                        </Button>
                      </Space>
                    </Form.Item>
                  </Form>
                </Card>
                <Card className="panel-card contracts-card" title={`Contratos (${total})`}>
                  {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />}
                  <Table
                    rowKey="id"
                    columns={columns}
                    dataSource={contracts}
                    loading={loading}
                    scroll={{ x: 1100 }}
                    pagination={{
                      current: pagination.current,
                      pageSize: pagination.pageSize,
                      total,
                      showSizeChanger: true,
                      pageSizeOptions: [10, 20, 50, 100],
                    }}
                    onChange={(nextPagination) => {
                      loadContracts(nextPagination.current, nextPagination.pageSize)
                    }}
                  />
                </Card>
              </div>
            </Content>
          </Layout>
        </Layout>
      </AntApp>
    </ConfigProvider>
  )
}

export default App
