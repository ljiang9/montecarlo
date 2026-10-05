#!/usr/bin/env python3
"""Monte Carlo solitaire (蒙特卡洛纸牌接龙).

5x5 牌桌, 移除相邻(横/竖/斜)同点数对子; 移除后向左靠拢并从牌堆补牌.
全部移除 52 张即获胜. 纯标准库.
"""

import argparse
import random
import secrets
import sys

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
SUITS = ["♠", "♥", "♦", "♣"]

ROWS, COLS = 5, 5


def new_deck(rng):
    deck = [(r, s) for s in SUITS for r in RANKS]
    rng.shuffle(deck)
    return deck


def card_name(card):
    r, s = card
    return f"{s}{r}"


def adjacent(p1, p2):
    """两格是否相邻(含对角线)."""
    (r1, c1), (r2, c2) = p1, p2
    return (r1, c1) != (r2, c2) and abs(r1 - r2) <= 1 and abs(c1 - c2) <= 1


class Game:
    MAX_REDEALS = 3

    def __init__(self, seed=None):
        self.rng = random.Random(seed) if seed is not None else secrets.SystemRandom()
        deck = new_deck(self.rng)
        self.tableau = [[deck.pop() for _ in range(COLS)] for _ in range(ROWS)]
        self.stock = deck  # 27 张
        self.removed = 0
        self.redeals = 0

    def valid(self, r, c):
        return 0 <= r < ROWS and 0 <= c < COLS and self.tableau[r][c] is not None

    def find_pairs(self):
        """返回所有可移除对子 [(p1, p2), ...]."""
        pairs = []
        cells = [(r, c) for r in range(ROWS) for c in range(COLS) if self.valid(r, c)]
        for i, p1 in enumerate(cells):
            for p2 in cells[i + 1:]:
                if (self.tableau[p1[0]][p1[1]][0] == self.tableau[p2[0]][p2[1]][0]
                        and adjacent(p1, p2)):
                    pairs.append((p1, p2))
        return pairs

    def remove_pair(self, p1, p2):
        """移除对子, 成功返回 True."""
        (r1, c1), (r2, c2) = p1, p2
        if not (self.valid(r1, c1) and self.valid(r2, c2)):
            return False
        a, b = self.tableau[r1][c1], self.tableau[r2][c2]
        if a[0] != b[0] or not adjacent(p1, p2):
            return False
        self.tableau[r1][c1] = None
        self.tableau[r2][c2] = None
        self.removed += 2
        self._consolidate()
        return True

    def _consolidate(self):
        """向左靠拢, 空位从牌堆补."""
        cards = [self.tableau[r][c] for r in range(ROWS) for c in range(COLS)
                 if self.tableau[r][c] is not None]
        while self.stock and len(cards) < ROWS * COLS:
            cards.append(self.stock.pop())
        self.tableau = [cards[r * COLS:(r + 1) * COLS] + [None] * COLS
                        for r in range(ROWS)]
        for r in range(ROWS):
            self.tableau[r] = self.tableau[r][:COLS]

    def won(self):
        return self.removed == 52

    def redeal(self):
        """无对子可走时重发: 收拢牌桌+牌堆, 洗牌重发(限 MAX_REDEALS 次)。"""
        if self.redeals >= self.MAX_REDEALS:
            return False
        cards = [c for row in self.tableau for c in row if c is not None] + self.stock
        self.rng.shuffle(cards)
        new_tab = []
        for _ in range(ROWS):
            row = [cards.pop() if cards else None for _ in range(COLS)]
            new_tab.append(row)
        self.tableau = new_tab
        self.stock = cards
        self.redeals += 1
        return True

    def stuck(self):
        return not self.find_pairs() and not self.stock and self.redeals >= self.MAX_REDEALS


def render(g):
    print("    " + " ".join(f"{c + 1:>3}" for c in range(COLS)))
    for r in range(ROWS):
        row = " ".join(f"{card_name(g.tableau[r][c]):>3}" if g.tableau[r][c] else "  ·"
                       for c in range(COLS))
        print(f" {chr(65 + r)}  {row}")
    print(f"牌堆剩: {len(g.stock)}  已移除: {g.removed}/52")


def parse_pos(text):
    text = text.strip().upper()
    if len(text) < 2 or not text[0].isalpha() or not text[1:].isdigit():
        raise ValueError(f"坐标无效: {text}")
    r, c = ord(text[0]) - 65, int(text[1:]) - 1
    if not (0 <= r < ROWS and 0 <= c < COLS):
        raise ValueError(f"坐标越界: {text}")
    return (r, c)


def play_interactive(seed):
    if not sys.stdin.isatty():
        print("error: 交互模式需要终端, 管道场景请用 --auto", file=sys.stderr)
        return 2
    g = Game(seed)
    while True:
        render(g)
        if g.won():
            print("🎉 全部移除! 你赢了!")
            return 0
        if not g.find_pairs():
            if g.redeal():
                print(f"无对子可走, 重发牌桌 (第 {g.redeals} 次)。")
                continue
            print(f"无牌可走, 剩余 {52 - g.removed} 张。游戏结束。")
            return 0
        try:
            text = input("选两张 (如 A1 B2, q 退出): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            return 0
        if text.lower() == "q":
            print("已退出。")
            return 0
        parts = text.split()
        if len(parts) != 2:
            print("请输入两个坐标, 如 A1 B2。")
            continue
        try:
            p1, p2 = parse_pos(parts[0]), parse_pos(parts[1])
        except ValueError as e:
            print(e)
            continue
        a, b = g.tableau[p1[0]][p1[1]], g.tableau[p2[0]][p2[1]]
        if a is not None and b is not None and g.remove_pair(p1, p2):
            print(f"移除 {card_name(a)} + {card_name(b)}。")
        else:
            print("不能移除: 必须相邻且同点数。")


def play_auto(seed, verbose=False):
    g = Game(seed)
    moves = 0
    while True:
        if g.won():
            if verbose:
                print(f"自动游玩结束: 胜利, {moves} 步, 重发 {g.redeals} 次。")
            return True, moves
        pairs = g.find_pairs()
        if not pairs:
            if g.redeal():
                continue
            if verbose:
                print(f"自动游玩结束: 失败, 移除 {g.removed}/52, {moves} 步。")
            return False, moves
        p1, p2 = pairs[0]
        assert g.remove_pair(p1, p2), "auto bot 只走合法对子"
        moves += 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="蒙特卡洛纸牌接龙: 移除相邻同点数对子")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--auto", action="store_true", help="自动游玩(贪心机器人)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    if args.auto:
        won, moves = play_auto(args.seed, verbose=True)
        return 0
    return play_interactive(args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
