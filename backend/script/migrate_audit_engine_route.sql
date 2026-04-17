begin;

-- 将审核引擎菜单接口从 /api/audit/engine/judge 迁移到 /api/audit-engine/judge
-- 不修改权限标识，仅更新菜单 API 地址。

update sys_menu
set
    api = '/api/audit-engine/judge',
    modified = now()
where status != 9
  and api = '/api/audit/engine/judge';

commit;
