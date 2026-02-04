Perfeito. Agora sim dá pra **fechar a v0.3.3 com critério**.
Vou fazer exatamente o que você pediu: **cobrir os gaps**, sem mudar o rumo do projeto, usando **o README e o CHANGELOG que você enviou** como base .

Vou dividir em 3 partes objetivas:

1. **Veredito técnico do estado atual**
2. **O que entra oficialmente na v0.3.3**
3. **Arquivos prontos pra você copiar e colar**

   * `PROTOCOL.md`
   * ajuste mínimo no `README.md`
   * `CHANGELOG.md` v0.3.3

---

## 1️⃣ Veredito técnico (frio e honesto)

**Estado atual (v0.3.2):**

* Arquitetura: **correta**
* Ideia central: **clara**
* Implementação: **coerente**
* Risco de desvio: **baixo**
* Risco real: **protocolo implícito (não documentado)**

👉 Ou seja: **o código já é melhor que a documentação**.
A v0.3.3 existe exatamente pra alinhar isso.

---

## 2️⃣ O que a v0.3.3 PRECISA fazer (e só isso)

### ✅ Entram na v0.3.3

* Protocolo **documentado e congelado** (`ssp/0.2`)
* Core signals oficialmente definidos
* Capabilities enriquecidas (sem breaking change)
* Testes mínimos de forma (shape / schema)
* README alinhado com o papel real do projeto

### ❌ Não entram

* Dashboard
* .exe
* Portas (UDP / Serial)
* UI / config

Esses ficam **100% limpos pra v0.4.0**.

---

## 3️⃣ Arquivos finais da v0.3.3

---

# 📄 `PROTOCOL.md` (NOVO – copie e cole)

````md
# SSP – SimRacing Standard Protocol
Version: ssp/0.2

This document defines the **SSP telemetry protocol**, a simulator-agnostic
data format designed to unify sim racing telemetry for dashboards, tools,
and custom hardware (Arduino, ESP32, etc).

The protocol is **capability-driven**, **state-aware**, and **forward-compatible**.

---

## 1. Core Concepts

### 1.1 State Model

The bridge operates as a persistent state machine and emits lifecycle events:

- `waiting` – No simulator detected
- `active` – Telemetry is flowing
- `lost` – Simulator disconnected or stalled

State events are **deduplicated** and must be handled idempotently by clients.

---

## 2. Message Types

### 2.1 Status Event

```json
{
  "type": "status",
  "ts": 1770225996.75,
  "state": "active",
  "source": "acc"
}
````

| Field  | Type          | Description                 |
| ------ | ------------- | --------------------------- |
| type   | string        | Always `"status"`           |
| ts     | number        | Unix timestamp (seconds)    |
| state  | string        | `waiting`, `active`, `lost` |
| source | string | null | Active simulator or null    |

---

### 2.2 Capabilities Handshake

Emitted on simulator connect or switch.

```json
{
  "type": "capabilities",
  "ts": 1770226017.54,
  "source": "acc",
  "schema": "ssp/0.2",
  "capabilities": {
    "schema": "ssp/0.2",
    "plugin": "acc",
    "signals": {
      "engine.rpm": {
        "type": "integer",
        "unit": "rpm",
        "hz": 60,
        "min": 0,
        "max": 12000
      }
    }
  }
}
```

Capabilities describe **what MAY appear** in telemetry frames.
Signals not listed here must not be assumed by clients.

---

### 2.3 Telemetry Frame

```json
{
  "v": "0.2",
  "ts": 1770226017.57,
  "source": "acc",
  "signals": {
    "engine.rpm": 7200,
    "vehicle.speed_kmh": 145.5
  }
}
```

| Field   | Type   | Description                |
| ------- | ------ | -------------------------- |
| v       | string | Protocol version (`"0.2"`) |
| ts      | number | Unix timestamp             |
| source  | string | Simulator ID               |
| signals | object | Key-value map of telemetry |

**Rules:**

* Missing signals mean “not available”, not zero.
* Clients must rely on capabilities for discovery.
* Backward compatibility is preserved within the same `v`.

---

## 3. Core Signals (Frozen)

These signals form the **SSP Core v0.2**.
Plugins should provide them whenever possible.

| Signal                | Type    | Unit |
| --------------------- | ------- | ---- |
| engine.rpm            | integer | rpm  |
| vehicle.speed_kmh     | number  | km/h |
| drivetrain.gear       | integer | gear |
| controls.throttle_pct | number  | %    |
| controls.brake_pct    | number  | %    |

Optional:

* `controls.clutch_pct`

---

## 4. Versioning Rules

* `schema` identifies the SSP generation (`ssp/0.2`)
* `v` identifies frame compatibility
* Minor additions do not break clients
* Renaming or unit changes require a new major version

---

## 5. Design Goals

* Simulator-agnostic
* Hardware-friendly
* No hidden assumptions
* Easy to implement on microcontrollers

---

SSP is a **contract**, not an implementation detail.

````

---

# ✏️ Ajuste mínimo no `README.md`

Adicionar **uma única seção**, sem mudar o resto:

```md
## 📜 Protocol Specification

SSP-BRIDGE implements the **SimRacing Standard Protocol (SSP)**.

The protocol is fully documented and versioned in:

- [`PROTOCOL.md`](./PROTOCOL.md)

Dashboards, tools, and hardware integrations should rely on the protocol
definition rather than simulator-specific behavior.
````