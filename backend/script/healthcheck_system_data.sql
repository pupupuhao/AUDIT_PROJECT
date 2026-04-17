-- 系统管理健康检查 SQL
-- 关注菜单树完整性、角色菜单关联完整性、角色重复、用户角色重复及多激活角色问题。

-- 1. 孤儿菜单：父节点不存在或父节点已删除
select
    m.id,
    m.name,
    m.pid,
    m.path,
    m.component
from sys_menu m
left join sys_menu parent on parent.id = m.pid and parent.status != 9
where m.status != 9
  and m.pid is not null
  and m.pid != 0
  and parent.id is null
order by m.id;

-- 2. 角色菜单引用不存在或已删除的菜单
select
    rm.id,
    rm.rid,
    rm.mid,
    rm.status
from sys_role_menu rm
left join sys_menu m on m.id = rm.mid and m.status != 9
where rm.status != 9
  and m.id is null
order by rm.id;

-- 3. 角色菜单引用不存在或已删除的角色
select
    rm.id,
    rm.rid,
    rm.mid,
    rm.status
from sys_role_menu rm
left join sys_role r on r.id = rm.rid and r.status != 9
where rm.status != 9
  and r.id is null
order by rm.id;

-- 4. 重复角色名
select
    name,
    count(*) as duplicate_count,
    array_agg(id order by id) as role_ids
from sys_role
where status != 9
group by name
having count(*) > 1
order by name;

-- 5. 同一用户重复绑定同一角色
select
    uid,
    rid,
    count(*) as duplicate_count,
    array_agg(id order by id) as relation_ids
from sys_user_role
where status != 9
group by uid, rid
having count(*) > 1
order by uid, rid;

-- 6. 同一用户存在多个激活角色
select
    uid,
    count(*) as active_role_count,
    array_agg(rid order by rid) as active_role_ids
from sys_user_role
where status = 5
group by uid
having count(*) > 1
order by uid;

-- 7. 激活角色指向不存在或已删除的角色
select
    ur.id,
    ur.uid,
    ur.rid,
    ur.status
from sys_user_role ur
left join sys_role r on r.id = ur.rid and r.status != 9
where ur.status = 5
  and r.id is null
order by ur.id;
