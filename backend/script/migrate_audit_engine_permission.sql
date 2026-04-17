begin;

-- 将审核引擎菜单权限从 audit:engine:judge:view 迁移到 audit-engine:judge:view

update sys_menu
set
    identifier = 'audit-engine:judge:view',
    modified = now()
where status != 9
  and identifier = 'audit:engine:judge:view';

commit;
