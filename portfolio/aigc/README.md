## AIGC 提示词与生成示例（面试作品集）

这个目录不追求“自动化一键到底”，而是给你能讲清楚的工程细节：

- `midjourney/`：把提示词模板和参数解释整理成结构化库（`prompt_database.json`）
- `stable_diffusion/`：给出一个 ControlNet + Stable Diffusion 的最小工程示例脚本

你在面试里可以这么讲：

1. 为什么要用模板库：减少“记不住参数/复现困难”
2. 为什么要用 ControlNet：让生成结果有条件约束（边缘/结构）
3. 工程上怎么取舍：显存、下载耗时、可复现的输入输出

