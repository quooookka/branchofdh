function toast(msg, type="info"){
  const box = document.createElement('div');
  box.className = `toast ${type}`;
  Object.assign(box.style, {
    position:'fixed', top:'16px', right:'16px', zIndex:2000,
    background: type==='error' ? '#ffe8e6' : '#eaffef',
    color: type==='error' ? '#7f1d1d' : '#065f46',
    borderLeft: `4px solid ${type==='error' ? '#dc2626' : '#16a34a'}`,
    padding:'10px 14px', borderRadius:'6px', boxShadow:'0 6px 18px rgba(0,0,0,.12)',
    transition:'all .25s'
  });
  box.textContent = msg;
  document.body.appendChild(box);
  setTimeout(()=>{ box.style.opacity='0'; box.style.transform='translateY(-6px)'; }, 2800);
  setTimeout(()=> box.remove(), 3200);
}

async function postFormByFetch(form){
  const fd = new FormData(form);
  const res = await fetch(form.action, {
    method: form.method || 'POST',
    headers: { 'X-Requested-With': 'XMLHttpRequest' }, // 让后端知道这是 AJAX
    body: fd
  });
  let data;
  try { data = await res.json(); } catch(e){ data = { ok:false, message:'响应解析失败'}; }
  if(!res.ok || !data.ok) throw new Error(data.message || '操作失败');
  return data;
}

function findRow(el){ return el.closest('tr[data-uid]'); }

// 用已有行里的“角色下拉选项”作为模板（表格为空时再用备选模板）
function getRoleOptionsHTML(){
  const anyGrantSelect = document.querySelector('.js-grant select');
  if (anyGrantSelect) return anyGrantSelect.innerHTML;
  // 备选：如果没有任何行，页面里放一个隐藏模板 <template id="role-options">...</template>
  const tpl = document.getElementById('role-options');
  return tpl ? tpl.innerHTML : '';
}

document.addEventListener('submit', async (e)=>{
  const f = e.target;

  // 创建用户（局部刷新）
  if (f.matches('.js-create')) {
    e.preventDefault();
    try{
      const data = await postFormByFetch(f);
      // 构造新行的 HTML
      const roleOptions = getRoleOptionsHTML();
      const rolesText   = (data.roles || []).join(', ');

      const tr = document.createElement('tr');
      tr.setAttribute('data-uid', data.id);
      tr.innerHTML = `
        <td>${data.id}</td>
        <td>${data.username}</td>
        <td class="email-col">${data.email}</td>
        <td class="role-cell">${rolesText}</td>
        <td class="conduct-col">
          <form class="js-grant" data-uid="${data.id}" method="post" action="/admin/users/${data.id}/grant" style="display:inline-flex; align-items:center; margin-right:8px;">
            <select name="role">${roleOptions}</select>
            <button class="page-btn" type="submit" style="margin-left:6px;">赋权</button>
          </form>
          <form class="js-revoke" data-uid="${data.id}" method="post" action="/admin/users/${data.id}/revoke" style="display:inline-flex; align-items:center; margin-right:8px;">
            <select name="role">${roleOptions}</select>
            <button class="page-btn" type="submit" style="margin-left:6px;">回收</button>
          </form>
          <form class="js-reset" data-uid="${data.id}" method="post" action="/admin/users/${data.id}/reset-password" style="display:inline-flex; align-items:center;">
            <input name="new_password" placeholder="新密码">
            <button class="page-btn" type="submit" style="margin-left:6px;">重置密码</button>
          </form>
        </td>
        <td class="delete-col">
          <form class="js-delete" data-uid="${data.id}" method="post" action="/admin/users/${data.id}/delete">
            <button type="submit" class="btn-danger">删除用户</button>
          </form>
        </td>
      `;

      // 追加到 tbody 末尾（或根据需要插到合适位置）
      document.querySelector('.data-table tbody').appendChild(tr);

      // 清空创建表单
      f.reset();
      toast(data.message || '创建成功', 'success');
    }catch(err){
      toast(err.message || '创建失败', 'error');
    }
  }

  // 赋权
  if(f.matches('.js-grant')){
    e.preventDefault();
    try{
      const data = await postFormByFetch(f);
      const row = findRow(f);
      row.querySelector('.role-cell').textContent = (data.roles||[]).join(', ');
      toast(data.message || '赋权成功', 'success');
    }catch(err){ toast(err.message, 'error'); }
  }

  // 回收
  if(f.matches('.js-revoke')){
    e.preventDefault();
    try{
      const data = await postFormByFetch(f);
      const row = findRow(f);
      row.querySelector('.role-cell').textContent = (data.roles||[]).join(', ');
      toast(data.message || '回收成功', 'success');
    }catch(err){ toast(err.message, 'error'); }
  }

  // 重置密码
  if(f.matches('.js-reset')){
    e.preventDefault();
    try{
      const data = await postFormByFetch(f);
      f.querySelector('input[name="new_password"]').value = '';
      toast(data.message || '已重置密码', 'success');
    }catch(err){ toast(err.message, 'error'); }
  }

  // 删除
  if(f.matches('.js-delete')){
    e.preventDefault();
    if(!confirm('确认删除该用户？该操作不可撤销')) return;
    try{
      const data = await postFormByFetch(f);
      const row = findRow(f);
      row.remove();
      toast(data.message || '已删除', 'success');
    }catch(err){ toast(err.message, 'error'); }
  }
});
