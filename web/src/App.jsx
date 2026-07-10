import { useEffect, useMemo, useState } from 'react'
import dayjs from 'dayjs'
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  Checkbox,
  ConfigProvider,
  DatePicker,
  Drawer,
  Form,
  Input,
  InputNumber,
  Layout,
  Popconfirm,
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
  DeleteOutlined,
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

const stylePresets = {
  dark: {
    label: 'Dark Ops',
    algorithms: [theme.darkAlgorithm],
    tokens: {
      colorPrimary: '#1677ff',
      colorBgBase: '#0b1020',
      colorBgContainer: '#111827',
      colorBorder: '#243044',
      borderRadius: 14,
      fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    },
  },
  light: {
    label: 'Light SaaS',
    algorithms: [theme.defaultAlgorithm],
    tokens: {
      colorPrimary: '#111827',
      colorBgBase: '#f4f6fb',
      colorBgContainer: '#ffffff',
      colorBorder: '#e5e7eb',
      borderRadius: 16,
      fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    },
  },
  compact: {
    label: 'Compact',
    algorithms: [theme.darkAlgorithm, theme.compactAlgorithm],
    tokens: {
      colorPrimary: '#13c2c2',
      colorBgBase: '#050b13',
      colorBgContainer: '#0f172a',
      colorBorder: '#1f2a3d',
      borderRadius: 10,
      fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    },
  },
  grafana: {
    label: 'Grafana Dark',
    algorithms: [theme.darkAlgorithm],
    tableHeaderBg: '#181b1f',
    tokens: {
      colorPrimary: '#f46800',
      colorInfo: '#5794f2',
      colorSuccess: '#73bf69',
      colorWarning: '#fade2a',
      colorError: '#f2495c',
      colorBgBase: '#0b0c0e',
      colorBgContainer: '#111217',
      colorBorder: '#2f3136',
      borderRadius: 8,
      fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    },
  },
  datadog: {
    label: 'Datadog',
    algorithms: [theme.defaultAlgorithm],
    tableHeaderBg: '#f6f3fb',
    tokens: {
      colorPrimary: '#632ca6',
      colorInfo: '#2f80ed',
      colorSuccess: '#00a86b',
      colorWarning: '#ffb020',
      colorError: '#d12f2f',
      colorBgBase: '#f7f5fb',
      colorBgContainer: '#ffffff',
      colorBorder: '#ded7eb',
      borderRadius: 12,
      fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    },
  },
  cartoon: {
    label: 'Cartoon Style',
    algorithms: [theme.defaultAlgorithm],
    tableHeaderBg: '#fff0a8',
    tokens: {
      colorPrimary: '#ff5c8a',
      colorInfo: '#0099ff',
      colorSuccess: '#00b875',
      colorWarning: '#ffb800',
      colorError: '#ff3b30',
      colorBgBase: '#fff7d6',
      colorBgContainer: '#ffffff',
      colorBorder: '#1f2937',
      borderRadius: 22,
      fontFamily: 'Nunito, "Comic Sans MS", ui-rounded, system-ui, sans-serif',
    },
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

function ServicoInput({ value, onChange, ...rest }) {
  const [local, setLocal] = useState(value)

  useEffect(() => { setLocal(value) }, [value])

  return (
    <InputNumber
      value={local}
      onChange={(v) => setLocal(v)}
      onBlur={() => {
        if (local !== value) onChange(local)
      }}
      {...rest}
    />
  )
}

function formatNumber(value) {
  if (value === null || value === undefined) return '-'
  return Number(value).toLocaleString('pt-BR')
}

function App() {
  const [siderCollapsed, setSiderCollapsed] = useState(true)
  const [stylePreset, setStylePreset] = useState(
    () => localStorage.getItem('monitor-contrato-style') || 'dark'
  )
  const activePreset = stylePresets[stylePreset] || stylePresets.dark
  const isDarkStyle = ['dark', 'compact', 'grafana'].includes(stylePreset)

  const antdTheme = useMemo(() => ({
    algorithm: activePreset.algorithms,
    token: activePreset.tokens,
    components: {
      Layout: {
        headerBg: activePreset.tokens.colorBgContainer,
        siderBg: activePreset.tokens.colorBgContainer,
        bodyBg: activePreset.tokens.colorBgBase,
      },
      Table: {
        headerBg: activePreset.tableHeaderBg || (isDarkStyle ? '#172033' : '#f8fafc'),
      },
      Card: { headerFontSize: 15 },
    },
  }), [activePreset, isDarkStyle])

  function handleStylePresetChange(value) {
    setStylePreset(value)
    localStorage.setItem('monitor-contrato-style', value)
  }

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
  const [filters, setFilters] = useState({ q: '' })
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 })

  const [institutions, setInstitutions] = useState([])
  const [instTotal, setInstTotal] = useState(0)
  const [instLoading, setInstLoading] = useState(false)
  const [instError, setInstError] = useState(null)
  const [instFilters, setInstFilters] = useState({ q: '', status: 1 })
  const [instPagination, setInstPagination] = useState({ current: 1, pageSize: 20 })
  const [editingInst, setEditingInst] = useState(null)
  const [creatingNew, setCreatingNew] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [savingInst, setSavingInst] = useState(false)

  const [editingContract, setEditingContract] = useState(null)
  const [contractDrawerOpen, setContractDrawerOpen] = useState(false)
  const [savingContract, setSavingContract] = useState(false)

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
      if (instFilters.status !== null && instFilters.status !== undefined) {
        params.set('status', instFilters.status)
      }
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

  async function handleEditContract(codigo) {
    try {
      const response = await fetch(`/api/contracts/${codigo}`, { headers: authHeaders(token) })
      if (!response.ok) throw new Error('Erro ao carregar detalhes')
      const data = await response.json()
      setEditingContract(data)
      setContractDrawerOpen(true)
    } catch (err) {
      message.error(err.message)
    }
  }

  function handleCloseContractDrawer() {
    setContractDrawerOpen(false)
    setEditingContract(null)
  }

  function handleServicoChange(index, field, value) {
    if (!editingContract) return
    const servicos = [...editingContract.servicos]
    servicos[index] = { ...servicos[index], [field]: value }
    setEditingContract({ ...editingContract, servicos })
  }

  async function handleDeleteService(servicoId) {
    if (!editingContract) return
    try {
      const response = await fetch(
        `/api/contracts/${editingContract.codigo_instituicao}/services/${servicoId}`,
        { method: 'DELETE', headers: authHeaders(token) }
      )
      if (!response.ok) throw new Error('Erro ao excluir serviço')
      const updated = await response.json()
      setEditingContract(updated)
      message.success('Serviço desativado')
    } catch (err) {
      message.error(err.message)
    }
  }

  async function handleSaveContract(values) {
    if (!editingContract) return
    setSavingContract(true)
    try {
      const body = {}
      for (const [key, value] of Object.entries(values)) {
        if (value === '' || value === null || value === undefined) continue
        body[key] = value?.format ? value.format('YYYY-MM-DD') : value
      }
      delete body.codigo
      body.servicos = editingContract.servicos.map((s) => {
        const item = {
          servico: s.servico,
          num_ac_contratados: s.num_ac_contratados,
          fl_acessos_ilimitados: s.fl_acessos_ilimitados ? 1 : 0,
          valor_excedente: s.valor_excedente,
        }
        if (s.id) item.id = s.id
        return item
      })
      const response = await fetch(`/api/contracts/${editingContract.codigo_instituicao}`, {
        method: 'PUT',
        headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || 'Erro ao salvar')
      }
      message.success('Contrato atualizado com sucesso')
      await loadContracts()
      handleCloseContractDrawer()
    } catch (err) {
      message.error(err.message)
    } finally {
      setSavingContract(false)
    }
  }

  function handleNewInstitution() {
    setCreatingNew(true)
    setEditingInst({
      codigo_instituicao: null,
      nome_instituicao: '',
      numero_contrato: '',
      dt_ini: null,
      dt_fim: null,
      cod_compartilhado: null,
      dt_corte_inicial: null,
      frequencia_corte: null,
      status: 1,
      num_ac_contratados: null,
      numero_linhas_resultado: null,
    })
    setDrawerOpen(true)
  }

  function handleEditInstitution(record) {
    setCreatingNew(false)
    setEditingInst({ ...record })
    setDrawerOpen(true)
  }

  function handleCloseDrawer() {
    setDrawerOpen(false)
    setEditingInst(null)
    setCreatingNew(false)
  }

  async function handleSaveInstitution(values) {
    if (!editingInst) return
    setSavingInst(true)
    try {
      const body = {}
      for (const [key, value] of Object.entries(values)) {
        if (value === '' || value === null || value === undefined) continue
        body[key] = value?.format ? value.format('YYYY-MM-DD') : value
      }
      if (creatingNew && body.codigo_instituicao) {
        const response = await fetch(`/api/institutions`, {
          method: 'POST',
          headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        })
        if (!response.ok) {
          const data = await response.json().catch(() => ({}))
          throw new Error(data.detail || 'Erro ao criar')
        }
        message.success('Instituição criada com sucesso')
      } else {
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
      }
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
      width: 60,
      align: 'right',
      render: (_, __, index) => (pagination.current - 1) * pagination.pageSize + index + 1,
    },
    {
      title: 'Código',
      dataIndex: 'codigo_instituicao',
      key: 'codigo_instituicao',
      width: 120,
    },
    {
      title: 'Instituição',
      dataIndex: 'nome_instituicao',
      key: 'nome_instituicao',
    },
    {
      title: 'Contrato',
      dataIndex: 'numero_contrato',
      key: 'numero_contrato',
      width: 140,
    },
    { title: 'Início', dataIndex: 'dt_ini', key: 'dt_ini', render: formatDate, width: 100 },
    { title: 'Fim', dataIndex: 'dt_fim', key: 'dt_fim', render: formatDate, width: 100 },
    { title: 'Corte', dataIndex: 'dt_corte_inicial', key: 'dt_corte_inicial', render: formatDate, width: 100 },
    { title: 'Freq.', dataIndex: 'frequencia_corte', key: 'frequencia_corte', width: 90 },
    {
      title: 'Serviços',
      dataIndex: 'servicos',
      key: 'servicos',
      width: 180,
      render: (value) => (
        <Space wrap size={[4, 4]}>
          {(value || []).map((item) => (
            <Tag color={item === 'API' ? 'blue' : item === 'Lote' ? 'cyan' : 'purple'} key={item}>
              {item}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (v) =>
        v === 1 ? <Tag color="green">Ativo</Tag> : <Tag color="default">Inativo</Tag>,
    },
    {
      title: 'Ações',
      key: 'actions',
      width: 90,
      render: (_, record) => (
        <Button
          size="small"
          icon={<EditOutlined />}
          onClick={() => handleEditContract(record.codigo_instituicao)}
        >
          Editar
        </Button>
      ),
    },
  ]

  const instColumns = [
    {
      title: '#',
      key: 'row_number',
      width: 60,
      align: 'right',
      render: (_, __, index) => (instPagination.current - 1) * instPagination.pageSize + index + 1,
    },
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

  const servicoColumns = [
    {
      title: 'Serviço',
      dataIndex: 'servico',
      key: 'servico',
      width: 120,
      render: (value, record, index) => (
        <Select
          value={value}
          onChange={(v) => handleServicoChange(index, 'servico', v)}
          style={{ width: '100%' }}
          options={['Individual', 'Lote', 'API'].map((s) => ({ value: s, label: s }))}
        />
      ),
    },
    {
      title: 'Qtde Acessos',
      dataIndex: 'num_ac_contratados',
      key: 'num_ac_contratados',
      width: 130,
      render: (value, record, index) => (
        <ServicoInput
          value={value}
          onChange={(v) => handleServicoChange(index, 'num_ac_contratados', v)}
          min={0}
          disabled={record.fl_acessos_ilimitados}
          controls={false}
          style={{ width: '100%' }}
        />
      ),
    },
    {
      title: 'Ilimitado',
      dataIndex: 'fl_acessos_ilimitados',
      key: 'fl_acessos_ilimitados',
      width: 80,
      render: (value, record, index) => (
        <div style={{ textAlign: 'center' }}>
          <Checkbox
            checked={value}
            onChange={(e) => handleServicoChange(index, 'fl_acessos_ilimitados', e.target.checked)}
          />
        </div>
      ),
    },
    {
      title: 'Valor Excedente',
      dataIndex: 'valor_excedente',
      key: 'valor_excedente',
      width: 130,
      render: (value, record, index) => (
        <ServicoInput
          value={value}
          onChange={(v) => handleServicoChange(index, 'valor_excedente', v)}
          min={0}
          step={0.01}
          controls={false}
          style={{ width: '100%' }}
        />
      ),
    },
    {
      title: '',
      key: 'actions',
      width: 50,
      render: (_, record, index) =>
        record.id ? (
          <Popconfirm
            title="Desativar serviço"
            description={`Desativar o serviço "${record.servico}"?`}
            onConfirm={() => handleDeleteService(record.id)}
            okText="Confirmar"
            cancelText="Cancelar"
          >
            <Button type="text" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        ) : (
          <Button
            type="text"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => {
              const servicos = editingContract.servicos.filter((_, i) => i !== index)
              setEditingContract({ ...editingContract, servicos })
            }}
          />
        ),
    },
  ]

  if (!token) {
    return (
      <ConfigProvider locale={ptBR} theme={antdTheme}>
        <AntApp>
          <div className={`login-page theme-${stylePreset}`}>
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
                  Use suas credenciais do sistema
                </Text>
              </Space>
            </Card>
          </div>
        </AntApp>
      </ConfigProvider>
    )
  }

  return (
    <ConfigProvider locale={ptBR} theme={antdTheme}>
      <AntApp>
        <Layout className={`app-shell theme-${stylePreset}`}>
          <Sider
            width={252}
            className="app-sider"
            collapsible
            collapsed={siderCollapsed}
            collapsedWidth={80}
            trigger={null}
            onMouseEnter={() => setSiderCollapsed(false)}
            onMouseLeave={() => setSiderCollapsed(true)}
          >
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
                    ? 'Manutenção e consulta de contratos.'
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
                {activePage === 'institutions' && (
                  <Button type="primary" icon={<PlusOutlined />} onClick={handleNewInstitution}>
                    Nova Instituição
                  </Button>
                )}
                <Select
                  value={stylePreset}
                  onChange={handleStylePresetChange}
                  style={{ width: 160 }}
                  size="small"
                  options={Object.entries(stylePresets).map(([value, preset]) => ({
                    value,
                    label: preset.label,
                  }))}
                />
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
                            placeholder="Código, nome ou contrato"
                            prefix={<SearchOutlined />}
                            value={filters.q}
                            onChange={(e) => setFilters({ ...filters, q: e.target.value })}
                          />
                        </Form.Item>
                        <Form.Item label=" ">
                          <Space>
                            <Button type="primary" htmlType="submit">
                              Aplicar filtros
                            </Button>
                            <Button
                              onClick={() => {
                                setFilters({ q: '' })
                                setTimeout(() => loadContracts(1, pagination.pageSize), 0)
                              }}
                            >
                              Limpar
                            </Button>
                          </Space>
                        </Form.Item>
                      </Form>
                    </Card>
                    <Card className="panel-card" title={`Contratos (${total})`}>
                      {error && (
                        <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />
                      )}
                      <Table
                        rowKey="codigo_instituicao"
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
                    <Drawer
                      title={
                        editingContract
                          ? `${editingContract.nome_instituicao} (${editingContract.codigo_instituicao})`
                          : 'Carregando...'
                      }
                      open={contractDrawerOpen}
                      onClose={handleCloseContractDrawer}
                      width={640}
                    >
                      {editingContract && (
                        <Form
                          layout="vertical"
                          initialValues={{
                            numero_contrato: editingContract.numero_contrato,
                            dt_ini: editingContract.dt_ini ? dayjs(editingContract.dt_ini.split('T')[0]) : null,
                            dt_fim: editingContract.dt_fim ? dayjs(editingContract.dt_fim.split('T')[0]) : null,
                            cod_compartilhado: editingContract.cod_compartilhado,
                            dt_corte_inicial: editingContract.dt_corte_inicial
                              ? dayjs(editingContract.dt_corte_inicial.split('T')[0])
                              : null,
                            frequencia_corte: editingContract.frequencia_corte,
                          }}
                          onFinish={handleSaveContract}
                        >
                          <Text strong style={{ display: 'block', marginBottom: 8 }}>
                            Dados do Contrato
                          </Text>

                          <div style={{ display: 'flex', gap: 12 }}>
                            <Form.Item label="Código" style={{ flex: 1 }}>
                              <Input disabled value={editingContract.codigo_instituicao} />
                            </Form.Item>
                            <Form.Item name="cod_compartilhado" label="Cod. Compartilhado" style={{ flex: 1 }}>
                              <Input style={{ width: '100%' }} />
                            </Form.Item>
                          </div>

                          <Form.Item label="Instituição">
                            <Input disabled value={editingContract.nome_instituicao} />
                          </Form.Item>

                          <Form.Item name="numero_contrato" label="Número do Contrato">
                            <Input />
                          </Form.Item>

                          <div style={{ display: 'flex', gap: 12 }}>
                            <Form.Item name="dt_ini" label="Data Início" style={{ flex: 1 }}>
                              <DatePicker format="DD/MM/YYYY" className="center-date" style={{ width: '100%' }} allowClear={false} />
                            </Form.Item>
                            <Form.Item
                              name="dt_fim"
                              label="Data Fim"
                              style={{ flex: 1 }}
                              dependencies={['dt_ini']}
                              rules={[
                                ({ getFieldValue }) => ({
                                  validator(_, value) {
                                    const ini = getFieldValue('dt_ini')
                                    if (!ini || !value || value.isAfter(ini)) return Promise.resolve()
                                    return Promise.reject(new Error('Data Fim deve ser maior que Data Início'))
                                  },
                                }),
                              ]}
                            >
                              <DatePicker format="DD/MM/YYYY" className="center-date" style={{ width: '100%' }} allowClear={false} />
                            </Form.Item>
                            <Form.Item name="dt_corte_inicial" label="Corte Inicial" style={{ flex: 1 }}>
                              <DatePicker format="DD/MM/YYYY" className="center-date" style={{ width: '100%' }} allowClear={false} />
                            </Form.Item>
                          </div>

                          <Form.Item name="frequencia_corte" label="Frequência">
                            <Select
                              options={['Mensal', 'Trimestral', 'Semestral', 'Anual'].map((v) => ({
                                value: v,
                                label: v,
                              }))}
                            />
                          </Form.Item>

                          <Text strong style={{ display: 'block', marginBottom: 8, marginTop: 16 }}>
                            Serviços
                          </Text>

                          <div style={{ marginBottom: 8 }}>
                            <Button
                              size="small"
                              type="dashed"
                              onClick={() => {
                                const servicos = editingContract.servicos || []
                                setEditingContract({
                                  ...editingContract,
                                  servicos: [
                                    ...servicos,
                                    {
                                      id: null,
                                      servico: 'Individual',
                                      num_ac_contratados: null,
                                      fl_acessos_ilimitados: false,
                                      valor_excedente: null,
                                    },
                                  ],
                                })
                              }}
                            >
                              + Adicionar Serviço
                            </Button>
                          </div>

                          <Table
                            rowKey={(r) => r.id ?? `new-${r.servico}-${Math.random()}`
                            }
                            columns={servicoColumns}
                            dataSource={editingContract.servicos}
                            pagination={false}
                            scroll={{ x: 530 }}
                            size="small"
                          />

                          <Form.Item style={{ marginTop: 24 }}>
                            <Space>
                              <Button type="primary" htmlType="submit" loading={savingContract}>
                                Salvar
                              </Button>
                              <Button onClick={handleCloseContractDrawer}>Cancelar</Button>
                            </Space>
                          </Form.Item>
                        </Form>
                      )}
                    </Drawer>
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
                            onChange={(e) => setInstFilters({ ...instFilters, q: e.target.value })}
                          />
                        </Form.Item>
                        <Form.Item label="Status">
                          <Select
                            allowClear
                            placeholder="Todos"
                            value={instFilters.status}
                            onChange={(value) => {
                              const newStatus = value !== undefined ? value : null
                              setInstFilters({ ...instFilters, status: newStatus })
                              loadInstitutions(1, instPagination.pageSize)
                            }}
                            options={[
                              { value: 1, label: 'Ativo' },
                              { value: 0, label: 'Inativo' },
                            ]}
                          />
                        </Form.Item>
                        <Form.Item label=" ">
                          <Space>
                            <Button type="primary" htmlType="submit">
                              Aplicar filtros
                            </Button>
                            <Button
                              onClick={() => {
                                setInstFilters({ q: '', status: null })
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
                      title={
                        creatingNew
                          ? 'Nova Instituição'
                          : `Editar Instituição - ${editingInst?.codigo_instituicao || ''}`
                      }
                      open={drawerOpen}
                      onClose={handleCloseDrawer}
                      width={520}
                    >
                      {editingInst && (
                        <Form
                          layout="vertical"
                          initialValues={{
                            codigo_instituicao: editingInst.codigo_instituicao,
                            nome_instituicao: editingInst.nome_instituicao,
                            numero_contrato: editingInst.numero_contrato,
                            dt_ini: editingInst.dt_ini ? dayjs(editingInst.dt_ini.split('T')[0]) : null,
                            dt_fim: editingInst.dt_fim ? dayjs(editingInst.dt_fim.split('T')[0]) : null,
                            cod_compartilhado: editingInst.cod_compartilhado,
                            dt_corte_inicial: editingInst.dt_corte_inicial
                              ? dayjs(editingInst.dt_corte_inicial.split('T')[0])
                              : null,
                            frequencia_corte: editingInst.frequencia_corte,
                            status: editingInst.status,
                            num_ac_contratados: editingInst.num_ac_contratados,
                            numero_linhas_resultado: editingInst.numero_linhas_resultado,
                          }}
                          onFinish={handleSaveInstitution}
                        >
                          <Form.Item
                            name="codigo_instituicao"
                            label="Código"
                            rules={[{ required: true, message: 'Código é obrigatório' }]}
                          >
                            <Input disabled={!creatingNew} />
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
                          <Text strong style={{ display: 'block', marginBottom: 8 }}>
                            Contrato
                          </Text>
                          <Form.Item name="numero_contrato" label="Número do Contrato">
                            <Input />
                          </Form.Item>
                          <div style={{ display: 'flex', gap: 12 }}>
                            <Form.Item name="dt_ini" label="Data Início" style={{ flex: 1 }}>
                              <DatePicker format="DD/MM/YYYY" className="center-date" style={{ width: '100%' }} allowClear={false} />
                            </Form.Item>
                            <Form.Item
                              name="dt_fim"
                              label="Data Fim"
                              style={{ flex: 1 }}
                              dependencies={['dt_ini']}
                              rules={[
                                ({ getFieldValue }) => ({
                                  validator(_, value) {
                                    const ini = getFieldValue('dt_ini')
                                    if (!ini || !value || value.isAfter(ini)) return Promise.resolve()
                                    return Promise.reject(new Error('Data Fim deve ser maior que Data Início'))
                                  },
                                }),
                              ]}
                            >
                              <DatePicker format="DD/MM/YYYY" className="center-date" style={{ width: '100%' }} allowClear={false} />
                            </Form.Item>
                            <Form.Item name="dt_corte_inicial" label="Corte Inicial" style={{ flex: 1 }}>
                              <DatePicker format="DD/MM/YYYY" className="center-date" style={{ width: '100%' }} allowClear={false} />
                            </Form.Item>
                          </div>
                          <Form.Item name="cod_compartilhado" label="Código Compartilhado">
                            <Input style={{ width: '100%' }} />
                          </Form.Item>
                          <Form.Item name="frequencia_corte" label="Frequência">
                            <Select
                              options={['Mensal', 'Trimestral', 'Semestral', 'Anual'].map((v) => ({
                                value: v,
                                label: v,
                              }))}
                            />
                          </Form.Item>
                          <Form.Item name="num_ac_contratados" label="Qtde. Acessos Contratados">
                            <InputNumber style={{ width: '100%' }} min={0} />
                          </Form.Item>
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
