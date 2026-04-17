begin;

-- 先清空权限相关测试数据
delete from sys_role_menu;
delete from sys_user_role;
delete from sys_menu;
delete from sys_user;
delete from sys_role;

-- 1. 创建角色
insert into sys_role (id, name, remark, status, created, modified)
values
(1, 'super_admin', '超级管理员', 1, now(), now()),
(2, 'system_admin', '系统管理员', 1, now(), now()),
(3, 'auditor', '审核员', 1, now(), now()),
(4, 'viewer', '查看员', 1, now(), now());

-- 2. 创建用户
insert into sys_user (id, username, nickname, password, status, created, modified)
values
(1, 'super_admin', '超级管理员', '$2b$12$W3K3sucHNbmEDJdCRwT8WOMvOPYEZ8y0r0UiqjcDFMazVYovFz19m', 1, now(), now()),
(2, 'system_admin', '系统管理员', '$2b$12$W3K3sucHNbmEDJdCRwT8WOMvOPYEZ8y0r0UiqjcDFMazVYovFz19m', 1, now(), now()),
(3, 'auditor_01', '审核员1', '$2b$12$W3K3sucHNbmEDJdCRwT8WOMvOPYEZ8y0r0UiqjcDFMazVYovFz19m', 1, now(), now()),
(4, 'viewer_01', '查看员1', '$2b$12$W3K3sucHNbmEDJdCRwT8WOMvOPYEZ8y0r0UiqjcDFMazVYovFz19m', 1, now(), now());

-- 3. 用户角色绑定
-- status=5 表示当前激活角色
insert into sys_user_role (id, uid, rid, status, created, modified)
values
(1, 1, 1, 5, now(), now()),
(2, 2, 2, 5, now(), now()),
(3, 3, 3, 5, now(), now()),
(4, 4, 4, 5, now(), now());

-- 4. 创建菜单
-- type: 0目录 1页面 2按钮 3数据权限
insert into sys_menu (id, name, icon, path, type, component, pid, identifier, api, method, status, created, modified)
values
-- 系统管理目录
(1, '系统管理', 'SettingOutlined', '/main/system', 0, null, 0, null, null, null, 1, now(), now()),
(2, '用户管理', 'UserOutlined', '/main/system/user', 1, 'user/user', 1, 'system:user:view', '/api/system/user', 'GET', 1, now(), now()),
(101, '新增用户', null, null, 2, null, 2, 'user:create', '/api/system/user', 'POST', 1, now(), now()),
(102, '编辑用户', null, null, 2, null, 2, 'user:update', '/api/system/user/{pk}', 'PUT', 1, now(), now()),
(103, '删除用户', null, null, 2, null, 2, 'user:delete', '/api/system/user/{pk}', 'DELETE', 1, now(), now()),
(3, '角色管理', 'TeamOutlined', '/main/system/role', 1, 'role/role', 1, 'system:role:view', '/api/system/role', 'GET', 1, now(), now()),
(111, '新增角色', null, null, 2, null, 3, 'role:create', '/api/system/role', 'POST', 1, now(), now()),
(112, '编辑角色', null, null, 2, null, 3, 'role:update', '/api/system/role/{pk}', 'PUT', 1, now(), now()),
(113, '删除角色', null, null, 2, null, 3, 'role:delete', '/api/system/role/{pk}', 'DELETE', 1, now(), now()),
(4, '菜单管理', 'MenuOutlined', '/main/system/menu', 1, 'menu/menu', 1, 'system:menu:view', '/api/system/menu', 'GET', 1, now(), now()),
(121, '新增菜单', null, null, 2, null, 4, 'menu:create', '/api/system/menu', 'POST', 1, now(), now()),
(122, '编辑菜单', null, null, 2, null, 4, 'menu:update', '/api/system/menu/{pk}', 'PUT', 1, now(), now()),
(123, '删除菜单', null, null, 2, null, 4, 'menu:delete', '/api/system/menu/{pk}', 'DELETE', 1, now(), now()),

-- 业务管理目录
(10, '业务管理', 'AuditOutlined', '/main/business', 0, null, 0, null, null, null, 1, now(), now()),
(11, '法律文件库管理', 'DatabaseOutlined', '/main/business/law', 1, 'rule-center/law/law', 10, 'compliance:law:view', '/api/compliance/laws', 'GET', 1, now(), now()),
(211, '法规条款查询', null, null, 3, null, 11, null, '/api/compliance/law-clauses/query', 'POST', 1, now(), now()),
(212, '新增法规条款', null, null, 2, null, 11, 'law:create', '/api/compliance/law-clauses', 'POST', 1, now(), now()),
(213, '编辑法规条款', null, null, 2, null, 11, 'law:update', '/api/compliance/law-clauses/{pk}', 'PUT', 1, now(), now()),
(214, '删除法规条款', null, null, 2, null, 11, 'law:delete', '/api/compliance/law-clauses/{pk}', 'DELETE', 1, now(), now()),
(12, '审核规则管理', 'CheckCircleOutlined', '/main/business/rule', 1, 'rule-center/rule/rule', 10, 'compliance:rule:view', '/api/compliance/rules', 'GET', 1, now(), now()),
(221, '刷新规则缓存', null, null, 3, null, 12, null, '/api/compliance/rules/refresh', 'GET', 1, now(), now()),
(13, '规则检索', null, null, 3, null, 12, null, '/api/compliance/rules/search', 'POST', 1, now(), now()),
(222, '新增规则', null, null, 2, null, 12, 'compliance:rule:create', '/api/compliance/rules', 'POST', 1, now(), now()),
(223, '编辑规则', null, null, 2, null, 12, 'compliance:rule:update', '/api/compliance/rules/{rule_id}', 'PUT', 1, now(), now()),
(224, '删除规则', null, null, 2, null, 12, 'compliance:rule:delete', '/api/compliance/rules/{rule_id}', 'DELETE', 1, now(), now()),
(14, '前往审核', 'SearchOutlined', '/main/audit-engine/judge', 1, 'audit-engine/judge/judge', 10, 'audit-engine:judge:view', '/api/audit-engine/judge', 'POST', 1, now(), now());

-- 5. 角色菜单绑定

-- super_admin 拥有全部权限
insert into sys_role_menu (id, rid, mid, status, created, modified)
values
(1, 1, 1, 1, now(), now()),
(2, 1, 2, 1, now(), now()),
(3, 1, 101, 1, now(), now()),
(4, 1, 102, 1, now(), now()),
(5, 1, 103, 1, now(), now()),
(6, 1, 3, 1, now(), now()),
(7, 1, 111, 1, now(), now()),
(8, 1, 112, 1, now(), now()),
(9, 1, 113, 1, now(), now()),
(10, 1, 4, 1, now(), now()),
(11, 1, 121, 1, now(), now()),
(12, 1, 122, 1, now(), now()),
(13, 1, 123, 1, now(), now()),
(14, 1, 10, 1, now(), now()),
(15, 1, 11, 1, now(), now()),
(16, 1, 211, 1, now(), now()),
(17, 1, 212, 1, now(), now()),
(18, 1, 213, 1, now(), now()),
(19, 1, 214, 1, now(), now()),
(20, 1, 12, 1, now(), now()),
(21, 1, 221, 1, now(), now()),
(22, 1, 222, 1, now(), now()),
(23, 1, 223, 1, now(), now()),
(24, 1, 224, 1, now(), now()),
(25, 1, 13, 1, now(), now()),
(26, 1, 14, 1, now(), now());

-- system_admin 只拥有系统管理
insert into sys_role_menu (id, rid, mid, status, created, modified)
values
(101, 2, 1, 1, now(), now()),
(102, 2, 2, 1, now(), now()),
(103, 2, 101, 1, now(), now()),
(104, 2, 102, 1, now(), now()),
(105, 2, 103, 1, now(), now()),
(106, 2, 3, 1, now(), now()),
(107, 2, 111, 1, now(), now()),
(108, 2, 112, 1, now(), now()),
(109, 2, 113, 1, now(), now()),
(110, 2, 4, 1, now(), now()),
(111, 2, 121, 1, now(), now()),
(112, 2, 122, 1, now(), now()),
(113, 2, 123, 1, now(), now());

-- auditor 拥有业务管理全流程权限
insert into sys_role_menu (id, rid, mid, status, created, modified)
values
(201, 3, 10, 1, now(), now()),
(202, 3, 11, 1, now(), now()),
(203, 3, 211, 1, now(), now()),
(204, 3, 212, 1, now(), now()),
(205, 3, 213, 1, now(), now()),
(206, 3, 214, 1, now(), now()),
(207, 3, 12, 1, now(), now()),
(208, 3, 221, 1, now(), now()),
(209, 3, 222, 1, now(), now()),
(210, 3, 223, 1, now(), now()),
(211, 3, 224, 1, now(), now()),
(212, 3, 13, 1, now(), now()),
(213, 3, 14, 1, now(), now());

-- viewer 只读查看法规和规则
insert into sys_role_menu (id, rid, mid, status, created, modified)
values
(301, 4, 10, 1, now(), now()),
(302, 4, 11, 1, now(), now()),
(303, 4, 211, 1, now(), now()),
(304, 4, 12, 1, now(), now());

commit;
