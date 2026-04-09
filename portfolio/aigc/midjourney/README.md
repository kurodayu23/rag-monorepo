## Midjourney 提示词模板库

这个目录把“会用但不难记”的提示词整理成模板 + 参数说明。

### 你会拿到什么

- `prompt_database.json`：模板（如 `cinematic_portrait`）和参数解释（如 `--c/--s/--w/--seed`）

### 基本用法（手工拼提示词）

例如你想生成“赛博海边城市的电影感人像”，可以先选模板：

- 模板：`cinematic_portrait`
- 把 `{subject}` 替换为你的主题

再把你常用的参数一起加上（如果需要复现风格就用固定 `--seed`）。

### 结构参考

模板字段里固定了 `--ar/--style/--v` 等参数；你只需要填主体内容（`{subject}`）。

