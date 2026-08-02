#!/usr/bin/env python3
"""Сравнение рынков: юнит-экономика одной книги в разных странах.

ВСЕ параметры — гипотезы. Курсы, цены печати и ставки редакторов не подтверждены
сметами. Модель нужна не чтобы узнать ответ, а чтобы понять, от чего он зависит.

Всё считается в USD для сопоставимости.

    python3 tools/geo.py
"""

from dataclasses import dataclass

# Курсы к доллару, гипотезы на август 2026
FX = {"RUB": 95, "NGN": 1600, "EGP": 50, "KZT": 520, "AED": 3.67, "USD": 1}


@dataclass(frozen=True)
class Market:
    name: str
    currency: str
    price_usd: float          # цена продукта, USD
    print_usd: float          # печать 1 экз., твёрдый переплёт
    ship_usd: float
    editor_rate_hour: float   # ставка редактора, ВЛАДЕЮЩЕГО языком рынка
    generation_usd: float
    conv_preview_paid: float  # превью → оплата
    cac_usd: float
    # качественные факторы, 1 (плохо) … 5 (отлично)
    payments: int             # можем ли физически получить деньги
    legal: int                # выполнимость требований к детским данным
    language: int             # есть ли у нас редакционная культура языка
    logistics: int            # доставка и печать
    depth: int                # глубина платёжеспособного сегмента
    note: str


EDIT_MIN_PRE, EDIT_MIN_POST = 100, 35
PACK_SHARE, DEFECT, ACQ, SERVICE_SHARE = 0.08, 0.07, 0.03, 0.09


MARKETS = [
    Market("Россия", "RUB", 94, 15.8, 4.2, 7.4, 3.7, 0.55, 15.8,
           5, 3, 5, 4, 4, "база; юр. риск по 152-ФЗ высокий"),
    Market("Казахстан / СНГ", "KZT", 80, 18.0, 6.0, 6.0, 3.7, 0.50, 14.0,
           4, 4, 5, 3, 3, "тот же язык, редакцию не пересобирать"),
    Market("Нигерия", "NGN", 45, 12.0, 5.0, 4.0, 4.0, 0.45, 12.0,
           2, 3, 2, 2, 1, "рынок детских книг ~$9,9 млн целиком"),
    Market("Египет", "EGP", 50, 9.0, 4.0, 3.5, 4.0, 0.45, 10.0,
           2, 3, 1, 3, 1, "покупательная способность обвалилась"),
    Market("ОАЭ / Залив", "AED", 140, 22.0, 7.0, 15.0, 4.0, 0.55, 30.0,
           4, 4, 1, 5, 5, "высокий ARPU, но нужна арабская редакция"),
    Market("Диаспора RU в ЕС/США", "USD", 120, 25.0, 8.0, 7.4, 4.0, 0.55, 25.0,
           2, 3, 5, 4, 2, "наш язык, чужая юрисдикция и платежи"),
    # Варианты, которые модель подсказала сама
    Market("Залив + редакция Египта", "AED", 140, 22.0, 7.0, 5.0, 4.0, 0.55, 30.0,
           4, 4, 2, 5, 5, "продаём в Заливе, редактируем в Каире"),
    Market("Нигерия, премиум Лагос", "NGN", 90, 12.0, 5.0, 4.0, 4.0, 0.40, 25.0,
           2, 3, 2, 2, 1, "экономика сходится, сегмент почти пустой"),

    # «Наш язык, их доход» — русскоязычные общины в богатых странах.
    # Редакцию пересобирать НЕ надо: ставка редактора остаётся нашей.
    Market("ОАЭ, рус. сегмент", "USD", 140, 22.0, 7.0, 7.4, 4.0, 0.55, 28.0,
           4, 4, 5, 5, 3, "релоканты: молодые семьи, высокий доход"),
    Market("Израиль, рус. сегмент", "USD", 130, 28.0, 6.0, 7.4, 4.0, 0.55, 25.0,
           4, 4, 5, 4, 4, "1,1 млн русскоязычных, рождаемость 2,9 — выше всех в ОЭСР"),
    Market("США, рус. сегмент", "USD", 130, 26.0, 9.0, 7.4, 4.0, 0.50, 30.0,
           3, 4, 5, 4, 3, "~3 млн русскоязычных, дорогой трафик"),
    Market("Германия, рус. сегмент", "USD", 120, 24.0, 7.0, 7.4, 4.0, 0.50, 25.0,
           3, 4, 5, 4, 2, "3,7 млн, но община стареет — мало малышей"),

    # Локальные языки: редакцию надо строить с нуля
    Market("Польша", "USD", 85, 16.0, 5.0, 9.0, 4.0, 0.50, 18.0,
           3, 4, 1, 4, 3, "дешевле трафик, но нужен польский редактор"),
    Market("Великобритания", "USD", 110, 24.0, 7.0, 22.0, 4.0, 0.50, 45.0,
           3, 4, 1, 5, 5, "$438 на ребёнка в год — и родина Wonderbly"),
    Market("Южная Корея", "USD", 150, 20.0, 6.0, 20.0, 4.0, 0.50, 40.0,
           3, 3, 1, 5, 5, "культ трат на единственного ребёнка"),
]


def econ(m: Market) -> dict:
    edit_pre = EDIT_MIN_PRE / 60 * m.editor_rate_hour
    edit_post = EDIT_MIN_POST / 60 * m.editor_rate_hour
    pack = m.print_usd * PACK_SHARE
    service = m.price_usd * SERVICE_SHARE * 0.2
    pre_per_preview = m.generation_usd + edit_pre
    pre_effective = pre_per_preview / m.conv_preview_paid
    post = (m.print_usd + m.ship_usd + pack
            + (m.print_usd + m.ship_usd) * DEFECT
            + edit_post + m.price_usd * ACQ + service)
    contrib = m.price_usd - pre_effective - post
    floor = (pre_effective + post - m.price_usd * ACQ) / (1 - ACQ)
    return {
        "contrib": contrib,
        "margin": contrib / m.price_usd,
        "after_cac": contrib - m.cac_usd,
        "floor": floor,
        "price_local": m.price_usd * FX[m.currency],
        "floor_local": floor * FX[m.currency],
    }


def breakeven_rate(m: Market) -> float:
    """Ставка редактора, при которой вклад обнуляется."""
    pack = m.print_usd * PACK_SHARE
    service = m.price_usd * SERVICE_SHARE * 0.2
    fixed_post = (m.print_usd + m.ship_usd + pack
                  + (m.print_usd + m.ship_usd) * DEFECT + service)
    num = (m.price_usd * (1 - ACQ) - m.generation_usd / m.conv_preview_paid
           - fixed_post)
    den = EDIT_MIN_PRE / 60 / m.conv_preview_paid + EDIT_MIN_POST / 60
    return num / den


def readiness(m: Market) -> float:
    """Готовность рынка. Платежи и язык — с двойным весом: без них нет запуска."""
    return (m.payments * 2 + m.legal + m.language * 2 + m.logistics + m.depth) / 7


def bar(v: float, width: int = 5) -> str:
    full = round(v)
    return "█" * full + "·" * (width - full)


def money(x, cur="USD"):
    if cur == "USD":
        return f"${x:,.0f}"
    return f"{x:,.0f}".replace(",", " ")


def main():
    print("\nСРАВНЕНИЕ РЫНКОВ — все параметры ГИПОТЕЗЫ\n")

    print("1. ЮНИТ-ЭКОНОМИКА ОДНОЙ КНИГИ, USD")
    print("─" * 88)
    print(f"  {'Рынок':<24}{'Цена':>8}{'Вклад':>9}{'Маржа':>8}"
          f"{'После CAC':>11}{'Ценовой пол':>13}")
    for m in MARKETS:
        e = econ(m)
        print(f"  {m.name:<24}{money(m.price_usd):>8}{money(e['contrib']):>9}"
              f"{e['margin']:>7.0%}{money(e['after_cac']):>11}"
              f"{money(e['floor']):>13}")

    print("\n2. ТО ЖЕ В МЕСТНОЙ ВАЛЮТЕ")
    print("─" * 88)
    for m in MARKETS:
        e = econ(m)
        print(f"  {m.name:<24}цена {money(e['price_local'], m.currency):>10} {m.currency:<4}"
              f"   пол {money(e['floor_local'], m.currency):>10} {m.currency}")

    print("\n3. ГОТОВНОСТЬ РЫНКА (платежи и язык — двойной вес)")
    print("─" * 88)
    print(f"  {'Рынок':<24}{'Платежи':<8}{'Право':<8}{'Язык':<8}"
          f"{'Логист.':<9}{'Глубина':<9}{'Итог':>6}")
    for m in sorted(MARKETS, key=readiness, reverse=True):
        print(f"  {m.name:<24}{bar(m.payments):<8}{bar(m.legal):<8}"
              f"{bar(m.language):<8}{bar(m.logistics):<9}{bar(m.depth):<9}"
              f"{readiness(m):>6.1f}")

    print("\n4. ГЛАВНЫЙ ФИЛЬТР: сколько книг в месяц нужно, чтобы окупить")
    print("   создание иностранного юрлица (~$4 000 разово + $200/мес)")
    print("─" * 88)
    for m in MARKETS:
        e = econ(m)
        net = e["after_cac"]
        if net <= 0:
            print(f"  {m.name:<24}не окупается ни при каком объёме "
                  f"(вклад после CAC {money(net)})")
            continue
        months12 = (4000 + 200 * 12) / net / 12
        print(f"  {m.name:<24}{months12:>5.1f} книг/мес в течение года")

    print("\n5. ЧТО НА САМОМ ДЕЛЕ РЕШАЕТ: ставка редактора")
    print("─" * 88)
    print("  Предельная ставка — при которой вклад обнуляется.")
    print("  Рынок жив, пока редактор на языке покупателя дешевле этой суммы.\n")
    print(f"  {'Рынок':<24}{'Ставка':>9}{'Предел':>9}{'Запас':>9}"
          f"{'Доля редактуры в затратах':>28}")
    for m in sorted(MARKETS, key=lambda x: -(breakeven_rate(x) - x.editor_rate_hour)):
        br = breakeven_rate(m)
        e = econ(m)
        edit_cost = (EDIT_MIN_PRE / 60 / m.conv_preview_paid
                     + EDIT_MIN_POST / 60) * m.editor_rate_hour
        total_cost = m.price_usd - e["contrib"]
        share = edit_cost / total_cost if total_cost > 0 else 0
        gap = br - m.editor_rate_hour
        flag = "  ← убыточен" if gap < 0 else ""
        print(f"  {m.name:<24}{money(m.editor_rate_hour):>9}{money(br):>9}"
              f"{money(gap):>9}{share:>27.0%}{flag}")

    print("\n6. ЗАМЕТКИ")
    print("─" * 88)
    for m in MARKETS:
        print(f"  {m.name:<24}{m.note}")
    print()


if __name__ == "__main__":
    main()
