#!/usr/bin/env python3
"""Генератор датасета сделок для задания «Дашборд аналитики по сделкам».

Запуск:
    python3 data/seed.py

Создаёт рядом с собой trades.csv (100 000 строк). Генерация детерминирована:
при одном и том же SEED файл получается побайтово одинаковым.

ВАЖНО: этот файл и полученный trades.csv — входные данные задания.
Их нельзя править.
"""

from __future__ import annotations

import csv
import math
import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROWS = 100_000
SEED = 20260831
OUT = Path(__file__).parent / "trades.csv"

UTC = timezone.utc
PERIOD_START = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
PERIOD_END = datetime(2025, 12, 31, 23, 59, 59, tzinfo=UTC)

# Остановка торговли на время миграции инфраструктуры.
GAP_START = datetime(2024, 7, 1, 0, 0, 0, tzinfo=UTC)
GAP_END = datetime(2024, 7, 15, 0, 0, 0, tzinfo=UTC)

# Алматы — UTC+5 круглый год, без переходов на летнее время.
ALMATY_OFFSET = timedelta(hours=5)

CENT = Decimal("0.01")
FEE_RATE = Decimal("0.0005")
BREAKEVEN_PROB = 0.01

# symbol -> (базовая цена, шаг цены, шаг количества)
SYMBOLS: dict[str, tuple[Decimal, Decimal, Decimal]] = {
    "BTCUSDT": (Decimal("62000"), Decimal("0.01"), Decimal("0.001")),
    "ETHUSDT": (Decimal("3100"), Decimal("0.01"), Decimal("0.01")),
    "SOLUSDT": (Decimal("145"), Decimal("0.01"), Decimal("0.1")),
    "LINKUSDT": (Decimal("14.5"), Decimal("0.001"), Decimal("1")),
    "AVAXUSDT": (Decimal("27.0"), Decimal("0.001"), Decimal("1")),
    "XRPUSDT": (Decimal("0.52"), Decimal("0.0001"), Decimal("10")),
    "ADAUSDT": (Decimal("0.38"), Decimal("0.0001"), Decimal("10")),
    "DOGEUSDT": (Decimal("0.13"), Decimal("0.00001"), Decimal("100")),
}

# Не каждая стратегия торгует каждый инструмент — как в жизни.
STRATEGY_SYMBOLS: dict[str, list[str]] = {
    "momentum_v1": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "LINKUSDT"],
    "mean_rev_v2": ["BTCUSDT", "ETHUSDT", "XRPUSDT", "ADAUSDT"],
    "breakout_v1": ["ETHUSDT", "SOLUSDT", "LINKUSDT", "AVAXUSDT"],
    "grid_v2": ["ADAUSDT", "DOGEUSDT"],
    "carry_v1": ["BTCUSDT", "AVAXUSDT", "XRPUSDT"],
}

STRATEGY_WEIGHTS = {
    "momentum_v1": 30,
    "mean_rev_v2": 25,
    "breakout_v1": 20,
    "grid_v2": 15,
    "carry_v1": 10,
}

# Ожидаемое движение цены на сделку: (среднее, сигма). Разные стратегии —
# разное качество, чтобы дашборд имел смысл.
STRATEGY_EDGE: dict[str, tuple[float, float]] = {
    "momentum_v1": (0.0022, 0.018),
    "mean_rev_v2": (0.0009, 0.011),
    "breakout_v1": (0.0014, 0.026),
    "grid_v2": (0.0004, 0.005),
    "carry_v1": (-0.0006, 0.009),
}

# Комбинации (инструмент, стратегия, календарные сутки), которые генератор
# не занимает: сделки за эти сутки заданы вручную в fixed_trades().
# Сутки здесь локальные, как и везде в проекте.
RESERVED: dict[tuple[str, str], set[date]] = {
    ("ADAUSDT", "grid_v2"): {date(2024, 6, 20)},
    ("SOLUSDT", "momentum_v1"): {date(2024, 9, 11)},
    ("XRPUSDT", "mean_rev_v2"): {date(2025, 4, 2)},
    ("AVAXUSDT", "carry_v1"): {
        date(2024, 3, 9),
        date(2024, 3, 10),
        date(2024, 3, 11),
        date(2024, 3, 12),
        date(2024, 3, 13),
    },
}

FIELDNAMES = [
    "id",
    "symbol",
    "strategy",
    "side",
    "opened_at",
    "closed_at",
    "qty",
    "entry_price",
    "exit_price",
    "fee",
    "pnl",
]


def quant(value: Decimal, step: Decimal) -> Decimal:
    return (value / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * step


def quant2(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def iso(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_trade(
    symbol: str,
    strategy: str,
    side: str,
    closed_at: datetime,
    entry: Decimal,
    exit_: Decimal,
    qty: Decimal,
    hold: timedelta,
) -> dict[str, str]:
    """Собирает одну строку. pnl всегда согласован с ценами, объёмом и комиссией."""
    direction = Decimal(1) if side == "long" else Decimal(-1)
    gross = (exit_ - entry) * qty * direction
    fee = quant2((entry * qty + exit_ * qty) * FEE_RATE)
    pnl = quant2(gross - fee)
    return {
        "id": "",  # проставляется после перемешивания
        "symbol": symbol,
        "strategy": strategy,
        "side": side,
        "opened_at": iso(closed_at - hold),
        "closed_at": iso(closed_at),
        "qty": str(qty),
        "entry_price": str(entry),
        "exit_price": str(exit_),
        "fee": f"{fee:.2f}",
        "pnl": f"{pnl:.2f}",
    }


def price_at(base: Decimal, tick: Decimal, moment: datetime, rnd: random.Random) -> Decimal:
    """Цена входа: медленный тренд по времени плюс шум."""
    days = (moment - PERIOD_START).total_seconds() / 86400
    trend = 1 + 0.18 * math.sin(days / 95) + 0.10 * math.sin(days / 310)
    noise = 1 + rnd.uniform(-0.06, 0.06)
    return quant(base * Decimal(str(trend * noise)), tick)


def local_date(moment: datetime) -> date:
    return (moment + ALMATY_OFFSET).date()


def is_reserved(symbol: str, strategy: str, closed_at: datetime) -> bool:
    days = RESERVED.get((symbol, strategy))
    return bool(days) and local_date(closed_at) in days


def random_trades(count: int, rnd: random.Random) -> list[dict[str, str]]:
    strategies = list(STRATEGY_WEIGHTS)
    weights = [STRATEGY_WEIGHTS[s] for s in strategies]
    span = int((PERIOD_END - PERIOD_START).total_seconds())
    out: list[dict[str, str]] = []

    while len(out) < count:
        strategy = rnd.choices(strategies, weights=weights, k=1)[0]
        symbol = rnd.choice(STRATEGY_SYMBOLS[strategy])
        closed_at = PERIOD_START + timedelta(seconds=rnd.randrange(span))
        if GAP_START <= closed_at < GAP_END or is_reserved(symbol, strategy, closed_at):
            continue

        base, tick, qty_step = SYMBOLS[symbol]
        entry = price_at(base, tick, closed_at, rnd)
        qty = qty_step * rnd.randint(1, 60)
        side = "long" if rnd.random() < 0.62 else "short"
        hold = timedelta(minutes=rnd.randint(5, 3 * 24 * 60))

        if rnd.random() < BREAKEVEN_PROB:
            # Выход в ноль: сделка закрыта по цене входа, комиссия отбита ребейтом.
            out.append(
                make_trade(symbol, strategy, side, closed_at, entry, entry, qty, hold)
                | {"fee": "0.00", "pnl": "0.00"}
            )
            continue

        mu, sigma = STRATEGY_EDGE[strategy]
        move = rnd.gauss(mu, sigma)
        direction = 1 if side == "long" else -1
        exit_ = quant(entry * Decimal(str(1 + move * direction)), tick)
        if exit_ <= 0:
            continue
        out.append(make_trade(symbol, strategy, side, closed_at, entry, exit_, qty, hold))

    return out


def fixed_trades() -> list[dict[str, str]]:
    """Сделки, заданные вручную, а не генератором."""
    trades: list[dict[str, str]] = []
    hold = timedelta(hours=3)

    # ADAUSDT / grid_v2, 2024-06-20.
    for hour in (9, 11, 14):
        trades.append(
            make_trade(
                "ADAUSDT",
                "grid_v2",
                "long",
                datetime(2024, 6, 20, hour, 0, 0, tzinfo=UTC),
                Decimal("0.3800"),
                Decimal("0.3900"),
                Decimal("10"),
                hold,
            )
        )

    # SOLUSDT / momentum_v1, 2024-09-11.
    for hour, exit_price in ((8, "147.00"), (10, "146.50"), (12, "148.20"), (15, "149.00"), (17, "146.10")):
        trades.append(
            make_trade(
                "SOLUSDT",
                "momentum_v1",
                "long",
                datetime(2024, 9, 11, hour, 0, 0, tzinfo=UTC),
                Decimal("145.00"),
                Decimal(exit_price),
                Decimal("2.0"),
                hold,
            )
        )

    # XRPUSDT / mean_rev_v2, 2025-04-02.
    for hour, exit_price in ((6, "0.5100"), (8, "0.5050"), (10, "0.5120"), (12, "0.4980"),
                             (14, "0.5090"), (16, "0.5020"), (18, "0.5110")):
        trades.append(
            make_trade(
                "XRPUSDT",
                "mean_rev_v2",
                "long",
                datetime(2025, 4, 2, hour, 0, 0, tzinfo=UTC),
                Decimal("0.5200"),
                Decimal(exit_price),
                Decimal("100"),
                hold,
            )
        )

    # AVAXUSDT / carry_v1, два пакета заявок вечером 2024-03-10 по UTC.
    for index in range(40):
        exit_price = Decimal("27.500") if index % 2 == 0 else Decimal("26.400")
        trades.append(
            make_trade(
                "AVAXUSDT",
                "carry_v1",
                "long",
                datetime(2024, 3, 10, 18, 59, 59, tzinfo=UTC),
                Decimal("27.000"),
                exit_price,
                Decimal("3"),
                hold,
            )
        )
    for index in range(40):
        exit_price = Decimal("27.900") if index % 2 == 0 else Decimal("26.100")
        trades.append(
            make_trade(
                "AVAXUSDT",
                "carry_v1",
                "long",
                datetime(2024, 3, 10, 19, 0, 0, tzinfo=UTC),
                Decimal("27.000"),
                exit_price,
                Decimal("4"),
                hold,
            )
        )

    # LINKUSDT / breakout_v1: пакет позиций, закрытых одной заявкой.
    rnd = random.Random(777)
    for _ in range(137):
        move = rnd.choice([Decimal("0.250"), Decimal("-0.180"), Decimal("0.420"), Decimal("-0.310")])
        trades.append(
            make_trade(
                "LINKUSDT",
                "breakout_v1",
                "long" if rnd.random() < 0.5 else "short",
                datetime(2025, 2, 3, 12, 0, 0, tzinfo=UTC),
                Decimal("14.500"),
                Decimal("14.500") + move,
                Decimal(str(rnd.randint(1, 40))),
                hold,
            )
        )

    return trades


def main() -> None:
    rnd = random.Random(SEED)
    fixed = fixed_trades()
    rows = random_trades(ROWS - len(fixed), rnd) + fixed

    # Порядок строк в файле произвольный.
    rnd.shuffle(rows)
    for index, row in enumerate(rows, start=1):
        row["id"] = str(index)

    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{OUT}: {len(rows)} строк")


if __name__ == "__main__":
    main()
