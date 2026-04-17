begin;

-- 将审核引擎菜单组件路径从 audit/judge/judge 迁移到 audit-engine/judge/judge

update sys_menu
set
    component = 'audit-engine/judge/judge',
    modified = now()
where status != 9
  and component = 'audit/judge/judge';

commit;
