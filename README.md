# montecarlo — 蒙特卡洛纸牌接龙

终端里的 Monte Carlo 纸牌接龙: 5×5 牌桌上移除相邻(横/竖/斜)同点数对子,
移除后牌向左靠拢、从牌堆补牌。52 张全部移除即获胜。

## 玩法

```bash
python -m montecarlo            # 交互游玩
python -m montecarlo --seed 42 # 固定牌序
python -m montecarlo --auto    # 贪心机器人自动游玩
```

交互时输入两个坐标移除对子, 如 `A1 B2`; `q` 退出。

## 规则

- 只有**相邻**(含对角线)且**同点数**的两张牌才能一起移除。
- 每次移除后: 每行牌向左靠拢, 空位从牌堆补齐。
- 牌桌无对子可走时**重发**: 收拢牌桌与牌堆、洗牌重发(最多 3 次)。
- 移除全部 52 张获胜; 3 次重发后仍无对子则失败。

## 设计取舍

- 纯标准库(`argparse`/`random`/`secrets`/`sys`), 无第三方依赖。
- 洗牌用 `secrets.SystemRandom`; `--seed` 固定时用可复现的 `random.Random`。
- 重发次数上限 3 次, 保证 `--auto` 必然终止。

## 已知局限

- 无悔棋、无存档、无最佳成绩; 行输入模式, 每步需回车。
- `--auto` 是贪心机器人(见对子就吃), 不是最优策略。
- 教学/娱乐用小工具。

## License

MIT, Copyright (c) 2026 ljiang9
