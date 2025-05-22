import json
import time
import paho.mqtt.client as mqtt

class MQTTTester:
    """Client per testare la macchinetta via MQTT"""
    
    def __init__(self):
        self.broker = "test.mosquitto.org"
        self.port = 1883
        self.command_topic = "coffee_machine_demo/commands"
        self.status_topic = "coffee_machine_demo/status"
        
        # Setup MQTT
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        print("🧪 Client di test MQTT")
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()
        time.sleep(2)
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connesso al broker per test")
            client.subscribe(self.status_topic)
        else:
            print(f"❌ Connessione fallita: {rc}")
    
    def on_message(self, client, userdata, msg):
        try:
            status = json.loads(msg.payload.decode())
            print(f"📊 STATUS: {status['state']} | Drink: {status.get('selected_drink', 'None')}")
        except:
            pass
    
    def send_command(self, command, payload=None):
        """Invia comando alla macchinetta"""
        message = {
            "source": "tester",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "command": command
        }
        
        if payload:
            message["payload"] = payload
        
        self.client.publish(self.command_topic, json.dumps(message))
        print(f"📤 Comando inviato: {command}")
        time.sleep(1)
    
    def run_test_sequence(self):
        """Esegue sequenza di test"""
        print("\n🚀 INIZIO TEST AUTOMATICO:")
        
        # Test completo
        self.send_command("turn_on")
        time.sleep(2)
        
        self.send_command("select_drink", {"drink": "espresso"})
        time.sleep(2)
        
        self.send_command("brew")
        time.sleep(5)  # Aspetta preparazione
        
        self.send_command("select_drink", {"drink": "cappuccino"})
        time.sleep(2)
        
        self.send_command("brew")
        time.sleep(7)  # Aspetta preparazione cappuccino
        
        self.send_command("turn_off")
        
        print("✅ Test completato!")
    
    def interactive_mode(self):
        """Modalità interattiva"""
        print("\n🎮 MODALITÀ INTERATTIVA")
        print("Comandi: 1=ON, 2=OFF, 3=Espresso, 4=Cappuccino, 5=Americano, 6=Brew, q=Quit")
        
        while True:
            cmd = input("\n➤ Comando: ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == '1':
                self.send_command("turn_on")
            elif cmd == '2':
                self.send_command("turn_off")
            elif cmd == '3':
                self.send_command("select_drink", {"drink": "espresso"})
            elif cmd == '4':
                self.send_command("select_drink", {"drink": "cappuccino"})
            elif cmd == '5':
                self.send_command("select_drink", {"drink": "americano"})
            elif cmd == '6':
                self.send_command("brew")
            else:
                print("❌ Comando non valido")

def main():
    tester = MQTTTester()
    
    print("\nScegli modalità:")
    print("1 - Test automatico")
    print("2 - Modalità interattiva")
    
    choice = input("➤ Scelta: ").strip()
    
    if choice == '1':
        tester.run_test_sequence()
    else:
        tester.interactive_mode()
    
    tester.client.loop_stop()
    tester.client.disconnect()

if __name__ == "__main__":
    main()