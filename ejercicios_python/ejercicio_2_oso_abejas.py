"""
UNJu - Facultad de Ingeniería
Teoría de Sistemas Operativos (TSO) - Ciclo Lectivo 2026
Cátedra: Ing. María Fernanda Vázquez - JTP: Ing. Fabio D. Argañaraz

Ejercicio Práctico N° 2: El Problema del Oso y las Abejas
Bibliografía de Referencia:
- Silberschatz: Cap. 6.6 (Problemas clásicos de sincronización)
- Stallings: Cap. 5.4 (Sincronización con semáforos)
"""

import sys
import threading
import time
import random

# Configuración UTF-8 para consola Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

M = 10                  # Capacidad del tarro de miel
NUM_ABEJAS = 5          # Número de abejas obreras
tarro_miel = 0          # Variable compartida
simulacion_activa = True

# TODO PARA EL ESTUDIANTE:
# 1. Define los mecanismos de sincronización necesarios:
# - Un cerrojo (Lock) o semáforo binario para exclusión mutua en el tarro.
# - Un semáforo para despertar al oso cuando el tarro esté lleno.
# - Un semáforo para que las abejas esperen si el tarro está lleno o el oso está comiendo.
# mutex = threading.Lock()
# sem_oso = threading.Semaphore(0)
# sem_tarro_disponible = threading.Semaphore(1)
# Mecanismos de sincronización
mutex = threading.Lock()                     # Protege el acceso concurrente a tarro_miel
sem_oso = threading.Semaphore(0)             # Despierta al oso cuando el tarro está lleno (M porciones)
sem_tarro_disponible = threading.Semaphore(1)# Permite a las abejas producir solo si el tarro no está lleno

def abeja(id_abeja):
    global tarro_miel, simulacion_activa
    while simulacion_activa:
        time.sleep(random.uniform(0.05, 0.2))
        
        # 1. Verificar si el tarro está disponible para producir
        sem_tarro_disponible.acquire()
        if not simulacion_activa:
            # Liberar si la simulación terminó mientras esperábamos
            sem_tarro_disponible.release()
            break

        # 2. Exclusión mutua para modificar la variable compartida
        with mutex:
            tarro_miel += 1
            print(f"🐝 Abeja [{id_abeja}] aportó miel -> Porciones en el tarro: {tarro_miel}/{M}")
            
            # 3. Si el tarro se llenó, avisar al oso
            if tarro_miel == M:
                print(f"🚨 Abeja [{id_abeja}]: ¡El tarro está lleno! Despertando al oso 🐻💤...")
                sem_oso.release()
                # NOTA: No liberamos sem_tarro_disponible aquí; las abejas se quedan
                # bloqueadas hasta que el oso coma y libere el tarro nuevamente.
            else:
                # Si aún no está lleno, otra abeja puede seguir aportando miel
                sem_tarro_disponible.release()

def oso(max_tarros=2):
    global tarro_miel, simulacion_activa
    tarros_comidos = 0
    while tarros_comidos < max_tarros and simulacion_activa:
        # 1. El oso duerme en espera pasiva hasta que una abeja lo despierte
        sem_oso.acquire()
        
        if not simulacion_activa:
            break

        # 2. Comerse toda la miel del tarro
        print(f"\n🐻 Oso se despierta y se come las {tarro_miel} porciones de miel! 🍯😋")
        time.sleep(0.3)  # Tiempo simulado que tarda en comer
        tarro_miel = 0
        tarros_comidos += 1
        print(f"🐻 Oso volvió a dormir. Tarros comidos: {tarros_comidos}/{max_tarros}\n")

        # 3. Habilitar el tarro para que las abejas puedan volver a producir
        sem_tarro_disponible.release()

    # Finalizar simulación tras completar las rondas del oso
    simulacion_activa = False
    print("🏁 Simulación finalizada. Liberando hilos...")
    
    # Desbloquear abejas que puedan haber quedado esperando
    sem_tarro_disponible.release()

if __name__ == "__main__":
    print("=" * 60)
    print(" Iniciando Simulación: El Oso y las Abejas (UNJu FI)")
    print("=" * 60)
    
    # Crear e iniciar el hilo del Oso
    hilo_oso = threading.Thread(target=oso, args=(2,))
    hilo_oso.start()

    # Crear e iniciar los hilos de las N Abejas
    hilos_abejas = []
    for i in range(NUM_ABEJAS):
        t = threading.Thread(target=abeja, args=(i + 1,))
        hilos_abejas.append(t)
        t.start()

    # Esperar la finalización del Oso y las Abejas
    hilo_oso.join()
    for t in hilos_abejas:
        t.join()

    print("=" * 60)
    print(" FIN DE LA EJECUCIÓN DEL PROGRAMA")
    print("=" * 60)