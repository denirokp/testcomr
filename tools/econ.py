#!/usr/bin/env python3
"""Расчётная модель юнит-экономики и 90-дневного прогноза.

Все входные величины — ГИПОТЕЗЫ до получения смет типографий (задача O-1)
и первых замеров человеко-минут в треке B. Меняй ASSUMPTIONS и перезапускай.

    python3 tools/econ.py
"""

from dataclasses import dataclass, replace

# ─────────────────────────────────────────────────────────────────────────────
# ДОПУЩЕНИЯ (гипотезы)
# ─────────────────────────────────────────────────────────────────────────────

EDITOR_RATE_HOUR = 700      # ₽/час: наёмный редактор ИЛИ альтернативная
                            # стоимость часа владельца. Ноль здесь — самообман.

@dataclass(frozen=True)
class Costs:
    print_single: int = 1500     # твёрдый переплёт, 24–28 стр., 1 экз.
    shipping: int = 400          # СДЭК/Почта по РФ, средневзвешенно
    packaging: int = 120         # коробка, наполнитель, открытка
    generation: int = 350        # изображения с перегенерациями + текст
    editorial_min_pre: int = 100 # минуты редактора ДО превью
    editorial_min_post: int = 35 # минуты редактора ПОСЛЕ оплаты
    defect_rate: float = 0.07    # брак и допечатка, доля от печати+доставки
    acquiring: float = 0.03      # эквайринг
    service_per_order: int = 150 # инфраструктура, инструменты на заказ
    tax_rate: float = 0.06       # УСН «доходы»


@dataclass(frozen=True)
class Product:
    key: str
    name: str
    price: int


PRODUCTS = [
    Product("pet",       "Питомец",            7900),
    Product("child",     "Ребёнок",            8900),
    Product("child_pet", "Ребёнок + питомец", 11900),
]

# Допродажи. Ключевое: превью и редактура уже оплачены основным заказом,
# поэтому предельная себестоимость допродажи — почти только производство.
UPSELLS = [
    ("Второй экземпляр (бабушке)", 3900, "print"),
    ("Подарочная упаковка",         900, "flat300"),
]

MIX = {"pet": 0.30, "child": 0.40, "child_pet": 0.30}

# Воронка
CONV_VISIT_LEAD = 0.03     # посетитель лендинга → заявка
CONV_LEAD_INTAKE = 0.60    # заявка → завершённый интейк
CONV_INTAKE_PREVIEW = 0.95 # интейк → собранное превью
# превью → оплата задаётся сценарием

FIXED_MONTHLY = 15000      # инфра, связь, инструменты, мелочь. Без рекламы и ФОТ.


# ─────────────────────────────────────────────────────────────────────────────
# РАСЧЁТ
# ─────────────────────────────────────────────────────────────────────────────

def editorial_pre(c: Costs) -> float:
    return c.editorial_min_pre / 60 * EDITOR_RATE_HOUR


def editorial_post(c: Costs) -> float:
    return c.editorial_min_post / 60 * EDITOR_RATE_HOUR


def cost_per_preview(c: Costs) -> float:
    """Тратится на КАЖДОЕ превью, включая неоплаченные (правило 7)."""
    return c.generation + editorial_pre(c)


def cost_after_payment(p: Product, c: Costs) -> float:
    defect = (c.print_single + c.shipping) * c.defect_rate
    return (c.print_single + c.shipping + c.packaging + defect
            + editorial_post(c) + p.price * c.acquiring + c.service_per_order)


def contribution(p: Product, c: Costs, conv_paid: float) -> dict:
    pre_effective = cost_per_preview(c) / conv_paid
    post = cost_after_payment(p, c)
    total = pre_effective + post
    contrib = p.price - total
    return {
        "price": p.price,
        "pre_effective": pre_effective,
        "post": post,
        "total": total,
        "contribution": contrib,
        "margin": contrib / p.price,
    }


def blended_contribution(c: Costs, conv_paid: float) -> float:
    return sum(contribution(p, c, conv_paid)["contribution"] * MIX[p.key]
               for p in PRODUCTS)


def blended_price(c: Costs) -> float:
    return sum(p.price * MIX[p.key] for p in PRODUCTS)


def breakeven_books(c: Costs, conv_paid: float, cac: float) -> float:
    """Сколько книг в месяц покрывает денежные постоянные расходы."""
    per_book = blended_contribution(c, conv_paid) - cac
    if per_book <= 0:
        return float("inf")
    return FIXED_MONTHLY / per_book


# ─────────────────────────────────────────────────────────────────────────────
# ВЫВОД
# ─────────────────────────────────────────────────────────────────────────────

def money(x) -> str:
    return f"{round(x):,}".replace(",", " ")


def section(title):
    print(f"\n{'═' * 78}\n{title}\n{'═' * 78}")


def show_costs(c: Costs):
    section("1. СЕБЕСТОИМОСТЬ ОДНОЙ КНИГИ (гипотезы)")
    print(f"  Печать, 1 экз.                {money(c.print_single):>8} ₽")
    print(f"  Доставка                      {money(c.shipping):>8} ₽")
    print(f"  Упаковка                      {money(c.packaging):>8} ₽")
    print(f"  Генерация (текст+картинки)    {money(c.generation):>8} ₽")
    print(f"  Редактура ДО превью ({c.editorial_min_pre} мин)  {money(editorial_pre(c)):>8} ₽")
    print(f"  Редактура ПОСЛЕ ({c.editorial_min_post} мин)      {money(editorial_post(c)):>8} ₽")
    print(f"  Брак/допечатка {c.defect_rate:.0%}             {money((c.print_single+c.shipping)*c.defect_rate):>8} ₽")
    print(f"  Сервис на заказ               {money(c.service_per_order):>8} ₽")
    print(f"  Эквайринг                     {c.acquiring:>7.0%}")
    print(f"\n  Ставка редактора: {EDITOR_RATE_HOUR} ₽/час. "
          f"Итого {c.editorial_min_pre + c.editorial_min_post} мин = "
          f"{money(editorial_pre(c)+editorial_post(c))} ₽ на книгу.")


def show_products(c: Costs, conv_paid: float):
    section(f"2. ВКЛАД НА ПОКРЫТИЕ (конверсия превью→оплата = {conv_paid:.0%})")
    print(f"  {'Продукт':<18}{'Цена':>8}{'До превью*':>12}{'После':>10}"
          f"{'Вклад':>10}{'Маржа':>8}")
    for p in PRODUCTS:
        r = contribution(p, c, conv_paid)
        print(f"  {p.name:<18}{money(r['price']):>8}{money(r['pre_effective']):>12}"
              f"{money(r['post']):>10}{money(r['contribution']):>10}"
              f"{r['margin']:>7.0%}")
    print(f"\n  * «До превью» — стоимость превью, делённая на конверсию: мы платим")
    print(f"    и за те превью, которые не купили (правило 7).")
    print(f"\n  Средневзвешенный вклад при миксе "
          f"{'/'.join(f'{int(v*100)}%' for v in MIX.values())}: "
          f"{money(blended_contribution(c, conv_paid))} ₽")


def show_sensitivity(c: Costs):
    section("3. ЧУВСТВИТЕЛЬНОСТЬ: конверсия превью→оплата × CAC")
    convs = [0.35, 0.45, 0.55, 0.65, 0.75]
    cacs = [500, 1000, 1500, 2000, 2500]
    print("  Чистый вклад с книги после CAC и налога, ₽\n")
    header = "CAC / конв."
    print(f"  {header:<14}" + "".join(f"{c_:>10.0%}" for c_ in convs))
    for cac in cacs:
        row = f"  {money(cac) + ' ₽':<14}"
        for cv in convs:
            val = (blended_contribution(c, cv) - cac
                   - blended_price(c) * c.tax_rate)
            row += f"{money(val):>10}"
        print(row)
    print("\n  Отрицательное значение = каждый следующий заказ увеличивает убыток.")


def show_breakeven(c: Costs):
    section("4. ТОЧКА БЕЗУБЫТОЧНОСТИ")
    print(f"  Денежные постоянные расходы: {money(FIXED_MONTHLY)} ₽/мес")
    print(f"  (без рекламы и без ФОТ владельца)\n")
    print(f"  {'CAC':<12}{'конв. 45%':>14}{'конв. 55%':>14}{'конв. 65%':>14}")
    for cac in (500, 1000, 1500, 2000, 2500):
        row = f"  {money(cac)+' ₽':<12}"
        for cv in (0.45, 0.55, 0.65):
            be = breakeven_books(c, cv, cac)
            row += f"{'не достигается' if be == float('inf') else str(round(be,1))+' кн.':>14}"
        print(row)


SCENARIOS = {
    "Пессимистичный": dict(conv=0.40, vol=(3, 6, 9), cac=2200),
    "Базовый":        dict(conv=0.55, vol=(5, 15, 25), cac=1500),
    "Оптимистичный":  dict(conv=0.65, vol=(8, 28, 54), cac=900),
}


def show_forecast(c: Costs):
    section("5. ПРОГНОЗ НА 90 ДНЕЙ (август–октябрь)")
    for name, s in SCENARIOS.items():
        conv, vols, cac = s["conv"], s["vol"], s["cac"]
        contrib = blended_contribution(c, conv)
        avg_price = blended_price(c)
        total_paid = sum(vols)
        print(f"\n  ── {name} "
              f"(конверсия превью→оплата {conv:.0%}, CAC {money(cac)} ₽) "
              f"{'─' * (28 - len(name))}")
        print(f"  {'Месяц':<8}{'Опл.':>7}{'Превью':>8}{'Заявки':>8}{'Трафик':>9}"
              f"{'Выручка':>11}{'Вклад':>10}{'Реклама':>10}{'Итог':>10}")
        cum = 0
        for i, paid in enumerate(vols, 1):
            previews = paid / conv
            leads = previews / (CONV_LEAD_INTAKE * CONV_INTAKE_PREVIEW)
            visits = leads / CONV_VISIT_LEAD
            revenue = paid * avg_price
            gross = paid * contrib
            ads = paid * cac
            net = gross - ads - FIXED_MONTHLY - revenue * c.tax_rate
            cum += net
            print(f"  {'М'+str(i):<8}{paid:>7}{round(previews):>8}{round(leads):>8}"
                  f"{round(visits):>9}{money(revenue):>11}{money(gross):>10}"
                  f"{money(ads):>10}{money(net):>10}")
        total_rev = total_paid * avg_price
        total_gross = total_paid * contrib
        print(f"  {'ИТОГО':<8}{total_paid:>7}{'':>8}{'':>8}{'':>9}"
              f"{money(total_rev):>11}{money(total_gross):>10}"
              f"{money(total_paid*cac):>10}{money(cum):>10}")
        hours = total_paid * (c.editorial_min_pre / conv + c.editorial_min_post) / 60
        print(f"  Человеко-часов производства за 90 дней: {round(hours)} ч "
              f"(~{round(hours/3/21, 1)} ч в рабочий день)")


def show_allowable_cac(c: Costs):
    section("6. ДОПУСТИМЫЙ CAC")
    for cv in (0.45, 0.55, 0.65):
        contrib = blended_contribution(c, cv)
        tax = blended_price(c) * c.tax_rate
        breakeven_cac = contrib - tax
        target_cac = breakeven_cac * 0.5   # половина вклада — на прибыль и постоянные
        print(f"  Конверсия {cv:.0%}: вклад {money(contrib)} ₽, "
              f"CAC безубыточности {money(breakeven_cac)} ₽, "
              f"целевой CAC ≤ {money(target_cac)} ₽")


def price_floor(c: Costs, conv_paid: float, target_contribution: float) -> float:
    """Минимальная цена, дающая заданный вклад. Ключ к вопросу «а если дешевле»."""
    fixed_post = (c.print_single + c.shipping + c.packaging
                  + (c.print_single + c.shipping) * c.defect_rate
                  + editorial_post(c) + c.service_per_order)
    pre_eff = cost_per_preview(c) / conv_paid
    return (target_contribution + pre_eff + fixed_post) / (1 - c.acquiring)


def show_price_floor(c: Costs):
    section("10. ЦЕНОВОЙ ПОЛ — можем ли мы вообще быть дешевле")
    print("  Минимальная цена при заданном вкладе, ₽\n")
    print(f"  {'Вклад':<16}{'конв. 45%':>13}{'конв. 55%':>13}{'конв. 65%':>13}")
    for target in (0, 1500, 3000, 4000):
        label = "0 (в ноль)" if target == 0 else money(target) + " ₽"
        row = f"  {label:<16}"
        for cv in (0.45, 0.55, 0.65):
            row += f"{money(price_floor(c, cv, target)):>13}"
        print(row)
    floor = price_floor(c, 0.55, 0)
    print(f"\n  Продавать дешевле {money(floor)} ₽ при нашей структуре затрат")
    print(f"  означает терять деньги на каждом заказе.")
    print(f"  Рыночный диапазон РФ (2026): 990–7 000 ₽ — см. docs/business/market-research.md")
    print(f"  Вывод: массовый тир нам структурно недоступен. Только премиум.")


def show_upsells(c: Costs):
    section("8. ДОПРОДАЖИ (вклад почти чистый — превью уже оплачено)")
    for name, price, kind in UPSELLS:
        if kind == "print":
            cost = (c.print_single + c.packaging
                    + c.print_single * c.defect_rate + price * c.acquiring)
        else:
            cost = 300 + price * c.acquiring
        print(f"  {name:<30}{money(price):>8} ₽   себест. {money(cost):>6} ₽   "
              f"вклад {money(price-cost):>6} ₽  ({(price-cost)/price:.0%})")
    print("\n  Второй экземпляр не требует ни интейка, ни редактуры, ни превью:")
    print("  он едет в той же посылке. Это самый дешёвый рост среднего чека.")
    take = 0.35   # гипотеза: доля заказов с допродажей
    extra = sum((p - (c.print_single + c.packaging + c.print_single*c.defect_rate
                      + p*c.acquiring) if k == "print" else p - 300 - p*c.acquiring)
                for _, p, k in UPSELLS) * take
    print(f"  При {take:.0%} проникновении обеих допродаж средний вклад растёт на "
          f"{money(extra)} ₽ с заказа (гипотеза).")


def show_capacity(c: Costs):
    section("9. ПРОПУСКНАЯ СПОСОБНОСТЬ")
    for conv in (0.55,):
        mins = c.editorial_min_pre / conv + c.editorial_min_post
        print(f"  При конверсии {conv:.0%} на одну ОПЛАЧЕННУЮ книгу уходит "
              f"{round(mins)} мин редактора\n  (включая работу над непроданными превью).\n")
        for hours in (20, 40, 80, 120):
            print(f"  {hours:>4} ч производства в месяц  →  "
                  f"{int(hours*60/mins):>3} книг/мес  →  выручка "
                  f"{money(int(hours*60/mins)*blended_price(c)):>9} ₽")
    print("\n  120 ч/мес — это фактически полная занятость одного человека")
    print("  ТОЛЬКО производством, без продаж, закупки рекламы и общения с клиентом.")
    print("  Реальный потолок соло: 20–25 книг/мес.")


def show_levers(c: Costs):
    section("7. РЫЧАГИ: что меняет экономику сильнее всего")
    base = blended_contribution(c, 0.55)
    variants = [
        ("Базовый сценарий", c, 0.55),
        ("Редактура 60 мин вместо 135", replace(c, editorial_min_pre=45, editorial_min_post=15), 0.55),
        ("Печать 1100 ₽ (партия 10+)", replace(c, print_single=1100), 0.55),
        ("Конверсия 65% вместо 55%", c, 0.65),
        ("Конверсия 40%", c, 0.40),
        ("Генерация вдвое дороже", replace(c, generation=700), 0.55),
    ]
    for name, cc, cv in variants:
        val = blended_contribution(cc, cv)
        delta = val - base
        sign = "+" if delta >= 0 else "−"
        print(f"  {name:<34}{money(val):>8} ₽   "
              f"{sign}{money(abs(delta)):>6} ₽")


def main():
    c = Costs()
    print("\nМОДЕЛЬ ЮНИТ-ЭКОНОМИКИ — все числа ГИПОТЕЗЫ до смет типографии")
    show_costs(c)
    show_products(c, 0.55)
    show_sensitivity(c)
    show_breakeven(c)
    show_allowable_cac(c)
    show_forecast(c)
    show_price_floor(c)
    show_upsells(c)
    show_capacity(c)
    show_levers(c)
    print()


if __name__ == "__main__":
    main()
