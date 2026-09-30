"""
UNJu - Facultad de Ingeniería
Teoría de Sistemas Operativos (TSO) - Ciclo Lectivo 2026
Cátedra: Ing. María Fernanda Vázquez - JTP: Ing. Fabio D. Argañaraz

Ejercicio Práctico N° 4: Monitores y Variables de Condición (El Barbero Dormilón)
Bibliografía de Referencia:
- Silberschatz: Cap. 6.7 (Monitores) y Cap. 6.6 (El problema del barbero dormilón)
- Diapositivas U5: Diapositiva 20 a 24 (Monitores y Problemas Clásicos)

Fundamentos de Monitores:
Un Monitor provee exclusión mutua automática sobre sus variables internas mediante un cerrojo (Lock).
Para coordinar eventos disjuntos, utiliza Variables de Condición separadas:
1. 'cond_barbero': Para que el barbero espere a los clientes o su acomodo en el sillón.
2. 'cond_sala_espera': Para que los clientes esperen hasta que el sillón quede libre.
3. 'cond_corte': Para que el cliente en el sillón espere a que el barbero termine de cortar.
"""
import sys
import threading
import time
import random

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

class BarberiaMonitor:
    """
    Implementación del problema del Barbero Dormilón utilizando el concepto de MONITOR
    mediante variables de condición de Python (threading.Condition).
    """
    def __init__(self, num_sillas_espera=3):
        self.num_sillas = num_sillas_espera
        self.clientes_esperando = 0
        
        # Cerrojo del Monitor y sus variables de condición disjuntas
        self.lock = threading.Lock()
        self.cond_barbero = threading.Condition(self.lock)
        self.cond_sala_espera = threading.Condition(self.lock)
        self.cond_corte = threading.Condition(self.lock)
        
        self.silla_barbero_ocupada = False
        self.cliente_listo_en_sillon = False
        self.corte_terminado = False
        self.barberia_abierta = True

    def entrar_cliente(self, cliente_id):
        """
        Invocado por el hilo Cliente al llegar a la barbería.
        Retorna True si fue atendido, False si la barbería estaba llena y se marchó.
        """
        with self.lock:
            print(f"👤 Cliente {cliente_id} llega a la barbería. (Sillas ocupadas: {self.clientes_esperando}/{self.num_sillas})")
            
            # 1. Si no hay sillas libres en la sala de espera, el cliente debe irse:
            if self.clientes_esperando >= self.num_sillas:
                print(f"🚪 [SALA LLENA] Cliente {cliente_id} se va sin cortarse el pelo.")
                return False
                
            # 2. Tomar asiento en sala de espera
            self.clientes_esperando += 1
            print(f"🪑 Cliente {cliente_id} se sienta a esperar.")
            self.cond_barbero.notify() # Despertar al barbero si está durmiendo
            
            # 3. Esperar mientras la silla del barbero esté ocupada por otro
            while self.silla_barbero_ocupada:
                self.cond_sala_espera.wait()

            # 4. Pasar al sillón del barbero
            self.clientes_esperando -= 1
            self.silla_barbero_ocupada = True
            self.cliente_listo_en_sillon = True
            self.corte_terminado = False
            print(f"💈 Cliente {cliente_id} se sienta en el sillón de barbería.")
            self.cond_barbero.notify() # Avisar al barbero que ya está sentado y listo

            # 5. Esperar a que el barbero termine el corte
            while not self.corte_terminado:
                self.cond_corte.wait()

            # 6. Al terminar el corte, dejar libre el sillón
            print(f"✅ Cliente {cliente_id} se levanta del sillón y sale satisfecho.")
            self.silla_barbero_ocupada = False
            self.cliente_listo_en_sillon = False
            
            # Notificar al barbero que el sillón quedó libre y avisar a la sala de espera
            self.cond_barbero.notify()
            self.cond_sala_espera.notify()
            
            return True

    def atender_siguiente_cliente(self):
        """
        Invocado cíclicamente por el hilo Barbero.
        """
        with self.lock:
            # 1. Mientras no haya cliente listo en el sillón y la barbería esté abierta:
            while not self.cliente_listo_en_sillon and self.barberia_abierta:
                if self.clientes_esperando > 0:
                    self.cond_sala_espera.notify() # Llamar a un cliente de la sala
                print("😴 [Barbero] Esperando cliente / Durmiendo...")
                self.cond_barbero.wait()

            # 2. Si cerró la barbería y no hay nadie para atender
            if not self.barberia_abierta and not self.cliente_listo_en_sillon:
                return False

            # 3. Hay un cliente listo en el sillón
            return True

    # Alias pedagógico
    esperar_cliente_para_corte = atender_siguiente_cliente

    def finalizar_corte(self):
        """
        El barbero avisa al cliente que terminó su corte de pelo.
        """
        with self.lock:
            # 1. Marcar corte terminado y avisar al cliente
            self.corte_terminado = True
            self.cond_corte.notify()
            
            # 2. Esperar a que el cliente se levante antes de buscar otro
            while self.silla_barbero_ocupada:
                self.cond_barbero.wait()

    def cerrar_barberia(self):
        with self.lock:
            self.barberia_abierta = False
            self.cond_barbero.notify_all()
            self.cond_sala_espera.notify_all()
            self.cond_corte.notify_all()


def hilo_barbero(barberia):
    while True:
        hay_cliente = barberia.atender_siguiente_cliente()
        if not hay_cliente:
            break
        print("✂️ [Barbero] Cortando el cabello...")
        time.sleep(random.uniform(0.1, 0.25))
        barberia.finalizar_corte()

def hilo_cliente(barberia, cliente_id):
    time.sleep(random.uniform(0.05, 0.3))
    barberia.entrar_cliente(cliente_id)

if __name__ == "__main__":
    print("=" * 60)
    print(" Barbería con Monitores y Variables de Condición (UNJu FI)")
    print("=" * 60)
    
    barberia = BarberiaMonitor(num_sillas_espera=3)
    
    t_barbero = threading.Thread(target=hilo_barbero, args=(barberia,), name="Barbero")
    t_barbero.start()
    
    # Llegan 8 clientes de manera concurrente
    clientes = []
    for i in range(1, 9):
        t_cli = threading.Thread(target=hilo_cliente, args=(barberia, i), name=f"Cliente-{i}")
        clientes.append(t_cli)
        t_cli.start()
        
    for t_cli in clientes:
        t_cli.join()
        
    time.sleep(0.5)
    barberia.cerrar_barberia()
    t_barbero.join()
    
    print("=" * 60)
    print(" Simulación de Barbería finalizada.")
    print("=" * 60)