# Mermaid Syntax Reference

Quick-reference patterns for the most common diagram types. Always test mentally
that the syntax is valid before outputting — invalid Mermaid silently fails to render.

---

## Flowchart

Use for: process flows, SOPs, decision trees, campaign workflows.

```mermaid
flowchart TD
    %% Use TD (top-down) or LR (left-right)
    A([Start]) --> B[First step]
    B --> C{Decision point?}
    C -- Yes --> D[Action if yes]
    C -- No --> E[Action if no]
    D --> F([End])
    E --> F
```

**Node shapes:**
- `[Text]` — rectangle (process step)
- `{Text}` — diamond (decision)
- `([Text])` — stadium/pill (start/end)
- `[(Text)]` — cylinder (database)
- `((Text))` — circle (connector)
- `[/Text/]` — parallelogram (input/output)
- `[[Text]]` — subroutine

**Swim lanes** (use `subgraph` for lanes by team/system):
```mermaid
flowchart LR
    subgraph Marketing
        A[Create campaign] --> B[Publish]
    end
    subgraph Sales
        C[Receive lead] --> D[Qualify]
    end
    B --> C
```

**Styling nodes** (use `classDef` for color groups):
```mermaid
flowchart TD
    classDef highlight fill:#f9c74f,stroke:#f3722c,color:#000
    A[Normal step] --> B[Important step]:::highlight
```

**Gotchas:**
- Labels with parentheses, slashes, or quotes must be wrapped: `A["Label (detail)"]`
- Avoid `end` as a node ID — it's a reserved word
- `subgraph` titles with spaces need quotes: `subgraph "My Team"`

---

## Sequence Diagram

Use for: API calls, system interactions, auth flows, handoffs between services/teams.

```mermaid
sequenceDiagram
    participant U as User
    participant A as App
    participant DB as Database

    U->>A: Submit form
    A->>DB: Query record
    DB-->>A: Return data
    A-->>U: Show result

    %% Activation boxes
    activate A
    A->>DB: Write update
    deactivate A

    %% Notes
    Note over U,A: This is a note spanning two actors
    Note right of DB: Single-actor note
```

**Arrow types:**
- `->>` solid arrow (sync call)
- `-->>` dashed arrow (async response)
- `-x` solid with X (failed call)
- `-)` open arrowhead

**Loops and conditionals:**
```mermaid
sequenceDiagram
    loop Every 5 minutes
        A->>B: Poll for updates
    end
    alt Success
        B-->>A: Return data
    else Failure
        B-->>A: Return error
    end
```

**Gotchas:**
- Participant aliases (`participant A as App`) prevent long names in arrows
- `autonumber` at the top adds step numbers automatically

---

## ER Diagram (Entity Relationship)

Use for: database schemas, data models, object relationships.

```mermaid
erDiagram
    CUSTOMER {
        int id PK
        string name
        string email
        date created_at
    }
    ORDER {
        int id PK
        int customer_id FK
        date order_date
        string status
    }
    PRODUCT {
        int id PK
        string name
        float price
    }
    ORDER_ITEM {
        int order_id FK
        int product_id FK
        int quantity
    }

    CUSTOMER ||--o{ ORDER : "places"
    ORDER ||--|{ ORDER_ITEM : "contains"
    PRODUCT ||--o{ ORDER_ITEM : "included in"
```

**Relationship cardinality:**
- `||--||` — exactly one to exactly one
- `||--o{` — one to zero or more
- `||--|{` — one to one or more
- `}o--o{` — zero or more to zero or more

**Gotchas:**
- Attribute types are display-only; Mermaid doesn't enforce them
- `PK` and `FK` are display markers, not functional
- Relationship labels must be quoted if they contain spaces

---

## State Diagram

Use for: status workflows, ticket lifecycles, approval chains.

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> InReview : Submit for review
    InReview --> Approved : Reviewer approves
    InReview --> Draft : Reviewer requests changes
    Approved --> Published : Publish
    Published --> Archived : Archive
    Archived --> [*]

    %% Compound states
    state InReview {
        [*] --> AwaitingReview
        AwaitingReview --> UnderReview : Reviewer opens
        UnderReview --> [*]
    }
```

**Gotchas:**
- Use `stateDiagram-v2` not `stateDiagram` (v2 is the current version)
- State names with spaces need quotes or underscores

---

## Gantt Chart

Use for: project timelines, sprint plans, campaign schedules.

```mermaid
gantt
    title Q2 Campaign Launch
    dateFormat YYYY-MM-DD
    section Strategy
        Brief & kickoff       :done,    s1, 2026-04-01, 5d
        Audience research     :active,  s2, 2026-04-06, 7d
    section Creative
        Copy drafts           :         c1, after s2, 5d
        Design assets         :         c2, after s2, 7d
        Review & approval     :crit,    c3, after c1, 3d
    section Launch
        Campaign goes live    :milestone, m1, after c3, 0d
```

**Status markers:** `done`, `active`, `crit` (critical path), `milestone`

---

## Class Diagram

Use for: object models, domain concepts, API response structures.

```mermaid
classDiagram
    class User {
        +int id
        +String name
        +String email
        +login() bool
        +logout() void
    }
    class Organization {
        +int id
        +String name
        +List~User~ members
    }
    class Project {
        +int id
        +String title
        +String status
    }

    User "1" --> "*" Project : owns
    Organization "1" *-- "*" User : has members
```

**Relationship types:**
- `-->` association
- `*--` composition
- `o--` aggregation
- `<|--` inheritance

---

## Common Gotchas (all diagram types)

1. **Special characters in labels** — Always quote labels containing `()`, `[]`, `/`, `#`, `&`, or `:`
2. **Reserved words** — Avoid using `end`, `start`, `class`, `state` as node IDs
3. **Long labels** — Keep under ~40 chars; break with `<br/>` inside quotes if needed
4. **Subgraph IDs** — Must be unique; using the same ID as a node causes silent failure
5. **Whitespace sensitivity** — Indentation matters in `sequenceDiagram` and `stateDiagram`
6. **Mermaid version differences** — Some tools use older Mermaid versions; stick to core syntax and avoid beta features like `kanban` or `sankey` unless you know the target renderer supports them
