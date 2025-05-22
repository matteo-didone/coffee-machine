import json
import time
import threading
from datetime import datetime
from enum import Enum
import paho.mqtt.client as mqtt

class CoffeeMachineState(Enum):
    """Stati della macchinetta del caffè"""
    OFF = "off"
    READY = "ready"
    WAITING_SELECTION = "waiting_selection"
    BREWING = "brewing"
    ERROR = "error"

class SimpleCoffeeMachine:
    """Macchinetta del caffè semplificata con MQTT"""
    
    def __init__(self):
        # Stati e configurazione
        self.current_state = CoffeeMachineState.OFF
        self.available_drinks = ["espresso", "cappuccino", "americano"]
        self.selected_drink = None
        self.error_message = None
        self.timer = None
        
        # MQTT Configuration - Broker pubblico per test
        self.mqtt_broker = "test.mosquitto.org"  # Broker pubblico
        self.mqtt_port = 1883
        
        # Topics MQTT
        self.command_topic = "coffee_machine_demo/commands"
        self.status_topic = "coffee_machine_demo/status"
        
        # Setup MQTT
        self.setup_mqtt()
        
        print("☕ Macchinetta del caffè semplificata")
        print(f"📡 Usando broker pubblico: {self.mqtt_broker}")
        print(f"📍 Stato iniziale: {self.current_state.value}")
        self.show_status()
    
    def setup_mqtt(self):
        """Setup connessione MQTT"""
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        try:
            print(f"📡 Connessione a {self.mqtt_broker}...")
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            time.sleep(2)
        except Exception as e:
            print(f"❌ Errore MQTT: {e}")
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback connessione MQTT"""
        if rc == 0:
            print("✅ Connesso al broker MQTT!")
            client.subscribe(self.command_topic)
            print(f"📥 In ascolto su: {self.command_topic}")
            self.publish_status()
        else:
            print(f"❌ Connessione fallita: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Gestisce messaggi MQTT"""
        try:
            message = json.loads(msg.payload.decode())
            print(f"\n📨 Comando ricevuto: {message}")
            self.process_command(message)
        except Exception as e:
            print(f"❌ Errore messaggio: {e}")
    
    def process_command(self, message):
        """Processa comandi JSON"""
        command = message.get("command")
        payload = message.get("payload", {})
        
        if command == "turn_on":
            self.turn_on()
        elif command == "turn_off":
            self.turn_off()
        elif command == "select_drink":
            self.select_drink(payload.get("drink"))
        elif command == "brew":
            self.start_brewing()
        else:
            print(f"❌ Comando sconosciuto: {command}")
    
    def turn_on(self):
        """Accende la macchina"""
        if self.current_state == CoffeeMachineState.OFF:
            self.change_state(CoffeeMachineState.READY)
            print("🔌 Macchina accesa e pronta!")
        else:
            print("⚠️ Macchina già accesa")
    
    def turn_off(self):
        """Spegne la macchina"""
        if self.current_state != CoffeeMachineState.OFF:
            self.cancel_timer()
            self.selected_drink = None
            self.change_state(CoffeeMachineState.OFF)
            print("🔌 Macchina spenta")
        else:
            print("⚠️ Macchina già spenta")
    
    def select_drink(self, drink):
        """Seleziona bevanda"""
        if self.current_state == CoffeeMachineState.READY:
            if drink in self.available_drinks:
                self.selected_drink = drink
                self.change_state(CoffeeMachineState.WAITING_SELECTION)
                print(f"☕ Bevanda selezionata: {drink}")
                print("✅ Invia comando 'brew' per iniziare")
            else:
                print(f"❌ Bevanda non disponibile: {drink}")
                print(f"🍹 Disponibili: {', '.join(self.available_drinks)}")
        else:
            print(f"❌ Non posso selezionare nello stato: {self.current_state.value}")
    
    def start_brewing(self):
        """Inizia preparazione"""
        if self.current_state == CoffeeMachineState.WAITING_SELECTION and self.selected_drink:
            self.change_state(CoffeeMachineState.BREWING)
            print(f"🔥 Preparazione {self.selected_drink} in corso...")
            
            # Timer per simulare preparazione
            brew_time = {"espresso": 3, "cappuccino": 5, "americano": 4}
            time_needed = brew_time.get(self.selected_drink, 3)
            
            self.timer = threading.Timer(time_needed, self.brewing_complete)
            self.timer.start()
        else:
            print("❌ Nessuna bevanda selezionata o stato non valido")
    
    def brewing_complete(self):
        """Completamento preparazione"""
        print(f"✅ {self.selected_drink.capitalize()} pronto!")
        self.selected_drink = None
        self.change_state(CoffeeMachineState.READY)
    
    def change_state(self, new_state):
        """Cambia stato"""
        old_state = self.current_state
        self.current_state = new_state
        print(f"🔄 {old_state.value} → {new_state.value}")
        self.publish_status()
        self.show_status()
    
    def cancel_timer(self):
        """Cancella timer"""
        if self.timer and self.timer.is_alive():
            self.timer.cancel()
    
    def publish_status(self):
        """Pubblica stato via MQTT"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "state": self.current_state.value,
            "selected_drink": self.selected_drink,
            "available_drinks": self.available_drinks
        }
        
        try:
            self.mqtt_client.publish(self.status_topic, json.dumps(status))
            print(f"📤 Status pubblicato")
        except Exception as e:
            print(f"❌ Errore pubblicazione: {e}")
    
    def show_status(self):
        """Mostra stato corrente"""
        print(f"\n{'='*50}")
        print(f"📊 STATO: {self.current_state.value.upper()}")
        if self.selected_drink:
            print(f"☕ Bevanda: {self.selected_drink}")
        print(f"🍹 Disponibili: {', '.join(self.available_drinks)}")
        print(f"📡 Comandi: {self.command_topic}")
        print(f"📡 Status: {self.status_topic}")
        print(f"{'='*50}")
    
    def cleanup(self):
        """Pulizia"""
        self.cancel_timer()
        try:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        except:
            pass

def main():
    """Funzione principale"""
    print("☕ === MACCHINETTA DEL CAFFÈ - VERSIONE SEMPLICE ===")
    
    machine = None
    try:
        machine = SimpleCoffeeMachine()
        
        print(f"\n🎮 ESEMPI DI COMANDI JSON:")
        print(f"Topic: {machine.command_topic}")
        print('{"source": "user1", "command": "turn_on"}')
        print('{"source": "user1", "command": "select_drink", "payload": {"drink": "espresso"}}')
        print('{"source": "user1", "command": "brew"}')
        print('{"source": "user1", "command": "turn_off"}')
        
        print(f"\n📊 Monitora status su: {machine.status_topic}")
        print("⌨️ Ctrl+C per uscire")
        
        # Mantieni in esecuzione
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Uscita...")
    finally:
        if machine:
            machine.cleanup()

if __name__ == "__main__":
    main()