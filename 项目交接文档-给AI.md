# 红星杯时间线看板 — 项目交接文档（给 AI）

## 项目概述
第六届"红星杯"大学生创新创业大赛路演 — 时间逻辑顺序图，单文件 HTML 看板，包含时间线视图和部门分工视图，数据通过 Supabase 云端同步。

## 文件清单

| 文件 | 作用 |
|------|------|
| `红星杯时间线.html` | **主文件**，包含全部 HTML/CSS/JS，约 2700 行 |
| `index.html` | 跳转页 → 红星杯时间线.html |
| `server.py` | Flask 本地服务器备用方案（端口 5050，密码 `hongxingbei2026`） |
| `sort_timeline.py` | 排序工具脚本，按截止时间重排任务 |
| `task_list.txt` | 任务清单参考 |
| `交接文档.md` | 旧版交接文档（可忽略，以此文档为准） |
| `项目交接文档-给AI.md` | 本文档 |

## 访问方式

| 方式 | 地址 |
|------|------|
| ☁️ GitHub Pages（推荐） | `https://crayon-lamb.github.io/Red-Star-Cup/` |
| 📁 本地 | `python -m http.server 8080` |

- **访问密码**：`hxb2026`
- **管理员密码**（重置用）：`hxbadmin2026`

## 部署方式

```bash
cd "C:/Users/28346/Desktop/测试"
git add "红星杯时间线.html"
git commit -m "描述你的改动"
git push
```

GitHub Pages 1-2 分钟自动更新。用户需 `Ctrl+Shift+R` 强制刷新。

---

## 数据同步架构

```
浏览器(平板) ──→ Supabase(PostgreSQL, 境外) ──→ 浏览器(电脑)
   ↓ 填负责人                              10秒轮询 ↓
  400ms后自动上传                             拉取最新
```

### Supabase 配置

- 项目 ID：`wgfdezkdgnnygprdaics`
- 表名：`tasks`
- 匿名 Key：内嵌在 HTML 的 `SUPABASE_KEY` 常量中
- SDK：直接用 `fetch()` 调 REST API，未引入外部 SDK

### 数据表结构

| 列 | 类型 | 说明 |
|----|------|------|
| `id` | TEXT (PK) | 任务唯一 ID，格式 `hxb_2026_URL编码` |
| `done` | BOOLEAN | 是否完成 |
| `owner` | TEXT | 合并后的负责人字符串，如 "张三 / 李四" |
| `depts` | TEXT | 部门列表 JSON 数组 |
| `dept_owners` | TEXT | 部门→负责人映射 JSON |

### 同步机制

- **写入**：填写负责人/勾选完成后 400ms 自动上传
- **读取**：页面加载时拉取 + 每 10 秒轮询
- **冲突**：后写覆盖先写（last-write-wins）

---

## ⚠️ 关于"国内数据库"的结论

2026年8月尝试过迁移到国内服务（腾讯云 CloudBase），结论是**不可行**：

1. **MemFire Cloud**：网站标记为不安全，无法信任
2. **LeanCloud**：已停止新用户注册
3. **阿里云 RDS Supabase**：无免费套餐，最便宜配置 ~30元/月
4. **腾讯云 CloudBase**：免费套餐禁止 Web 端 CORS 跨域访问，SDK 也无法绕过

结论：**Supabase 是唯一的免费可用方案。** 页面存储的数据仅为任务名、截止日期、打勾状态、负责人名字，不含任何个人身份信息，不属于涉密范畴。GitHub Pages + Supabase 是当前最优架构。

---

## 页面结构

### 5 个阶段

| data-phase | 名称 | 日期范围 |
|------------|------|----------|
| p1 | 一、通知与报名 | 6月 — 9月中旬 |
| p2 | 二、路演相关准备 | 7月 — 10月初 |
| p3 | 三、路演当天 | 10月13日 |
| p4 | 四、初赛赛后总结 | 路演后 |
| p5 | 五、决赛 | 2027年4月 |

### 部门与工作组
- **9 个部门**（p1/p2 默认）：学术实践部、办公室、组织部、宣传部、文艺部、生活权益部、信息技术部、研究生办公室、体育部
- **6 个工作组**（p3 默认）：票务服务组、现场秩序组、互动引导组、机动应急组、摄像组、工作组

---

## 如何修改任务

### 删除任务
找到对应的 `<div class="tl-item" data-phase="pX">` 整块删掉。

### 修改任务名称/时间
找到 `<span class="tl-name">` 或 `<span class="tl-date">` 修改文字。

### 添加任务
在对应阶段合适位置，复制 `tl-item` 块，修改名称、日期、部门。按时间排序插入。

### 任务块结构
```html
<div class="tl-item" data-phase="p1">
  <div class="tl-top">
    <span class="tl-name">任务名称</span>
    <span class="tl-date">截止日期</span>
  </div>
  <div class="tl-meta">
    <span class="tl-dept" style="...">部门名称</span>
  </div>
  <div class="tl-note">备注（可选）</div>
</div>
```

---

## 关键函数速查

| 函数 | 位置 | 作用 |
|------|------|------|
| `supabaseGetAll()` | ~1596 | 从 Supabase 拉取全部数据 |
| `supabaseUpsert(id, done, owner, depts, deptOwners)` | ~1604 | 写入/更新单条数据 |
| `supabaseDeleteAll(ids)` | ~1619 | 批量删除 |
| `syncNow(showMsg)` | ~2053 | 拉取云端 → 刷新 UI |
| `applyAllStates(tasksArray)` | ~1949 | 云端数据应用到 DOM + localStorage |
| `syncTimelineOwner(key)` | ~2408 | 汇总部门负责人 → 上传 dept_owners |
| `uploadLocalToCloud()` | ~1993 | 全部本地数据推送到云端 |
| `getDateSortKey(dateStr)` | ~2507 | 日期字符串 → 可比较数字，用于部门视图排序 |
| `buildDeptView()` | ~2445 | 渲染部门分工视图 |
| `onDeptOwnerChange(key, deptName, value)` | ~2384 | 部门视图负责人输入 → 时间线同步 + 上传 |
| `rebuildDeptOwnerRow(item, key)` | ~1770 | 重建各部门负责人输入行 |
| `buildDeptSelector(item, key)` | ~1684 | 构建部门多选下拉框 |
| `switchView(mode)` | ~2330 | 切换时间线/部门视图 |

---

## 已修复的关键 Bug

| Bug | 修复方式 | commit |
|------|----------|--------|
| 同步后部门负责人 UI 不刷新 | `syncNow` 新增 `rebuildDeptOwnerRow` UI 重建 | 9048529 |
| 部门负责人输入不上传云端 | 时间线&部门视图输入事件中新增 `syncTimelineOwner` 调用 | - |
| syncTimelineOwner 未上传 dept_owners | 新增 `dept_owners` 列，Supabase upsert 带上映射 | - |
| 换浏览器误清云端数据 | 移除危险的一次性清理逻辑 | - |
| 部门视图任务乱序 | 新增 `getDateSortKey` 日期排序函数 | 11aa522 |
| 删除负责人不生效（残留+空字符串） | `applyAllStates` 先清除旧 dept_owner 键再写入；owner 改用 `!== undefined` 检查 | 8d210e4 |

---

## 工具栏按钮

| 按钮 | 功能 |
|------|------|
| 🔄 同步 | 从云端拉取最新数据 |
| ⬆️ 上传 | 将本机全部数据推送到云端 |
| 📥 导出 | 下载全部数据为 JSON 备份 |
| 📤 导入 | 从 JSON 备份恢复数据 |
| 🗑️ 重置全部 | 清空所有数据（需管理员密码） |
| 📅/👥 | 时间线视图 / 部门分工视图切换 |

---

## 注意事项

1. 必须用 GitHub Pages 链接访问，`file://` 不支持 Supabase 同步
2. 每次部署后 `Ctrl+Shift+R` 强制刷新
3. 任务增删后部门视图自动反映
4. 部门归并规则：院/系宣传部 → 宣传部；研究生部 → 研究生办公室
5. `(宣传部/信息技术部)` 格式表示协作，自动拆分并标记 🤝
6. 不要在 localStorage 中手动修改 `_dept_owner_*` 键，会导致同步不一致
