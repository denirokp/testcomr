# Доменная модель

Общий движок — **Personalized Story Engine**. Коллекции и редакционные правила лежат
поверх него (правило 15). Модель описана как контракт домена, а не как схема БД:
хранилище выбирается позже и не должно протекать в эти определения.

## Карта сущностей

```
StoryProject (агрегат)
├── Collection            — какой продукт собираем и по каким редакционным правилам
├── Character[]           — кто в книге (human / dog / cat / other_pet)
├── Relationship[]        — явный граф связей между Character
├── Intake                — что рассказал заказчик (факты, а не сюжет)
├── StorySpec             — утверждённая структура книги (арка, развороты)
├── Manuscript            — текст по разворотам
├── IllustrationSet       — визуал по разворотам + референсы персонажей
├── AssetVault            — фотографии и производные, под политикой приватности
├── ConsentRecord[]       — кто и на что дал согласие
├── QualityReport[]       — результаты Quality Gates
└── Order                 — превью, оплата, печать, доставка
```

**Story Project — центральная сущность** (правило 4). Нет и не будет типов `ChildBook`,
`PetBook`, `CoupleBook`. Разница между продуктами живёт в `Collection`, а не в отдельных
классах — иначе через полгода получим три несовместимых кодовых базы.

## Character

Универсальная модель для всех участников (правило 5).

```ts
type CharacterKind = 'human' | 'dog' | 'cat' | 'other_pet'

type CharacterRole =
  | 'protagonist'   // главный герой, иллюстрируется на каждом развороте
  | 'companion'     // спутник, иллюстрируется регулярно
  | 'supporting'    // появляется эпизодически
  | 'mentioned'     // существует в тексте, НЕ иллюстрируется

interface Character {
  id: CharacterId
  kind: CharacterKind
  role: CharacterRole
  displayName: string            // как к нему обращаются в книге
  ageBand?: AgeBand              // '0-2' | '3-5' | '6-8' | '9-12' | 'adult'; у питомца — опц.
  species?: string               // порода / вид, для other_pet обязателен
  appearance: AppearanceDescriptor
  traits: Trait[]                // 3–5 черт характера, из интейка, без выдумки
  photoRefs: AssetRef[]          // ссылки в AssetVault, не сами файлы
  consentRef: ConsentId          // без него персонаж не может быть иллюстрирован
}

interface AppearanceDescriptor {
  // Текстовое описание, порождённое из фото и подтверждённое человеком.
  // Именно оно, а не фото, попадает в генерацию текста.
  summary: string
  stableFeatures: string[]       // то, что обязано совпадать на всех разворотах
  derivedFrom: AssetRef[]
  approvedBy: 'editor' | 'customer'
  approvedAt: Timestamp
}
```

**Почему `AppearanceDescriptor` отдельно от фото:** это единственный артефакт внешности,
который переживает удаление оригиналов (правило 8). Он должен быть достаточным, чтобы
допечатать тираж через полгода без исходных фотографий.

## Relationship

Отношения — явный граф (правило 6), а не поле `parentName` в книге.

```ts
type RelationshipType =
  | 'companion_of'   // ребёнок ↔ питомец, питомец ↔ питомец
  | 'sibling_of'
  | 'guardian_of'    // взрослый → ребёнок; в каталоге 1 только для 'mentioned'
  | 'friend_of'

interface Relationship {
  from: CharacterId
  to: CharacterId
  type: RelationshipType
  symmetric: boolean
  narrativeWeight: 1 | 2 | 3     // насколько связь двигает сюжет
  evidence: string               // фраза заказчика из интейка, обосновывающая связь
}
```

`evidence` обязателен намеренно: он не даёт движку изобретать тёплые отношения,
которых заказчик не описывал (правило 13).

## Collection

```ts
type CollectionId = 'pet_only' | 'child' | 'child_plus_pet'

interface Collection {
  id: CollectionId
  allowedProtagonistKinds: CharacterKind[]
  spreadCount: number            // развороты, не «страницы»
  editorialRules: EditorialRuleSet
  requiresChildConsent: boolean
  status: 'active' | 'planned' | 'forbidden'
}
```

Активна на текущем этапе только `pet_only`. `child` и `child_plus_pet` — `planned`.
Любые другие идентификаторы коллекций — `forbidden` и не заводятся «про запас»:
пустая заготовка `couple` в коде — это уже начало scope creep (правило 16).

## Ограничения каталога (машиночитаемые)

Эти инварианты проверяются кодом, а не памятью команды.

| Инвариант | Правило |
|---|---|
| `protagonist.kind` ∈ `allowedProtagonistKinds` коллекции | 2 |
| Взрослый `human` может иметь только `role = 'mentioned'` | 2, 3 |
| Коллекция со `status != 'active'` не создаёт StoryProject | 16 |
| Персонаж с `role != 'mentioned'` требует валидного `consentRef` | 10 |
| Признаки «ушедшего» персонажа в интейке → жёсткий стоп на ручной разбор | 11 |

Последний инвариант важнее, чем кажется: люди заказывают книгу про недавно умершую
собаку, не написав об этом прямо. Автоматический весёлый текст в такой ситуации —
худшее, что может сделать продукт.

## Жизненный цикл StoryProject

```
draft
  → intake_complete        интейк собран, персонажи и связи подтверждены
  → generation             текст и иллюстрации
  → internal_qa            Quality Gates + Human Review
  → preview_ready          полное превью собрано
  → customer_review        заказчик смотрит превью
  → approved               заказчик подтвердил
  → paid                   ← оплата ТОЛЬКО после approved (правило 7)
  → in_print
  → shipped
  → archived               оригиналы удалены, остались описатели и макет
```

Ветки: `customer_review → generation` (правки), `internal_qa → generation` (провал гейта),
любой статус → `cancelled` (с обязательным удалением оригиналов).

**Порядок `approved → paid` — конституционный, а не UX-предпочтение.** Оплата до превью
запрещена правилом 7. Это сознательно дороже: мы платим за генерацию до денег клиента.
Экономика этого решения посчитана в [unit-economics.md](unit-economics.md).

## Quality Gates

```ts
interface QualityReport {
  gate: GateId
  verdict: 'pass' | 'fail' | 'needs_human'
  findings: Finding[]
  reviewedBy?: EditorId
}
```

| Gate | Что ловит | Правило |
|---|---|---|
| `text.authenticity` | шаблонность, фальшивая сентиментальность, «вставь имя» | 13 |
| `text.factuality` | утверждения о персонаже, не подтверждённые интейком | 13 |
| `text.age_fit` | лексика и длина под `ageBand` | 12 |
| `visual.consistency` | персонаж узнаваем на всех разворотах | 12 |
| `visual.safety` | недопустимые изображения детей и животных | 10, 12 |
| `scope.catalog` | продукт не выехал за пределы активной коллекции | 2, 16 |
| `privacy.assets` | нет утечки оригиналов в артефакты и логи | 8, 9, 10 |

`needs_human` — не аварийный режим, а нормальный исход. На concierge-этапе Human Review
обязателен для **каждой** книги.

## Что этот документ сознательно не описывает

Отложено до следующей итерации, чтобы не проектировать вслепую:
- схема хранения и выбор БД;
- API-контракты и очереди;
- конкретные модели генерации текста и изображений;
- механика вёрстки и препресс-требования типографии.

Домен от них не зависит — в этом и был смысл описать его первым.
