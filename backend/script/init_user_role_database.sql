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
-- type: 0目录 1页面 2按钮 3数据
insert into sys_menu (id, name, icon, path, type, component, pid, identifier, api, method, status, created, modified)
values
-- 系统管理目录
(1, '系统管理', 'SettingOutlined', '/main/system', 0, null, 0, null, null, null, 1, now(), now()),
(2, '用户管理', 'UserOutlined', '/main/system/user', 1, '/system/user/user', 1, 'system:user:view', '/api/system/user', 'GET', 1, now(), now()),
(3, '角色管理', 'TeamOutlined', '/main/system/role', 1, '/system/role/role', 1, 'system:role:view', '/api/system/role', 'GET', 1, now(), now()),
(4, '菜单管理', 'MenuOutlined', '/main/system/menu', 1, '/system/menu/menu', 1, 'system:menu:view', '/api/system/menu', 'GET', 1, now(), now()),

-- 审核中心目录
(10, '审核中心', 'AuditOutlined', '/main/audit', 0, null, 0, null, null, null, 1, now(), now()),
(11, '规则库', 'DatabaseOutlined', '/main/audit/rules', 1, '/audit/rules', 10, 'audit:rules:view', '/api/audit/rules', 'GET', 1, now(), now()),
(12, '规则检索', 'SearchOutlined', '/main/audit/search', 1, '/audit/search', 10, 'audit:search:use', '/api/audit/search', 'POST', 1, now(), now()),
(13, '合规判定', 'CheckCircleOutlined', '/main/audit/judge', 1, '/audit/judge', 10, 'audit:judge:execute', '/api/audit/judge', 'POST', 1, now(), now());

-- 5. 角色菜单绑定

-- super_admin 拥有全部权限
insert into sys_role_menu (id, rid, mid, status, created, modified)
values
(1, 1, 1, 1, now(), now()),
(2, 1, 2, 1, now(), now()),
(3, 1, 3, 1, now(), now()),
(4, 1, 4, 1, now(), now()),
(5, 1, 10, 1, now(), now()),
(6, 1, 11, 1, now(), now()),
(7, 1, 12, 1, now(), now()),
(8, 1, 13, 1, now(), now());

-- system_admin 只拥有系统管理
insert into sys_role_menu (id, rid, mid, status, created, modified)
values
(101, 2, 1, 1, now(), now()),
(102, 2, 2, 1, now(), now()),
(103, 2, 3, 1, now(), now()),
(104, 2, 4, 1, now(), now());

-- auditor 只拥有审核中心
insert into sys_role_menu (id, rid, mid, status, created, modified)
values
(201, 3, 10, 1, now(), now()),
(202, 3, 11, 1, now(), now()),
(203, 3, 12, 1, now(), now()),
(204, 3, 13, 1, now(), now());

-- viewer 只读查看规则和检索
insert into sys_role_menu (id, rid, mid, status, created, modified)
values
(301, 4, 10, 1, now(), now()),
(302, 4, 11, 1, now(), now()),
(303, 4, 12, 1, now(), now());

commit;
