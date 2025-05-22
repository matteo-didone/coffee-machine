#!/usr/bin/env python3
"""
Enhanced Test Client per Coffee Machine
Test completo di tutti gli stati e scenari
"""

import json
import time
import threading
import paho.mqtt.client as mqtt

class EnhancedTester:
    """Client di test avanzato per la macchinetta"""
    
    def __init__(self):
        self.broker = "localhost"
        self.port = 1883
        self.base_topic = "enhanced_coffee_machine"
        self.command_topic = f"{self.base_topic}/commands"
        self.status_topic = f"{self.base_topic}/status"
        self.events_topic = f"{self.base_topic}/events"
        
        self.current_state = "unknown"
        self.resources = {}
        
        # Setup MQTT
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        print("🧪 Enhanced Coffee Machine Tester")
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()
        time.sleep(2)
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connesso al broker MQTT")
            client.subscribe(self.status_topic)
            client.subscribe(self.events_topic)
        else:
            print(f"❌ Connessione fallita: {rc}")
    
    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            
            if msg.topic == self.status_topic:
                self.current_state = data.get('state', 'unknown')
                self.resources = data.get('resources', {})
                print(f"📊 STATUS: {self.current_state} | "
                      f"Water: {self.resources.get('water_level', 0):.0f}% | "
                      f"Coffee: {self.resources.get('coffee_level', 0):.0f}%")
            
            elif msg.topic == self.events_topic:
                event = data.get('event', 'unknown')
                print(f"📣 EVENT: {event}")
                
        except Exception as e:
            print(f"❌ Errore messaggio: {e}")
    
    def send_command(self, command: str, payload: dict = None, delay: float = 1.5):
        """Invia comando con payload opzionale"""
        message = {
            "source": "enhanced_tester",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "command": command
        }
        
        if payload:
            message["payload"] = payload
        
        self.client.publish(self.command_topic, json.dumps(message))
        print(f"📤 Comando: {command}" + (f" ({payload})" if payload else ""))
        time.sleep(delay)
    
    def wait_for_state(self, expected_state: str, timeout: int = 10):
        """Aspetta che la macchina raggiunga uno stato specifico"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.current_state == expected_state:
                return True
            time.sleep(0.5)
        print(f"⏰ Timeout aspettando stato: {expected_state}")
        return False
    
    def test_full_cycle(self):
        """Test del ciclo completo"""
        print("\n🚀 === TEST CICLO COMPLETO ===")
        
        # 1. Accensione e self check
        print("\n1️⃣ Accensione...")
        self.send_command("turn_on")
        self.wait_for_state("ready", 10)
        
        # 2. Posizionamento tazza
        print("\n2️⃣ Posizionamento tazza...")
        self.send_command("place_cup")
        self.wait_for_state("ask_beverage")
        
        # 3. Selezione bevanda
        print("\n3️⃣ Selezione espresso...")
        self.send_command("select_beverage", {"beverage": "espresso"})
        time.sleep(1)
        
        # 4. Conferma selezione
        print("\n4️⃣ Conferma selezione...")
        self.send_command("confirm_selection")
        # Dopo produzione, con tazza presente, dovrebbe tornare ad ASK_BEVERAGE
        self.wait_for_state("ask_beverage", 8)
        
        # 5. Seconda bevanda (cappuccino) - tazza già presente
        print("\n5️⃣ Seconda bevanda (cappuccino) - workflow consecutivo...")
        self.send_command("select_beverage", {"beverage": "cappuccino"})
        time.sleep(1)
        self.send_command("confirm_selection")
        # Ancora ASK_BEVERAGE con tazza presente
        self.wait_for_state("ask_beverage", 10)
        
        # 6. Rimozione tazza (ora dovrebbe tornare a READY)
        print("\n6️⃣ Rimozione tazza...")
        self.send_command("remove_cup")
        self.wait_for_state("ready", 2)
        
        # 7. Spegnimento
        print("\n7️⃣ Spegnimento...")
        self.send_command("turn_off")
        self.wait_for_state("off", 2)
        
        print("\n✅ Test ciclo completo terminato!")
    
    def test_cleaning_cycle(self):
        """Test ciclo di pulizia"""
        print("\n🧽 === TEST PULIZIA ===")
        
        self.send_command("turn_on")
        self.wait_for_state("ready", 10)
        
        print("\n🧽 Avvio pulizia manuale...")
        self.send_command("start_cleaning")
        self.wait_for_state("ready", 15)
        
        print("\n✅ Test pulizia completato!")
    
    def test_error_scenarios(self):
        """Test scenari di errore"""
        print("\n❌ === TEST SCENARI ERRORE ===")
        
        self.send_command("turn_on")
        self.wait_for_state("ready", 10)
        
        # Test 1: Rimozione tazza durante produzione
        print("\n💥 Test 1: Rimozione tazza durante produzione...")
        self.send_command("place_cup")
        self.wait_for_state("ask_beverage", 2)
        self.send_command("select_beverage", {"beverage": "espresso"})
        time.sleep(1)
        self.send_command("confirm_selection")
        # Rimuovi tazza durante produzione
        time.sleep(1)  # Aspetta che inizi la produzione
        self.send_command("remove_cup", delay=0.5)
        self.wait_for_state("error", 5)
        
        # Reset errore
        print("\n🔄 Reset errore...")
        self.send_command("reset_error")
        self.wait_for_state("ready", 2)
        
        # Test 2: Comandi errati in stati sbagliati
        print("\n💥 Test 2: Comandi errati...")
        # Prova a posizionare tazza due volte
        self.send_command("place_cup")
        self.send_command("place_cup")  # Dovrebbe dare warning
        
        print("\n✅ Test errori completato!")
    
    def test_multiple_beverages(self):
        """Test produzione multipla per trigger pulizia automatica"""
        print("\n☕ === TEST PRODUZIONE MULTIPLA ===")
        
        self.send_command("turn_on")
        self.wait_for_state("ready", 10)
        
        beverages = ["espresso", "cappuccino", "americano"]
        
        # Test con workflow consecutivo (senza rimuovere tazza)
        print("\n🔄 Workflow consecutivo con tazza fissa...")
        self.send_command("place_cup")
        self.wait_for_state("ask_beverage")
        
        for i in range(3):  # 3 bevande consecutive
            print(f"\n☕ Bevanda consecutiva {i+1}/3: {beverages[i % len(beverages)]}")
            
            self.send_command("select_beverage", {"beverage": beverages[i % len(beverages)]})
            time.sleep(1)
            
            self.send_command("confirm_selection")
            # Dovrebbe tornare ad ASK_BEVERAGE (tazza presente)
            self.wait_for_state("ask_beverage", 10)
        
        # Rimuovi tazza alla fine
        print("\n🥤 Rimozione tazza finale...")
        self.send_command("remove_cup")
        self.wait_for_state("ready", 2)
        
        print("\n✅ Test produzione multipla completato!")
    
    def test_automatic_cleaning(self):
        """Test pulizia automatica dopo 10 bevande"""
        print("\n🧽 === TEST PULIZIA AUTOMATICA (10 bevande) ===")
        
        self.send_command("turn_on")
        self.wait_for_state("ready", 10)
        
        print("\n🔄 Produzione 10 bevande per trigger pulizia automatica...")
        self.send_command("place_cup")
        self.wait_for_state("ask_beverage")
        
        # Produci 10 bevande consecutive
        for i in range(10):
            beverage = ["espresso", "cappuccino", "americano"][i % 3]
            print(f"\n☕ Bevanda {i+1}/10: {beverage}")
            
            self.send_command("select_beverage", {"beverage": beverage}, delay=0.5)
            self.send_command("confirm_selection", delay=0.5)
            
            if i < 9:  # Non aspettare ASK_BEVERAGE per l'ultima
                self.wait_for_state("ask_beverage", 8)
            else:
                # La 10a dovrebbe triggerare pulizia automatica
                print("🧽 Attesa pulizia automatica...")
                self.wait_for_state("self_clean", 8)
                self.wait_for_state("ready", 15)  # Aspetta fine pulizia
        
        print("\n✅ Test pulizia automatica completato!")
    
    def interactive_mode(self):
        """Modalità interattiva avanzata"""
        print("\n🎮 === MODALITÀ INTERATTIVA AVANZATA ===")
        print("Comandi disponibili:")
        print("1=ON, 2=OFF, 3=Tazza, 4=Rimuovi Tazza")
        print("5=Espresso, 6=Cappuccino, 7=Americano, 8=Conferma")
        print("9=Pulizia, 0=Reset Errore, w=Riempi Acqua, c=Riempi Caffè")
        print("s=Status, q=Quit")
        
        while True:
            cmd = input(f"\n[{self.current_state}] ➤ ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == '1':
                self.send_command("turn_on", delay=0.5)
            elif cmd == '2':
                self.send_command("turn_off", delay=0.5)
            elif cmd == '3':
                self.send_command("place_cup", delay=0.5)
            elif cmd == '4':
                self.send_command("remove_cup", delay=0.5)
            elif cmd == '5':
                self.send_command("select_beverage", {"beverage": "espresso"}, delay=0.5)
            elif cmd == '6':
                self.send_command("select_beverage", {"beverage": "cappuccino"}, delay=0.5)
            elif cmd == '7':
                self.send_command("select_beverage", {"beverage": "americano"}, delay=0.5)
            elif cmd == '8':
                self.send_command("confirm_selection", delay=0.5)
            elif cmd == '9':
                self.send_command("start_cleaning", delay=0.5)
            elif cmd == '0':
                self.send_command("reset_error", delay=0.5)
            elif cmd == 'w':
                self.send_command("refill_water", delay=0.5)
            elif cmd == 'c':
                self.send_command("refill_coffee", delay=0.5)
            elif cmd == 's':
                print(f"📊 Stato attuale: {self.current_state}")
                print(f"💧 Risorse: {self.resources}")
            else:
                print("❌ Comando non valido")
    
    def run_all_tests(self):
        """Esegue tutti i test in sequenza"""
        print("\n🧪 === ESECUZIONE TUTTI I TEST ===")
        
        tests = [
            ("Ciclo Completo", self.test_full_cycle),
            ("Ciclo Pulizia", self.test_cleaning_cycle),
            ("Scenari Errore", self.test_error_scenarios),
            ("Produzione Multipla", self.test_multiple_beverages),
            ("Pulizia Automatica", self.test_automatic_cleaning)
        ]
        
        for test_name, test_func in tests:
            print(f"\n{'='*50}")
            print(f"🔬 Avvio test: {test_name}")
            print(f"{'='*50}")
            
            try:
                test_func()
                print(f"✅ Test '{test_name}' completato con successo")
            except Exception as e:
                print(f"❌ Test '{test_name}' fallito: {e}")
            
            # Spegni la macchina tra i test
            time.sleep(2)
            self.send_command("turn_off", delay=0.5)
            time.sleep(3)
        
        print(f"\n🏆 Tutti i test completati!")

def main():
    """Funzione principale del tester"""
    tester = EnhancedTester()
    
    print("\n🧪 Enhanced Coffee Machine Tester")
    print("Scegli modalità di test:")
    print("1 - Test ciclo completo")
    print("2 - Test pulizia")
    print("3 - Test scenari errore")
    print("4 - Test produzione multipla")
    print("5 - Test pulizia automatica (10 bevande)")
    print("6 - Tutti i test automatici")
    print("7 - Modalità interattiva")
    
    choice = input("➤ Scelta: ").strip()
    
    try:
        if choice == '1':
            tester.test_full_cycle()
        elif choice == '2':
            tester.test_cleaning_cycle()
        elif choice == '3':
            tester.test_error_scenarios()
        elif choice == '4':
            tester.test_multiple_beverages()
        elif choice == '5':
            tester.test_automatic_cleaning()
        elif choice == '6':
            tester.run_all_tests()
        elif choice == '7':
            tester.interactive_mode()
        else:
            print("❌ Scelta non valida")
    
    except KeyboardInterrupt:
        print("\n👋 Test interrotto")
    finally:
        tester.client.loop_stop()
        tester.client.disconnect()

if __name__ == "__main__":
    main()