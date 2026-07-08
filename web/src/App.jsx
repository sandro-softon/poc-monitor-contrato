import { useEffect, useState } from 'react'
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  ConfigProvider,
  Drawer,
  Form,
  Input,
  InputNumber,
  Layout,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
  theme,
} from 'antd'
import {
  BankOutlined,
  EditOutlined,
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
    Layout: { headerBg: '#111827', siderBg: '#111827', bodyBg: '#0b1020' },
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
  const [activePage, setActivePage] = useState('contracts')

  const [contracts, setContracts] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState({ q: '', service: [] })
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 })

  const [institutions, setInstitutions] = useState([])
  const [instTotal, setInstTotal] = useState(0)
  const [instLoading, setInstLoading] = useState(false)
  const [instError, setInstError] = useState(null)
  const [instFilters, setInstFilters] = useState({ q: '' })
  const [instPagination, setInstPagination] = useState({ current: 1, pageSize: 20 })
  const [editingInst, setEditingInst] = useState(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [savingInst, setSavingInst] = useState(false)

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

  async function loadInstitutions(page = instPagination.current, pageSize = instPagination.pageSize) {
    if (!token) return
    setInstLoading(true)
    setInstError(null)
    try {
      const params = new URLSearchParams({ page, page_size: pageSize })
      if (instFilters.q) params.set('q', instFilters.q)
      const response = await fetch(`/api/institutions?${params.toString()}`, {
        headers: authHeaders(token),
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || 'Erro ao carregar instituições')
      }
      const data = await response.json()
      setInstitutions(data.items)
      setInstTotal(data.total)
      setInstPagination({ current: data.page, pageSize: data.page_size })
    } catch (err) {
      setInstError(err.message)
    } finally {
      setInstLoading(false)
    }
  }

  useEffect(() => {
    if (token) {
      if (activePage === 'contracts') loadContracts(1, pagination.pageSize)
      else loadInstitutions(1, instPagination.pageSize)
    }
  }, [token, activePage])

  function handleEditInstitution(record) {
    setEditingInst({ ...record })
    setDrawerOpen(true)
  }

  function handleCloseDrawer() {
    setDrawerOpen(false)
    setEditingInst(null)
  }

  async function handleSaveInstitution(values) {
    if (!editingInst) return
    setSavingInst(true)
    try {
      const body = { ...values }
      for (const key of Object.keys(body)) {
        if (body[key] === '' || body[key] === null || body[key] === undefined) {
          delete body[key]
        }
      }
      const response = await fetch(`/api/institutions/${editingInst.codigo_instituicao}`, {
        method: 'PUT',
        headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || 'Erro ao salvar')
      }
      message.success('Instituição atualizada com sucesso')
      await loadInstitutions()
      handleCloseDrawer()
    } catch (err) {
      message.error(err.message)
    } finally {
      setSavingInst(false)
    }
  }

  const contractColumns = [
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

  const instColumns = [
    { title: 'Código', dataIndex: 'codigo_instituicao', key: 'codigo_instituicao', width: 120 },
    { title: 'Nome', dataIndex: 'nome_instituicao', key: 'nome_instituicao' },
    { title: 'Contrato', dataIndex: 'numero_contrato', key: 'numero_contrato', width: 140 },
    { title: 'Início', dataIndex: 'dt_ini', key: 'dt_ini', render: formatDate, width: 100 },
    { title: 'Fim', dataIndex: 'dt_fim', key: 'dt_fim', render: formatDate, width: 100 },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (v) =>
        v === 1 ? <Tag color="green">Ativo</Tag> : <Tag color="default">Inativo</Tag>,
    },
    { title: 'Produtos', dataIndex: 'produtos', key: 'produtos', width: 120 },
    {
      title: 'Ações',
      key: 'actions',
      width: 90,
      render: (_, record) => (
        <Button size="small" icon={<EditOutlined />} onClick={() => handleEditInstitution(record)}>
          Editar
        </Button>
      ),
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
                    <Input
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      size="large"
                      autoFocus
                    />
                  </Form.Item>
                  <Form.Item label="Senha">
                    <Input.Password
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      size="large"
                    />
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
            <div
              className={`side-item ${activePage === 'contracts' ? 'active' : ''}`}
              onClick={() => setActivePage('contracts')}
              style={{ cursor: 'pointer' }}
            >
              <FileTextOutlined />
              <span>Contratos</span>
            </div>
            <div
              className={`side-item ${activePage === 'institutions' ? 'active' : ''}`}
              onClick={() => setActivePage('institutions')}
              style={{ cursor: 'pointer' }}
            >
              <BankOutlined />
              <span>Instituições</span>
            </div>
          </Sider>
          <Layout>
            <Header className="app-header">
              <div>
                <Title level={3} style={{ margin: 0 }}>
                  {activePage === 'contracts' ? 'Contratos' : 'Instituições'}
                </Title>
                <Text type="secondary">
                  {activePage === 'contracts'
                    ? 'Manutenção e consulta de contratos monitorados.'
                    : 'Cadastro e manutenção de instituições.'}
                </Text>
              </div>
              <Space>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() =>
                    activePage === 'contracts' ? loadContracts() : loadInstitutions()
                  }
                >
                  Atualizar
                </Button>
                {activePage === 'contracts' && (
                  <Button type="primary" icon={<PlusOutlined />} disabled>
                    Novo contrato
                  </Button>
                )}
                <Button icon={<LogoutOutlined />} onClick={() => setToken(null)}>
                  Sair
                </Button>
              </Space>
            </Header>
            <Content className="page-content">
              <div className="page-container">
                {activePage === 'contracts' ? (
                  <>
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
                            options={['Individual', 'Lote', 'API'].map((value) => ({
                              value,
                              label: value,
                            }))}
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
                      {error && (
                        <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />
                      )}
                      <Table
                        rowKey="id"
                        columns={contractColumns}
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
                  </>
                ) : (
                  <>
                    <Card className="panel-card" title="Busca">
                      <Form
                        layout="vertical"
                        onFinish={() => loadInstitutions(1, instPagination.pageSize)}
                        className="filter-grid"
                      >
                        <Form.Item label="Buscar">
                          <Input
                            placeholder="Código, nome ou contrato"
                            prefix={<SearchOutlined />}
                            value={instFilters.q}
                            onChange={(e) => setInstFilters({ q: e.target.value })}
                          />
                        </Form.Item>
                        <Form.Item label=" ">
                          <Space>
                            <Button type="primary" htmlType="submit">
                              Aplicar filtros
                            </Button>
                            <Button
                              onClick={() => {
                                setInstFilters({ q: '' })
                                setTimeout(() => loadInstitutions(1, instPagination.pageSize), 0)
                              }}
                            >
                              Limpar
                            </Button>
                          </Space>
                        </Form.Item>
                      </Form>
                    </Card>
                    <Card className="panel-card" title={`Instituições (${instTotal})`}>
                      {instError && (
                        <Alert
                          type="error"
                          message={instError}
                          showIcon
                          style={{ marginBottom: 16 }}
                        />
                      )}
                      <Table
                        rowKey="codigo_instituicao"
                        columns={instColumns}
                        dataSource={institutions}
                        loading={instLoading}
                        scroll={{ x: 1000 }}
                        pagination={{
                          current: instPagination.current,
                          pageSize: instPagination.pageSize,
                          total: instTotal,
                          showSizeChanger: true,
                          pageSizeOptions: [10, 20, 50, 100],
                        }}
                        onChange={(nextPagination) => {
                          loadInstitutions(nextPagination.current, nextPagination.pageSize)
                        }}
                      />
                    </Card>
                    <Drawer
                      title={`Editar Instituição - ${editingInst?.codigo_instituicao || ''}`}
                      open={drawerOpen}
                      onClose={handleCloseDrawer}
                      width={520}
                    >
                      {editingInst && (
                        <Form
                          layout="vertical"
                          initialValues={{
                            nome_instituicao: editingInst.nome_instituicao,
                            numero_contrato: editingInst.numero_contrato,
                            dt_ini: editingInst.dt_ini ? editingInst.dt_ini.split('T')[0] : '',
                            dt_fim: editingInst.dt_fim ? editingInst.dt_fim.split('T')[0] : '',
                            status: editingInst.status,
                            produtos: editingInst.produtos,
                            tp_acessos: editingInst.tp_acessos,
                            num_ac_contratados: editingInst.num_ac_contratados,
                            numero_linhas_resultado: editingInst.numero_linhas_resultado,
                          }}
                          onFinish={handleSaveInstitution}
                        >
                          <Form.Item label="Código">
                            <Input disabled value={editingInst.codigo_instituicao} />
                          </Form.Item>
                          <Form.Item
                            name="nome_instituicao"
                            label="Nome"
                            rules={[{ required: true, message: 'Nome é obrigatório' }]}
                          >
                            <Input />
                          </Form.Item>
                          <Form.Item name="status" label="Status">
                            <Select
                              options={[
                                { value: 1, label: 'Ativo' },
                                { value: 0, label: 'Inativo' },
                              ]}
                            />
                          </Form.Item>
                          <Form.Item
                            name="produtos"
                            label="Produtos"
                            rules={[{ required: true, message: 'Produtos é obrigatório' }]}
                          >
                            <Input />
                          </Form.Item>
                          <Text strong style={{ display: 'block', marginBottom: 8 }}>
                            Contrato único
                          </Text>
                          <Form.Item name="numero_contrato" label="Número do Contrato">
                            <Input placeholder="Ex: CW40194" />
                          </Form.Item>
                          <Form.Item name="dt_ini" label="Data Início">
                            <Input placeholder="YYYY-MM-DD" />
                          </Form.Item>
                          <Form.Item name="dt_fim" label="Data Fim">
                            <Input placeholder="YYYY-MM-DD" />
                          </Form.Item>
                          <Form.Item name="num_ac_contratados" label="Qtde. Acessos Contratados">
                            <InputNumber style={{ width: '100%' }} min={0} />
                          </Form.Item>
                          <Form.Item
                            name="tp_acessos"
                            label="Tipo de Acesso"
                            rules={[{ required: true, message: 'Tipo de acesso é obrigatório' }]}
                          >
                            <Input />
                          </Form.Item>
                          <Text strong style={{ display: 'block', marginBottom: 8 }}>
                            Configuração de resultado
                          </Text>
                          <Form.Item name="numero_linhas_resultado" label="Número de Linhas">
                            <InputNumber style={{ width: '100%' }} min={0} />
                          </Form.Item>
                          <Form.Item>
                            <Space>
                              <Button type="primary" htmlType="submit" loading={savingInst}>
                                Salvar
                              </Button>
                              <Button onClick={handleCloseDrawer}>Cancelar</Button>
                            </Space>
                          </Form.Item>
                        </Form>
                      )}
                    </Drawer>
                  </>
                )}
              </div>
            </Content>
          </Layout>
        </Layout>
      </AntApp>
    </ConfigProvider>
  )
}

export default App
