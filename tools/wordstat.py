#!/usr/bin/env python3
"""Разбор данных Wordstat: объём спроса, сезонность, перевод в заказы.

Заполни data/wordstat.csv и data/wordstat_seasonality.csv по протоколу
forms/05-wordstat-collection.md, затем:

    python3 tools/wordstat.py

Скрипт отвечает не на вопрос «сколько людей ищут», а на вопрос
«сколько книг мы можем продать» — через воронку из tools/econ.py.
"""

import csv
import pathlib

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"

# Воронка — та же, что в tools/econ.py
CTR_ADS = 0.06           # доля показов, которые мы выкупим и получим клик (гипотеза)
CONV_VISIT_LEAD = 0.03
CONV_LEAD_INTAKE = 0.60
CONV_INTAKE_PREVIEW = 0.95
CONV_PREVIEW_PAID = 0.55
AVG_PRICE = 9500         # средневзвешенный чек, ₽

CLUSTERS = {
    "A": "Прямой спрос на продукт",
    "B": "Питомцы",
    "C": "Подарочный интент",
    "D": "Бренды конкурентов",
    "E": "Смежный бенчмарк",
}


def money(x):
    return f"{round(x):,}".replace(",", " ")


def load_queries():
    path = DATA / "wordstat.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [
            {**r, "broad": int(r["broad"] or 0),
             "phrase": int(r["phrase"] or 0), "exact": int(r["exact"] or 0)}
            for r in csv.DictReader(f)
        ]


def load_seasonality():
    path = DATA / "wordstat_seasonality.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        rows = []
        for r in csv.DictReader(f):
            rows.append({
                "month": r["month"],
                "kniga": int(r["imennaya_kniga"] or 0),
                "podarok": int(r["podarok_rebenku"] or 0),
            })
        return rows


def section(t):
    print(f"\n{'═' * 76}\n{t}\n{'═' * 76}")


def report_volume(rows):
    section("1. ОБЪЁМ СПРОСА ПО КЛАСТЕРАМ")
    print(f"  {'Кластер':<28}{'Базовая':>11}{'Фразовая':>11}{'Точная':>10}"
          f"{'Точн./Баз.':>12}")
    totals = {}
    for key, name in CLUSTERS.items():
        sub = [r for r in rows if r["cluster"] == key]
        b = sum(r["broad"] for r in sub)
        p = sum(r["phrase"] for r in sub)
        e = sum(r["exact"] for r in sub)
        totals[key] = {"broad": b, "phrase": p, "exact": e}
        ratio = f"{e / b:.0%}" if b else "—"
        print(f"  {name:<28}{money(b):>11}{money(p):>11}{money(e):>10}{ratio:>12}")
    return totals


def report_quality(rows, totals):
    section("2. КАЧЕСТВО СПРОСА")
    a = totals.get("A", {})
    if a.get("broad"):
        r = a["exact"] / a["broad"]
        print(f"  Доля точной частотности в базовой по кластеру A: {r:.0%}")
        if r < 0.05:
            print("  → Ниже 5%: базовая частотность почти целиком информационный шум.")
            print("    Планировать по базовой нельзя — рынок окажется втрое меньше.")
        elif r < 0.15:
            print("  → 5–15%: обычная картина для подарочной ниши.")
        else:
            print("  → Выше 15%: непривычно чистый спрос, перепроверь операторы.")

    dog = next((r for r in rows if r["query"] == "книга про собаку"), None)
    portrait = next((r for r in rows if r["query"] == "портрет питомца на заказ"), None)
    if dog and dog["broad"]:
        r = dog["exact"] / dog["broad"]
        print(f"\n  «книга про собаку»: точная/базовая = {r:.0%}")
        if r < 0.03:
            print("  → Подтверждает гипотезу: это запрос про массовые издания,")
            print("    а не про персональный подарок. В расчёт объёма не берём.")
    if portrait:
        print(f"\n  «портрет питомца на заказ», точная: {money(portrait['exact'])}")
        print("  → Главный индикатор кластера B: та же аудитория, чек и повод.")

    d = totals.get("D", {})
    e_ = totals.get("E", {})
    if d.get("exact"):
        print(f"\n  Брендовый спрос конкурентов (точная): {money(d['exact'])}/мес")
        print("  → Прямая мера того, насколько велики те, с кем нас сравнят.")
        if a.get("exact"):
            print(f"    Отношение к прямому спросу: {d['exact'] / a['exact']:.0%}")
    if e_.get("exact") and a.get("exact"):
        print(f"\n  Наша ниша меньше зрелой категории «фотокнига» "
              f"в {e_['exact'] / a['exact']:.1f} раза")


def report_funnel(totals):
    section("3. ИЗ ЗАПРОСОВ В ЗАКАЗЫ")
    base = totals.get("A", {}).get("exact", 0) + totals.get("B", {}).get("exact", 0)
    if not base:
        print("  Данные не заполнены — заполни data/wordstat.csv.")
        return
    print(f"  Целевой спрос (кластеры A + B, точная частотность): "
          f"{money(base)} показов/мес\n")
    print(f"  {'Доля рынка, которую выкупаем':<32}{'Визиты':>9}{'Заявки':>9}"
          f"{'Превью':>9}{'Оплаты':>9}{'Выручка':>12}")
    for share in (0.05, 0.10, 0.20, 0.35):
        visits = base * share * CTR_ADS
        leads = visits * CONV_VISIT_LEAD
        previews = leads * CONV_LEAD_INTAKE * CONV_INTAKE_PREVIEW
        paid = previews * CONV_PREVIEW_PAID
        print(f"  {share:>6.0%} показов кластера{'':<12}{round(visits):>9}"
              f"{round(leads):>9}{round(previews):>9}{round(paid):>9}"
              f"{money(paid * AVG_PRICE):>12}")
    print(f"\n  CTR по объявлению принят {CTR_ADS:.0%} — гипотеза, уточнить первой кампанией.")

    best = base * 0.35 * CTR_ADS * CONV_VISIT_LEAD * CONV_LEAD_INTAKE \
        * CONV_INTAKE_PREVIEW * CONV_PREVIEW_PAID
    print("\n  ИНТЕРПРЕТАЦИЯ")
    if best < 3:
        print(f"  Даже выкупив 35% всех целевых показов, поиск даёт {best:.1f} заказа/мес.")
        print("  → Поиск в этой нише НЕ КАНАЛ. Прямого спроса слишком мало.")
        print("    Продукт надо не искать, а показывать: блогеры, партнёрства,")
        print("    соцсети. Контекст годится только для добора тёплого трафика")
        print("    и защиты бренда, а не как источник объёма.")
    elif best < 20:
        print(f"  При 35% выкупа поиск даёт {best:.0f} заказов/мес — это добавка,")
        print("    но не основа. Основной объём всё равно из посевов и партнёрств.")
    else:
        print(f"  При 35% выкупа поиск даёт {best:.0f} заказов/мес.")
        print("  → Поиск самодостаточен; сравни с потолком производства 20–25 книг/мес.")
        print("    Если выше потолка — ограничитель мы, а не рынок, и приоритет")
        print("    уходит в автоматизацию (docs/tech/automation-roadmap.md).")


def report_seasonality(rows):
    section("4. СЕЗОННОСТЬ")
    filled = [r for r in rows if r["kniga"] or r["podarok"]]
    if len(filled) < 12:
        print("  Данных меньше 12 месяцев — заполни data/wordstat_seasonality.csv.")
        return
    avg_k = sum(r["kniga"] for r in filled) / len(filled)
    avg_p = sum(r["podarok"] for r in filled) / len(filled)
    print(f"  {'Месяц':<10}{'именная книга':>15}{'индекс':>9}"
          f"{'подарок ребёнку':>18}{'индекс':>9}{'разрыв':>9}")
    for r in filled:
        ik = r["kniga"] / avg_k if avg_k else 0
        ip = r["podarok"] / avg_p if avg_p else 0
        gap = ik - ip
        mark = "  ←" if ik > 1.5 else ""
        print(f"  {r['month']:<10}{money(r['kniga']):>15}{ik:>9.2f}"
              f"{money(r['podarok']):>18}{ip:>9.2f}{gap:>+9.2f}{mark}")

    peak = max(filled, key=lambda r: r["kniga"])
    trough = min(filled, key=lambda r: r["kniga"])
    line = f"\n  Пик: {peak['month']} ({money(peak['kniga'])}), дно: {trough['month']}"
    if trough["kniga"]:
        line += f" ({money(trough['kniga'])}), размах {peak['kniga'] / trough['kniga']:.1f}x"
    print(line)
    print("\n  Колонка «разрыв» — есть ли у ниши СВОЯ сезонность.")
    print("  Около нуля — мы просто повторяем общий подарочный цикл.")
    print("  Устойчиво положительный в отдельные месяцы — там наш собственный повод,")
    print("  и его стоит отрабатывать отдельной кампанией.")


def main():
    rows = load_queries()
    if not rows:
        print("Нет data/wordstat.csv. См. forms/05-wordstat-collection.md")
        return
    if not any(r["exact"] or r["broad"] for r in rows):
        print("\n⚠ Файл data/wordstat.csv заполнен нулями — это шаблон.")
        print("  Протокол сбора: forms/05-wordstat-collection.md (10 минут).")
        print("  Ниже структура отчёта, который получится после заполнения.\n")
    totals = report_volume(rows)
    report_quality(rows, totals)
    report_funnel(totals)
    report_seasonality(load_seasonality())
    print()


if __name__ == "__main__":
    main()
