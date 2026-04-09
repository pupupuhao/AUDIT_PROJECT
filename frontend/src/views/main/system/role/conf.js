export const columns = [
  {
    title: 'ID',
    dataIndex: 'id',
    key: 'id'
  },
  {
    title: '名称',
    dataIndex: 'name',
    key: 'name'
  },
  {
    title: '描述',
    dataIndex: 'remark',
    key: 'remark'
  },
  {
    title: '用户数',
    dataIndex: 'user_count',
    key: 'user_count'
  },
  {
    title: '已分配用户',
    dataIndex: 'users',
    key: 'users'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status'
  },
  {
    title: '创建时间',
    dataIndex: 'created',
    key: 'created'
  },
  {
    title: '更新时间',
    dataIndex: 'modified',
    key: 'modified'
  },
  {
    title: '操作',
    key: 'action'
  }
]

export const rules = {
  name: [
    { required: true, message: '请输入名称', trigger: 'blur' },
    { min: 2, max: 20, message: '2~20', trigger: 'blur' }
  ],
  remark: [
    { required: true, message: '请输入描述', trigger: 'blur' },
    { min: 1, max: 50, message: '1~50', trigger: 'blur' }
  ],
  menus: [{ required: true, message: '请选择菜单', trigger: 'blur' }]
}

// a-tree组件 字段替换 适配接口返回数据
export const treeFieldNames = {
  key: 'id',
  title: 'name',
  children: 'children'
}
