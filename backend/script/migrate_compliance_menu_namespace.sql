begin;

-- 将合规资产中心菜单从 audit 命名迁移到 compliance 命名。
-- 仅处理 laws / law-clauses / rules 相关菜单，不影响 audit_engine。

update sys_menu
set
    identifier = case identifier
        when 'audit:law:view' then 'compliance:law:view'
        when 'audit:rule:view' then 'compliance:rule:view'
        when 'audit:rule:create' then 'compliance:rule:create'
        when 'audit:rule:update' then 'compliance:rule:update'
        when 'audit:rule:delete' then 'compliance:rule:delete'
        else identifier
    end,
    api = case
        when api = '/api/audit/laws' then '/api/compliance/laws'
        when api = '/api/audit/law-clauses' then '/api/compliance/law-clauses'
        when api = '/api/audit/law-clauses/query' then '/api/compliance/law-clauses/query'
        when api = '/api/audit/law-clauses/{pk}' then '/api/compliance/law-clauses/{pk}'
        when api = '/api/audit/rules' then '/api/compliance/rules'
        when api = '/api/audit/rules/refresh' then '/api/compliance/rules/refresh'
        when api = '/api/audit/rules/search' then '/api/compliance/rules/search'
        when api = '/api/audit/rules/{rule_id}' then '/api/compliance/rules/{rule_id}'
        else api
    end,
    modified = now()
where status != 9
  and (
      identifier in (
          'audit:law:view',
          'audit:rule:view',
          'audit:rule:create',
          'audit:rule:update',
          'audit:rule:delete'
      )
      or api in (
          '/api/audit/laws',
          '/api/audit/law-clauses',
          '/api/audit/law-clauses/query',
          '/api/audit/law-clauses/{pk}',
          '/api/audit/rules',
          '/api/audit/rules/refresh',
          '/api/audit/rules/search',
          '/api/audit/rules/{rule_id}'
      )
  );

commit;
