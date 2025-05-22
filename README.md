# ☕ Macchinetta del caffè - Event-Driven Architecture

## 🎯 Panoramica del Progetto

Questo progetto implementa una **simulazione software completa** del comportamento di una macchinetta del caffè professionale, sviluppata per l'esercizio "Event-Driven Architecture" del corso di Architetture Cloud.

L'implementazione dimostra una **comprensione approfondita** di:
- **🔄 Finite State Machine (FSM)** con 7 stati realistici
- **📡 Event-Driven Architecture (EDA)** via protocollo MQTT
- **📊 Event Sourcing** con database SQLite persistente
- **⚡ Processi automatici** e gestione avanzata degli errori
- **🧪 Test automation** con client di test completo

---

## 🏗️ Architettura del Sistema

### Componenti Principali

| Componente | Descrizione | Implementazione |
|------------|-------------|-----------------|
| **Event Producer** | Client che inviano comandi JSON | `test_commands.py` + publisher MQTT esterni |
| **Event Consumer** | Macchinetta che reagisce agli eventi | `main.py` - classe `CoffeeMachine` |
| **Event Broker** | Broker MQTT per messaggi asincroni | Mosquitto locale (`localhost:1883`) |
| **Event Store** | Database eventi persistente | SQLite (`coffee_machine_events.db`) |
| **Event Processing** | Logica FSM + azioni automatiche | Timer-based processes nella FSM |

### Pattern Architetturali Implementati

- ✅ **Event-Driven Architecture**: Comunicazione completamente asincrona via MQTT
- ✅ **Finite State Machine**: 7 stati con transizioni controllate e validate
- ✅ **Event Sourcing**: Persistenza completa di eventi e snapshot di stato
- ✅ **Publisher-Subscriber**: Pattern MQTT per messaggi real-time
- ✅ **State Aggregation**: Ricostruzione stato da eventi + snapshot periodici
- ✅ **Command Pattern**: Comandi JSON mappati su metodi della macchina

---

## 🔄 Finite State Machine - Design Completo

### Stati della Macchina

| Stato | Descrizione | Durata | Azioni Automatiche | Transizioni Possibili |
|-------|-------------|--------|--------------------|--------------------|
| `OFF` | 🔴 Macchina spenta | Permanente | Nessuna | `turn_on` → SELF_CHECK |
| `SELF_CHECK` | 🔍 Controllo sistemi | 3-7 secondi | Riscaldamento 20°→90°C | `check_ok` → READY, `error` → ERROR |
| `READY` | 🟢 Pronta per l'uso | Permanente | Monitoring risorse | `place_cup` → ASK_BEVERAGE, `start_cleaning` → SELF_CLEAN |
| `ASK_BEVERAGE` | 🤔 Selezione bevanda | 30s timeout | Timer selezione | `confirm_selection` → PRODUCE_BEVERAGE, `timeout` → READY |
| `PRODUCE_BEVERAGE` | ⚙️ Produzione | 3-5 secondi | Consumo risorse | `beverage_ready` → ASK_BEVERAGE/READY |
| `SELF_CLEAN` | 🧽 Pulizia automatica | 8 secondi | Reset contatori | `cleaning_complete` → READY |
| `ERROR` | ❌ Stato di errore | Permanente | Logging errore | `reset_error` → READY |

### Diagramma delle Transizioni
![Diagramma Stati](./Flowchart.jpeg)

### Logica di Transizione Avanzata

#### **Workflow Consecutivo (Innovazione Chiave)**
```python
# Dopo produzione bevanda:
if self.resources["cup_present"]:
    # Tazza ancora presente → workflow consecutivo
    self.change_state(ASK_BEVERAGE, "Tazza presente - nuova selezione")
else:
    # Tazza rimossa → ritorno normale
    self.change_state(READY, "Bevanda completata")
```

Questa logica permette **bevande consecutive** senza dover rimuovere e riposizionare la tazza - **molto più realistico**!

---

## 🍹 Sistema Bevande e Gestione Risorse

### Bevande Supportate

| Bevanda | Tempo Preparazione | Consumo Acqua | Consumo Caffè | Note |
|---------|------------------|---------------|---------------|------|
| `espresso` | 3 secondi | 30ml (3%) | 7g (7%) | Bevanda base |
| `cappuccino` | 5 secondi | 150ml (15%) | 7g (7%) | Include latte |
| `americano` | 4 secondi | 200ml (20%) | 7g (7%) | Caffè lungo |

### Gestione Risorse Dinamica

```python
self.resources = {
    "water_level": 100,      # 100% → 0% (soglia errore: <10%)
    "coffee_level": 100,     # 100% → 0% (soglia errore: <5%)
    "cup_present": False,    # Tracking presenza tazza
    "temperature": 20,       # 20°C → 90°C (riscaldamento automatico)
    "cleaning_cycles": 0     # Contatore per pulizia automatica
}
```

#### **Pulizia Automatica Intelligente**
- **Trigger**: Ogni 10 bevande prodotte
- **Durata**: 8 secondi di simulazione
- **Effetti**: Reset contatori, interruzione workflow corrente
- **Recovery**: Automatico ritorno a READY

---

## 📡 Comunicazione MQTT - Architettura Completa

### Topics Structure

| Topic | Direzione | QoS | Descrizione | Formato |
|-------|-----------|-----|-------------|---------|
| `enhanced_coffee_machine/commands` | Input | 0 | Comandi JSON ricevuti | Command Object |
| `enhanced_coffee_machine/status` | Output | 0 | Stato corrente e risorse | Status Object |
| `enhanced_coffee_machine/events` | Output | 0 | Log eventi in tempo reale | Event Object |

### Formato Messaggi Dettagliato

#### **Comandi (Input)**
```json
{
  "source": "enhanced_tester",           // Identificativo client
  "timestamp": "2025-05-22T10:00:00Z",   // ISO timestamp
  "command": "select_beverage",          // Comando da eseguire
  "payload": {                           // Dati aggiuntivi (opzionale)
    "beverage": "cappuccino"
  }
}
```

**Comandi Supportati:**
- `turn_on` / `turn_off` - Controllo alimentazione
- `place_cup` / `remove_cup` - Gestione tazza
- `select_beverage` + `confirm_selection` - Selezione bevanda
- `start_cleaning` - Pulizia manuale
- `reset_error` - Reset stato errore
- `refill_water` / `refill_coffee` - Riempimento serbatoi

#### **Status (Output)**
```json
{
  "timestamp": "2025-05-22T10:00:00Z",
  "state": "ask_beverage",               // Stato FSM corrente
  "selected_beverage": "espresso",       // Bevanda selezionata (se presente)
  "error_type": null,                    // Tipo errore (se presente)
  "resources": {
    "water_level": 85,                   // Livello acqua (%)
    "coffee_level": 78,                  // Livello caffè (%)
    "temperature": 90,                   // Temperatura (°C)
    "cup_present": true,                 // Presenza tazza
    "cleaning_cycles": 3                 // Cicli dalla ultima pulizia
  },
  "available_beverages": ["espresso", "cappuccino", "americano"]
}
```

#### **Eventi (Output)**
```json
{
  "timestamp": "2025-05-22T10:00:00Z",
  "event": "state_changed",              // Tipo evento
  "state": "produce_beverage",           // Stato corrente
  "data": {                              // Dati contextuali
    "reason": "Selezione confermata",
    "previous_state": "ask_beverage"
  }
}
```

**Tipi di Eventi Tracciati:**
- `system_started` - Avvio sistema
- `state_changed` - Cambio stato FSM
- `command_*` - Tutti i comandi ricevuti
- `resource_consumed` - Consumo risorse
- `error_occurred` - Errori di sistema
- `cleaning_triggered` - Inizio pulizia

---

## 🗃️ Event Sourcing - Implementazione Completa

### Database SQLite Structure

#### **Tabella `events`**
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,              -- ISO timestamp evento
    event_type TEXT NOT NULL,             -- Tipo evento (es. "state_changed")
    old_state TEXT,                       -- Stato precedente
    new_state TEXT,                       -- Nuovo stato
    data TEXT,                           -- JSON con dati aggiuntivi
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### **Tabella `state_snapshots`**
```sql
CREATE TABLE state_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,              -- Timestamp snapshot
    state TEXT NOT NULL,                  -- Stato FSM
    resources TEXT NOT NULL,              -- JSON risorse complete
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Event Sourcing in Azione

```python
def log_event(self, event_type: str, data: Dict[str, Any] = None):
    """Registra evento nel database (Event Sourcing)"""
    # 1. Salva in database SQLite
    with self.db_lock:
        cursor = self.db_conn.cursor()
        cursor.execute('''INSERT INTO events ...''')
        self.db_conn.commit()
    
    # 2. Pubblica via MQTT per subscribers real-time
    event_msg = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        "state": self.state.value,
        "data": data or {}
    }
    self.publish_mqtt(self.events_topic, event_msg)
```

### Ricostruzione Stato

**Teoricamente possibile** (implementazione di base inclusa):
1. Leggere tutti gli eventi dal database in ordine cronologico
2. Riapplicare le transizioni di stato sequenzialmente
3. Ricostruire lo stato completo della macchina
4. Validare con l'ultimo snapshot disponibile

---

## 🚀 Installazione e Setup

### Prerequisiti

- **Python 3.11+**
- **Mosquitto MQTT Broker** (locale)
- **Connessione di rete** (per broker remoti opzionali)

### Setup Mosquitto (macOS)

```bash
# Installa Mosquitto
brew install mosquitto

# Configura per accettare connessioni esterne
echo "listener 1883 0.0.0.0" >> /opt/homebrew/etc/mosquitto/mosquitto.conf
echo "allow_anonymous true" >> /opt/homebrew/etc/mosquitto/mosquitto.conf

# Avvia broker
brew services start mosquitto

# Oppure avvia manualmente
mosquitto -c /opt/homebrew/etc/mosquitto/mosquitto.conf -v
```

### Setup Mosquitto (Linux/Ubuntu)

```bash
# Installa Mosquitto
sudo apt update
sudo apt install mosquitto mosquitto-clients

# Configura
sudo nano /etc/mosquitto/mosquitto.conf
# Aggiungi:
# listener 1883 0.0.0.0
# allow_anonymous true

# Avvia servizio
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

### Installazione Progetto

```bash
# Clona o scarica i file del progetto
mkdir enhanced-coffee-machine
cd enhanced-coffee-machine

# File richiesti:
# - main.py (applicazione principale)
# - test_commands.py (client di test)
# - requirements.txt (dipendenze)
# - README.md (questa documentazione)

# Installa dipendenze Python
pip install -r requirements.txt
```

### File `requirements.txt`
```
paho-mqtt==1.6.1
```

---

## 🎮 Utilizzo del Sistema

### 1. Avvio dell'Applicazione Principale

```bash
python main.py
```

**Output atteso:**
```
☕ === ENHANCED COFFEE MACHINE ===
🏗️ Event-Driven Architecture + Finite State Machine
📡 Connessione MQTT: localhost
✅ Connesso al broker MQTT
🚀 Enhanced Coffee Machine - Versione Completa

============================================================
📊 STATO: OFF
💧 Acqua: 100%
☕ Caffè: 100%
🌡️ Temperatura: 20°C
🥤 Tazza: Assente
============================================================
```

### 2. Esecuzione Test Automatici

```bash
# In un nuovo terminale
python test_commands.py
```

**Menu di Test:**
```
🧪 Enhanced Coffee Machine Tester
Scegli modalità di test:
1 - Test ciclo completo
2 - Test pulizia
3 - Test scenari errore
4 - Test produzione multipla
5 - Test pulizia automatica (10 bevande)
6 - Tutti i test automatici
7 - Modalità interattiva
```

### 3. Controllo Manuale via MQTT

```bash
# Comandi manuali con mosquitto_pub
mosquitto_pub -h localhost -t enhanced_coffee_machine/commands \
  -m '{"source": "manual", "command": "turn_on"}'

mosquitto_pub -h localhost -t enhanced_coffee_machine/commands \
  -m '{"source": "manual", "command": "place_cup"}'

mosquitto_pub -h localhost -t enhanced_coffee_machine/commands \
  -m '{"source": "manual", "command": "select_beverage", "payload": {"beverage": "espresso"}}'

mosquitto_pub -h localhost -t enhanced_coffee_machine/commands \
  -m '{"source": "manual", "command": "confirm_selection"}'
```

### 4. Monitoraggio Real-time

```bash
# Monitor di tutti i messaggi
mosquitto_sub -h localhost -t enhanced_coffee_machine/# -v

# Solo status
mosquitto_sub -h localhost -t enhanced_coffee_machine/status

# Solo eventi
mosquitto_sub -h localhost -t enhanced_coffee_machine/events
```

---
## 🔧 Dettagli Implementazione

### Classe `CoffeeMachine` - Componente Principale

#### **Attributi Chiave**
```python
class CoffeeMachine:
    def __init__(self):
        # FSM State Management
        self.state = MachineState.OFF
        self.previous_state = None
        self.error_type: Optional[ErrorType] = None
        
        # Business Logic
        self.beverages = {...}           # Configurazione bevande
        self.selected_beverage = None    # Selezione corrente
        self.resources = {...}           # Stato risorse
        
        # Infrastructure
        self.active_timer = None         # Timer per processi automatici
        self.mqtt_client = None          # Client MQTT
        self.db_conn = None             # Connessione SQLite
```

#### **Metodi Principali**

**Gestione Stati:**
- `change_state()` - Transizioni FSM con logging e validazione
- `_handle_state_entry()` - Azioni automatiche per ogni stato
- `show_status()` - Visualizzazione stato dettagliato

**Comandi Business:**
- `turn_on()` / `turn_off()` - Ciclo di vita macchina
- `place_cup()` / `remove_cup()` - Gestione presenza tazza
- `select_beverage()` / `confirm_selection()` - Workflow bevande
- `start_cleaning()` / `reset_error()` - Manutenzione

**Processi Automatici:**
- `_start_self_check()` - Controllo iniziale + riscaldamento
- `_start_production()` - Produzione bevanda + consumo risorse
- `_start_cleaning_cycle()` - Pulizia automatica
- `_start_selection_timeout()` - Timeout selezione bevanda

**Infrastructure:**
- `setup_mqtt()` - Configurazione comunicazione
- `log_event()` - Event Sourcing
- `publish_status()` - Broadcasting stato

### Classe `EnhancedTester` - Client di Test

#### **Funzionalità**
- **Connessione MQTT**: Automatica con retry logic
- **State Monitoring**: Tracking real-time stato macchina
- **Test Automation**: 5 suite di test automatiche
- **Interactive Mode**: Controllo manuale per debug
- **Resource Tracking**: Monitoraggio consumo acqua/caffè

#### **Architettura Test**
```python
class EnhancedTester:
    def send_command(self, command, payload=None, delay=1.5)
    def wait_for_state(self, expected_state, timeout=10)
    def test_full_cycle()          # Test base completo
    def test_error_scenarios()     # Test gestione errori
    def test_automatic_cleaning()  # Test pulizia automatica
    def interactive_mode()         # Modalità manuale
```

### Gestione Errori Avanzata

#### **Tipi di Errore**
```python
class ErrorType(Enum):
    WATER_EMPTY = "water_empty"      # Serbatoio acqua < 10%
    COFFEE_EMPTY = "coffee_empty"    # Serbatoio caffè < 5%
    CUP_MISSING = "cup_missing"      # Tazza rimossa durante produzione
    SYSTEM_ERROR = "system_error"    # Errori generici/eccezioni
    CLEANING_ERROR = "cleaning_error" # Fallimento pulizia
```

#### **Recovery Strategy**
- **Automatic Recovery**: Riempimento serbatoi → auto-reset
- **Manual Recovery**: `reset_error` command
- **State Preservation**: Mantenimento risorse durante errore
- **Graceful Degradation**: Spegnimento sicuro da qualsiasi stato

---

## 📄 Crediti

Progetto svolto da:

- **Matteo Didonè**
- **Federico Burello**

Realizzato per l’esercitazione “**Event-Driven Architecture**”  
nel corso di **Architetture Cloud IoT** – ITS Alto Adriatico
