# Наша история — Personalized Story Engine

Платформа редакционно проверенных персональных историй, превращённых в физические книги
о тех, кого человек любит.

> Позиционирование: **«Персональная книга редакционного качества о том, кого вы любите».**
> Технология — на втором плане.

## Статус

| | |
|---|---|
| Этап | Исследование / подготовка pet-only concierge MVP |
| Кода | нет (осознанно — сначала домен, приватность и экономика) |
| Первый каталог | ребёнок, ребёнок + питомец, питомец |
| Первый запуск | **pet-only concierge** (ручной пайплайн, без детских фото) |
| Детский пилот | **трек B (качество) идёт первым**, 5 книг; трек A после него; трек C закрыт |

## Документы

| Файл | О чём |
|---|---|
| [docs/constitution.md](docs/constitution.md) | Высший приоритет. 16 правил продукта и порядок их изменения |
| [docs/strategy.md](docs/strategy.md) | Стратегия запуска: широкая архитектура — узкий первый запуск |
| [docs/child-pilot.md](docs/child-pilot.md) | Детский пилот: три трека, что открыто и что закрыто |
| [docs/track-b-runbook.md](docs/track-b-runbook.md) | Регламент прогона трека B: шаги, замеры, критерии, что делать при провале |
| [docs/intake.md](docs/intake.md) | Универсальная анкета интейка и карта «вопрос → домен» |
| [docs/story-architecture.md](docs/story-architecture.md) | Скелет арки, правило разрешения, якорный разворот, тест подмены имён |
| [docs/illustration-consistency.md](docs/illustration-consistency.md) | Лист персонажа, лестница приёмов, требования к вендору |
| [docs/domain-model.md](docs/domain-model.md) | Story Project, Character, Relationships, Collections, Quality Gates |
| [docs/privacy.md](docs/privacy.md) | Жизненный цикл фото, согласия, удаление, запрет обучения моделей |
| [docs/unit-economics.md](docs/unit-economics.md) | Модель юнит-экономики и разбор публичных заявлений рынка |
| [docs/market-notes.md](docs/market-notes.md) | Наблюдения по конкурентам (по состоянию на 2026-08-01) |
| [docs/decision-log.md](docs/decision-log.md) | Decision Log. Каждое решение — с датой, причиной и последствиями |

## Бизнес-пакет

| Файл | О чём |
|---|---|
| [docs/business/market-research.md](docs/business/market-research.md) | Исследование рынка с источниками: тиры, игроки, юр. рамка 152-ФЗ |
| [docs/business/product-line.md](docs/business/product-line.md) | Три продукта, цены, состав превью, критерии отдачи клиенту |
| [docs/business/unit-economics.md](docs/business/unit-economics.md) | Себестоимость, вклад, безубыточность, чувствительность, рычаги |
| [docs/business/forecast-90d.md](docs/business/forecast-90d.md) | Три сценария на август–октябрь, трафик, что считать успехом |
| [docs/business/gtm.md](docs/business/gtm.md) | Сегменты, каналы, оффер, лендинги, скрипт concierge-продажи |
| [docs/business/operations.md](docs/business/operations.md) | 19 шагов от заявки до отправки, роли, риски, правило остановки |
| [docs/business/budget-and-plan.md](docs/business/budget-and-plan.md) | Бюджет первого месяца и план на 14 дней |
| [docs/business/geo-expansion.md](docs/business/geo-expansion.md) | География: Нигерия, Египет, Залив, СНГ, диаспора — что сходится и почему |
| [docs/business/decisions-morning.md](docs/business/decisions-morning.md) | Р-1…Р-10: решения владельца с рекомендациями |

Расчётные модели: `python3 tools/econ.py` — юнит-экономика и прогноз;
`python3 tools/geo.py` — сравнение рынков по странам. Меняешь допущения — пересчитывается всё.

## Рабочие формы

Заполняются при прогоне книги. Не документация — инструменты.

| Форма | Когда |
|---|---|
| [forms/01-intake-form.md](forms/01-intake-form.md) | шаг 1 прогона |
| [forms/02-consistency-sheet.md](forms/02-consistency-sheet.md) | шаг 7, по одному листу на оценивающего |
| [forms/03-book-report.md](forms/03-book-report.md) | шаг 8, книга без него не считается прогнанной |
| [forms/04-deletion-log.md](forms/04-deletion-log.md) | шаг 9 и еженедельная сверка |

## Правило работы

Любое изменение каталога продуктов, политики хранения фото или позиционирования —
только через явное решение владельца, зафиксированное в Decision Log.
Scope creep запрещён.
