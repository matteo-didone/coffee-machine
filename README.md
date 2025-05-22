# ☕ Simulatore Macchinetta del Caffè - Event-Driven Architecture

## 📋 Panoramica

Questo progetto implementa una **simulazione software** del comportamento di una macchinetta del caffè basata su una **Finite State Machine (FSM)** che riceve eventi tramite **MQTT**.

L'architettura segue il paradigma **Event-Driven Architecture (EDA)** dove le azioni del sistema sono innescate da eventi esterni ricevuti via messaggi JSON su protocollo MQTT.

## 🏗️ Architettura del Sistema

### Componenti Principali

- **Event Producer**: Client che inviano comandi JSON via MQTT
- **Event Consumer**: La macchinetta del caffè che reagisce agli eventi
- **Event Broker**: Broker MQTT pubblico (`test.mosquitto.org`)
- **Event Processing**: Finite State Machine che gestisce la logica degli stati

### Pattern Implementati

- **Finite State Machine (FSM)**: Gestione degli stati della macchina
- **Event-Driven Architecture**: Comunicazione basata su eventi MQTT
- **Publisher-Subscriber**: Pattern MQTT per messaggi asincroni

## 🔄 Stati della Macchina

| Stato | Descrizione | Azioni Possibili |
|-------|-------------|------------------|
| `OFF` | Macchina spenta | `turn_on` |
| `READY` | Pronta per l'uso | `select_drink`, `turn_off` |
| `WAITING_SELECTION` | Bevanda selezionata | `brew`, `turn_off` |
| `BREWING` | Preparazione in corso | `turn_off` (automatico → `READY`) |

### Transizioni di Stato

```
OFF --[turn_on]--> READY
READY --[select_drink]--> WAITING_SELECTION  
WAITING_SELECTION --[brew]--> BREWING
BREWING --[timer completato]--> READY
Qualsiasi stato --[turn_off]--> OFF
```

## 🍹 Bevande Supportate

| Bevanda | Tempo Preparazione |
|---------|-------------------|
| `espresso` | 3 secondi |
| `cappuccino` | 5 secondi |
| `americano` | 4 secondi |

## 📡 Comunicazione MQTT

### Topics

- **Comandi**: `coffee_machine_demo/commands` (input)
- **Status**: `coffee_machine_demo/status` (output)

### Formato Messaggi JSON

#### Comandi (Input)
```json
{
  "source": "user1",
  "timestamp": "2025-05-22T10:00:00Z",
  "command": "turn_on"
}
```

```json
{
  "source": "user1", 
  "timestamp": "2025-05-22T10:00:00Z",
  "command": "select_drink",
  "payload": {
    "drink": "espresso"
  }
}
```

#### Status (Output)
```json
{
  "timestamp": "2025-05-22T10:00:00Z",
  "state": "ready",
  "selected_drink": null,
  "available_drinks": ["espresso", "cappuccino", "americano"]
}
```

## 🚀 Installazione e Utilizzo

### Prerequisiti

- Python 3.11+
- Connessione internet (per broker MQTT pubblico)

### Installazione

```bash
# Clona o scarica i file del progetto
cd coffee-machine

# Installa dipendenze
pip install paho-mqtt

# Oppure usa requirements.txt
pip install -r requirements.txt
```

### Esecuzione

#### 1. Avvia la Macchinetta

```bash
python main.py
```

Output atteso:
```
☕ === MACCHINETTA DEL CAFFÈ - VERSIONE SEMPLICE ===
📡 Connessione a test.mosquitto.org...
✅ Connesso al broker MQTT!
📥 In ascolto su: coffee_machine_demo/commands
```

#### 2. Esegui i Test

In un secondo terminale:

```bash
# Test automatico completo
python test_commands.py
# Scegli opzione 1

# Test interattivo
python test_commands.py  
# Scegli opzione 2
```

## 🧪 Test e Esempi

### Sequenza di Test Completa

1. **Accensione**: `turn_on` → OFF → READY
2. **Selezione**: `select_drink` → READY → WAITING_SELECTION
3. **Preparazione**: `brew` → WAITING_SELECTION → BREWING → READY
4. **Spegnimento**: `turn_off` → READY → OFF

### Comandi MQTT Manuali

Usando `mosquitto_pub`:

```bash
# Accendi macchina
mosquitto_pub -h test.mosquitto.org -t "coffee_machine_demo/commands" \
  -m '{"source": "user1", "command": "turn_on"}'

# Seleziona espresso  
mosquitto_pub -h test.mosquitto.org -t "coffee_machine_demo/commands" \
  -m '{"source": "user1", "command": "select_drink", "payload": {"drink": "espresso"}}'

# Avvia preparazione
mosquitto_pub -h test.mosquitto.org -t "coffee_machine_demo/commands" \
  -m '{"source": "user1", "command": "brew"}'

# Spegni macchina
mosquitto_pub -h test.mosquitto.org -t "coffee_machine_demo/commands" \
  -m '{"source": "user1", "command": "turn_off"}'
```

### Monitoraggio Status

```bash
# Monitora status in tempo reale
mosquitto_sub -h test.mosquitto.org -t "coffee_machine_demo/status"
```

## 📁 Struttura del Progetto

```
coffee-machine/
├── main.py                 # Applicazione principale (FSM + MQTT)
├── test_commands.py        # Client di test automatico
├── requirements.txt        # Dipendenze Python
├── README.md              # Documentazione
└── state_diagram.mmd      # Diagramma stati (Mermaid)
```

## 🔧 Dettagli Implementazione

### Classe `SimpleCoffeeMachine`

- **Stati**: Enum `CoffeeMachineState` con 4 stati
- **MQTT**: Client paho-mqtt per comunicazione asincrona  
- **Timer**: Threading.Timer per processi automatici
- **FSM**: Metodi per gestire transizioni di stato

### Metodi Principali

| Metodo | Descrizione |
|--------|-------------|
| `setup_mqtt()` | Configura connessione MQTT |
| `process_command()` | Elabora comandi JSON ricevuti |
| `change_state()` | Gestisce transizioni FSM |
| `publish_status()` | Pubblica stato corrente |

### Gestione Errori

- Fallback in modalità standalone se MQTT non disponibile
- Validazione comandi e stati
- Gestione timeout e cleanup risorse

## 🎯 Risultati Ottenuti

### Requisiti Soddisfatti

✅ **Logica a stati definita**: FSM con 4 stati principali  
✅ **Diagramma degli stati**: Creato con Mermaid  
✅ **Codice FSM**: Implementato e testato  
✅ **Formato JSON**: Messaggi strutturati per comandi e status  
✅ **Sistema MQTT**: Comunicazione event-driven funzionante  

### Test Superati

- ✅ Tutte le transizioni di stato
- ✅ Timer automatici per preparazione 
- ✅ Comandi JSON via MQTT
- ✅ Pubblicazione status in tempo reale
- ✅ Gestione errori e cleanup

## 🐛 Troubleshooting

### Problemi Comuni

**Errore connessione MQTT**:
- Verifica connessione internet
- Il broker pubblico potrebbe essere temporaneamente non disponibile
- L'app continua in modalità standalone

**ModuleNotFoundError paho-mqtt**:
```bash
pip install paho-mqtt
```

**Warning API deprecata**:
- Warning normale, non influisce sul funzionamento
- Può essere ignorato per questo progetto didattico

## 👥 Autori

Progetto realizzato per l'esercizio "Event-Driven Architecture" del corso di Architetture Cloud da Matteo Didonè e Federico Burello

## 📄 Licenza

Progetto didattico - Uso educativo