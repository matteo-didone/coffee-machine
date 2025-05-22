#!/usr/bin/env python3
"""
Enhanced Coffee Machine - Event Driven Architecture
Implementazione completa con FSM avanzata e gestione eventi MQTT
"""

import json
import time
import threading
import sqlite3
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import paho.mqtt.client as mqtt

class MachineState(Enum):
    """Stati della macchinetta del caffè - FSM completa"""
    OFF = "off"
    SELF_CHECK = "self_check"
    READY = "ready"
    ASK_BEVERAGE = "ask_beverage"
    PRODUCE_BEVERAGE = "produce_beverage"
    SELF_CLEAN = "self_clean"
    ERROR = "error"

class ErrorType(Enum):
    """Tipi di errore gestiti"""
    WATER_EMPTY = "water_empty"
    COFFEE_EMPTY = "coffee_empty"
    CUP_MISSING = "cup_missing"
    SYSTEM_ERROR = "system_error"
    CLEANING_ERROR = "cleaning_error"

class CoffeeMachine:
    """Macchinetta del caffè con FSM completa e Event Sourcing"""
    
    def __init__(self):
        # === CONFIGURAZIONE STATI ===
        self.state = MachineState.OFF
        self.previous_state = None
        self.error_type: Optional[ErrorType] = None
        
        # === CONFIGURAZIONE BEVANDE ===
        self.beverages = {
            "espresso": {"time": 3, "water": 30, "coffee": 7},
            "cappuccino": {"time": 5, "water": 150, "coffee": 7},
            "americano": {"time": 4, "water": 200, "coffee": 7}
        }
        self.selected_beverage: Optional[str] = None
        
        # === RISORSE MACCHINA ===
        self.resources = {
            "water_level": 100,  # Percentuale
            "coffee_level": 100,  # Percentuale
            "cup_present": False,
            "temperature": 20,  # Celsius
            "cleaning_cycles": 0
        }
        
        # === TIMERS ===
        self.active_timer: Optional[threading.Timer] = None
        self.selection_timeout = 30  # secondi
        
        # === MQTT ===
        self.mqtt_broker = "localhost"
        self.mqtt_port = 1883
        self.base_topic = "enhanced_coffee_machine"
        self.command_topic = f"{self.base_topic}/commands"
        self.status_topic = f"{self.base_topic}/status"
        self.events_topic = f"{self.base_topic}/events"
        
        # === EVENT SOURCING DATABASE ===
        self.init_database()
        
        # === SETUP ===
        self.setup_mqtt()
        self.log_event("system_started")
        print("🚀 Enhanced Coffee Machine - Versione Completa")
        self.show_status()
    
    def init_database(self):
        """Inizializza database SQLite per Event Sourcing"""
        self.db_conn = sqlite3.connect('coffee_machine_events.db', check_same_thread=False)
        self.db_lock = threading.Lock()
        
        cursor = self.db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                old_state TEXT,
                new_state TEXT,
                data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS state_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                state TEXT NOT NULL,
                resources TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
        
        self.db_conn.commit()
    
    def log_event(self, event_type: str, data: Dict[str, Any] = None):
        """Registra evento nel database (Event Sourcing)"""
        with self.db_lock:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO events (timestamp, event_type, old_state, new_state, data)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                event_type,
                self.previous_state.value if self.previous_state else None,
                self.state.value,
                json.dumps(data) if data else None
            ))
            self.db_conn.commit()
        
        # Pubblica evento via MQTT
        event_msg = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "state": self.state.value,
            "data": data or {}
        }
        self.publish_mqtt(self.events_topic, event_msg)
    
    def setup_mqtt(self):
        """Setup connessione MQTT"""
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        
        try:
            print(f"📡 Connessione MQTT: {self.mqtt_broker}")
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            time.sleep(1)
        except Exception as e:
            print(f"❌ Errore MQTT: {e}")
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback connessione MQTT"""
        if rc == 0:
            print("✅ Connesso al broker MQTT")
            client.subscribe(self.command_topic)
            self.publish_status()
        else:
            print(f"❌ Connessione MQTT fallita: {rc}")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Gestisce comandi MQTT"""
        try:
            command = json.loads(msg.payload.decode())
            print(f"📨 Comando: {command}")
            self.process_command(command)
        except Exception as e:
            print(f"❌ Errore messaggio: {e}")
    
    def process_command(self, command: Dict[str, Any]):
        """Processa comandi JSON con FSM"""
        cmd = command.get("command")
        payload = command.get("payload", {})
        
        # Mappa comandi -> metodi
        command_map = {
            "turn_on": self.turn_on,
            "turn_off": self.turn_off,
            "place_cup": self.place_cup,
            "remove_cup": self.remove_cup,
            "select_beverage": lambda: self.select_beverage(payload.get("beverage")),
            "confirm_selection": self.confirm_selection,
            "start_cleaning": self.start_cleaning,
            "reset_error": self.reset_error,
            "refill_water": self.refill_water,
            "refill_coffee": self.refill_coffee
        }
        
        if cmd in command_map:
            try:
                command_map[cmd]()
                self.log_event(f"command_{cmd}", payload)
            except Exception as e:
                print(f"❌ Errore comando {cmd}: {e}")
                self.set_error(ErrorType.SYSTEM_ERROR)
        else:
            print(f"❌ Comando sconosciuto: {cmd}")
    
    def change_state(self, new_state: MachineState, reason: str = ""):
        """Cambia stato FSM con logging"""
        if self.state == new_state:
            return
        
        # Cancella timer del vecchio stato prima di cambiare
        if self.state == MachineState.ASK_BEVERAGE:
            self._cancel_timers()  # Cancella timeout selezione
        
        self.previous_state = self.state
        self.state = new_state
        
        print(f"🔄 {self.previous_state.value} → {new_state.value}" + 
              (f" ({reason})" if reason else ""))
        
        self.log_event("state_changed", {"reason": reason})
        self.publish_status()
        self.show_status()
        
        # Avvia azioni automatiche per nuovo stato
        self._handle_state_entry(new_state)
    
    def _handle_state_entry(self, state: MachineState):
        """Gestisce azioni automatiche all'ingresso di uno stato"""
        if state == MachineState.SELF_CHECK:
            self._start_self_check()
        elif state == MachineState.ASK_BEVERAGE:
            self._start_selection_timeout()
        elif state == MachineState.PRODUCE_BEVERAGE:
            self._start_production()
        elif state == MachineState.SELF_CLEAN:
            self._start_cleaning_cycle()
    
    # === COMANDI PRINCIPALI ===
    
    def turn_on(self):
        """Accende la macchina"""
        if self.state == MachineState.OFF:
            self.change_state(MachineState.SELF_CHECK, "Accensione")
        else:
            print("⚠️ Macchina già accesa")
    
    def turn_off(self):
        """Spegne la macchina"""
        if self.state != MachineState.OFF:
            self._cancel_timers()  # Cancella tutti i timer PRIMA di cambiare stato
            self.selected_beverage = None
            self.error_type = None  # Reset errore al spegnimento
            self.resources["cup_present"] = False
            self.change_state(MachineState.OFF, "Spegnimento")
        else:
            print("⚠️ Macchina già spenta")
    
    def place_cup(self):
        """Posiziona tazza"""
        if self.resources["cup_present"]:
            print("⚠️ Tazza già presente")
            return
            
        if self.state == MachineState.READY:
            self.resources["cup_present"] = True
            print("🥤 Tazza posizionata")
            self.change_state(MachineState.ASK_BEVERAGE, "Tazza posizionata")
        elif self.state == MachineState.OFF:
            print("❌ Accendi prima la macchina")
        elif self.state == MachineState.SELF_CHECK:
            print("⏳ Aspetta il completamento del self check")
        elif self.state == MachineState.ERROR:
            print("❌ Risolvi prima l'errore")
        else:
            print(f"❌ Non posso posizionare tazza nello stato: {self.state.value}")
    
    def remove_cup(self):
        """Rimuove tazza"""
        if self.resources["cup_present"]:
            self.resources["cup_present"] = False
            self.selected_beverage = None  # Cancella selezione eventuale
            print("🥤 Tazza rimossa")
            
            # Logica intelligente per cambio stato
            if self.state == MachineState.ASK_BEVERAGE:
                self._cancel_timers()  # Cancella timeout selezione
                self.change_state(MachineState.READY, "Tazza rimossa durante selezione")
            elif self.state == MachineState.PRODUCE_BEVERAGE:
                # Tazza rimossa durante produzione - possibile errore
                self._cancel_timers()
                self.set_error(ErrorType.CUP_MISSING)
            # Se siamo in READY con tazza, rimaniamo in READY senza tazza
            
        else:
            print("⚠️ Nessuna tazza da rimuovere")
    
    def select_beverage(self, beverage: str):
        """Seleziona bevanda"""
        if self.state == MachineState.ASK_BEVERAGE:
            if beverage in self.beverages:
                self.selected_beverage = beverage
                print(f"☕ Bevanda selezionata: {beverage}")
                print("✅ Invia 'confirm_selection' per confermare")
            else:
                print(f"❌ Bevanda non disponibile: {beverage}")
                print(f"🍹 Disponibili: {list(self.beverages.keys())}")
        else:
            print(f"❌ Non posso selezionare nello stato: {self.state.value}")
    
    def confirm_selection(self):
        """Conferma selezione bevanda"""
        if self.state == MachineState.ASK_BEVERAGE and self.selected_beverage:
            if self._check_resources():
                self.change_state(MachineState.PRODUCE_BEVERAGE, "Selezione confermata")
            else:
                self.set_error(ErrorType.WATER_EMPTY if self.resources["water_level"] < 10 
                             else ErrorType.COFFEE_EMPTY)
        else:
            print("❌ Nessuna bevanda selezionata")
    
    def start_cleaning(self):
        """Avvia ciclo di pulizia"""
        if self.state == MachineState.READY:
            self.change_state(MachineState.SELF_CLEAN, "Pulizia manuale")
        else:
            print(f"❌ Non posso pulire nello stato: {self.state.value}")
    
    def reset_error(self):
        """Reset errore"""
        if self.state == MachineState.ERROR:
            self.error_type = None
            self.change_state(MachineState.READY, "Reset errore")
        else:
            print("⚠️ Nessun errore da resettare")
    
    def refill_water(self):
        """Riempie serbatoio acqua"""
        self.resources["water_level"] = 100
        print("💧 Serbatoio acqua riempito")
        if self.state == MachineState.ERROR and self.error_type == ErrorType.WATER_EMPTY:
            self.reset_error()
    
    def refill_coffee(self):
        """Riempie serbatoio caffè"""
        self.resources["coffee_level"] = 100
        print("☕ Serbatoio caffè riempito")
        if self.state == MachineState.ERROR and self.error_type == ErrorType.COFFEE_EMPTY:
            self.reset_error()
    
    # === PROCESSI AUTOMATICI ===
    
    def _start_self_check(self):
        """Avvia controllo sistemi"""
        print("🔍 Self check in corso...")
        self.resources["temperature"] = 20
        
        def complete_check():
            # Simula riscaldamento
            for temp in range(20, 91, 10):
                self.resources["temperature"] = temp
                print(f"🌡️ Riscaldamento: {temp}°C")
                time.sleep(0.5)
            
            print("✅ Self check completato")
            self.change_state(MachineState.READY, "Sistema pronto")
        
        self.active_timer = threading.Timer(3, complete_check)
        self.active_timer.start()
    
    def _start_selection_timeout(self):
        """Avvia timeout selezione"""
        def timeout():
            if self.state == MachineState.ASK_BEVERAGE:  # Verifica stato prima del timeout
                print("⏰ Timeout selezione bevanda")
                self.selected_beverage = None
                self.resources["cup_present"] = False  # Considera tazza rimossa per timeout
                self.change_state(MachineState.READY, "Timeout selezione")
        
        self.active_timer = threading.Timer(self.selection_timeout, timeout)
        self.active_timer.start()
    
    def _start_production(self):
        """Avvia produzione bevanda"""
        if not self.selected_beverage:
            return
        
        beverage_info = self.beverages[self.selected_beverage]
        production_time = beverage_info["time"]
        beverage_name = self.selected_beverage  # Salva il nome prima che venga azzerato
        
        print(f"🔥 Preparazione {beverage_name} ({production_time}s)...")
        
        def complete_production():
            # Verifica che la produzione sia ancora valida
            if self.state != MachineState.PRODUCE_BEVERAGE:
                return  # Produzione interrotta
            
            # Consuma risorse
            self.resources["water_level"] -= beverage_info["water"] / 10
            self.resources["coffee_level"] -= beverage_info["coffee"]
            
            print(f"✅ {beverage_name.capitalize()} pronto!")
            self.selected_beverage = None
            
            # Pulizia automatica ogni 10 bevande
            self.resources["cleaning_cycles"] += 1
            if self.resources["cleaning_cycles"] >= 10:
                self.change_state(MachineState.SELF_CLEAN, "Pulizia automatica")
            else:
                # LOGICA CORRETTA: Controlla se la tazza è ancora presente
                if self.resources["cup_present"]:
                    print("🥤 Tazza ancora presente - Pronta per nuova selezione")
                    self.change_state(MachineState.ASK_BEVERAGE, f"{beverage_name} erogato - tazza presente")
                else:
                    print("🥤 Tazza rimossa - Ritorno a stato pronto")
                    self.change_state(MachineState.READY, f"{beverage_name} erogato - tazza rimossa")
        
        self.active_timer = threading.Timer(production_time, complete_production)
        self.active_timer.start()
    
    def _start_cleaning_cycle(self):
        """Avvia ciclo pulizia"""
        print("🧽 Ciclo di pulizia in corso...")
        
        def complete_cleaning():
            self.resources["cleaning_cycles"] = 0
            print("✅ Pulizia completata")
            self.change_state(MachineState.READY, "Pulizia terminata")
        
        self.active_timer = threading.Timer(8, complete_cleaning)
        self.active_timer.start()
    
    def _check_resources(self) -> bool:
        """Verifica disponibilità risorse"""
        return (self.resources["water_level"] >= 10 and 
                self.resources["coffee_level"] >= 5)
    
    def set_error(self, error_type: ErrorType):
        """Imposta stato di errore"""
        self._cancel_timers()
        self.error_type = error_type
        error_messages = {
            ErrorType.WATER_EMPTY: "💧 Serbatoio acqua vuoto",
            ErrorType.COFFEE_EMPTY: "☕ Serbatoio caffè vuoto", 
            ErrorType.CUP_MISSING: "🥤 Tazza mancante",
            ErrorType.SYSTEM_ERROR: "⚙️ Errore di sistema",
            ErrorType.CLEANING_ERROR: "🧽 Errore pulizia"
        }
        print(f"❌ ERRORE: {error_messages.get(error_type, 'Errore sconosciuto')}")
        self.change_state(MachineState.ERROR, error_type.value)
    
    def _cancel_timers(self):
        """Cancella timer attivi"""
        if self.active_timer and self.active_timer.is_alive():
            self.active_timer.cancel()
    
    # === COMUNICAZIONE ===
    
    def publish_mqtt(self, topic: str, message: Dict[str, Any]):
        """Pubblica messaggio MQTT"""
        try:
            self.mqtt_client.publish(topic, json.dumps(message))
        except Exception as e:
            print(f"❌ Errore pubblicazione MQTT: {e}")
    
    def publish_status(self):
        """Pubblica stato corrente"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "state": self.state.value,
            "selected_beverage": self.selected_beverage,
            "error_type": self.error_type.value if self.error_type else None,
            "resources": self.resources.copy(),
            "available_beverages": list(self.beverages.keys())
        }
        
        self.publish_mqtt(self.status_topic, status)
        
        # Salva snapshot stato
        with self.db_lock:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO state_snapshots (timestamp, state, resources)
                VALUES (?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                self.state.value,
                json.dumps(self.resources)
            ))
            self.db_conn.commit()
    
    def show_status(self):
        """Mostra stato dettagliato"""
        print(f"\n{'='*60}")
        print(f"📊 STATO: {self.state.value.upper().replace('_', ' ')}")
        
        if self.selected_beverage:
            print(f"☕ Bevanda: {self.selected_beverage}")
        
        if self.error_type:
            print(f"❌ Errore: {self.error_type.value}")
        
        print(f"💧 Acqua: {self.resources['water_level']:.0f}%")
        print(f"☕ Caffè: {self.resources['coffee_level']:.0f}%")
        print(f"🌡️ Temperatura: {self.resources['temperature']}°C")
        print(f"🥤 Tazza: {'Presente' if self.resources['cup_present'] else 'Assente'}")
        
        print(f"\n📡 Topics MQTT:")
        print(f"   Comandi: {self.command_topic}")
        print(f"   Status: {self.status_topic}")
        print(f"   Eventi: {self.events_topic}")
        print(f"{'='*60}")
    
    def cleanup(self):
        """Pulizia risorse"""
        self._cancel_timers()
        try:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.db_conn.close()
        except:
            pass

def main():
    """Funzione principale"""
    print("☕ === ENHANCED COFFEE MACHINE ===")
    print("🏗️ Event-Driven Architecture + Finite State Machine")
    
    machine = None
    try:
        machine = CoffeeMachine()
        
        print(f"\n🎮 ESEMPI COMANDI:")
        print('{"command": "turn_on"}')
        print('{"command": "place_cup"}')
        print('{"command": "select_beverage", "payload": {"beverage": "espresso"}}')
        print('{"command": "confirm_selection"}')
        print('{"command": "start_cleaning"}')
        print('{"command": "turn_off"}')
        
        print("\n⌨️ Ctrl+C per uscire")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Spegnimento...")
    finally:
        if machine:
            machine.cleanup()

if __name__ == "__main__":
    main()