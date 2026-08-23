import sys
import yaml
from scanner import Scanner

def main():
    print("\n" + "="*60)
    print("  DAPS-SIGNALS Ω X10 ULTRA  ")
    print("="*60 + "\n")

    # Cargar configuración
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Ejecutar scanner
    scanner = Scanner(config)
    signals = scanner.scan()

    # Imprimir resultados
    if not signals:
        print("No se encontraron señales operables en este momento.")
        return

    print(f"Señales encontradas: {len(signals)}\n")
    for i, signal in enumerate(signals[:10], 1):
        print(f"{i:2d}. {signal['asset']:12s} {signal['direction']:5s}  "
              f"Score: {signal['score']:.1f}%  "
              f"Entrada: {signal['entry']:.4f}  "
              f"SL: {signal['sl']:.4f}  TP: {signal['tp']:.4f}  R:R: {signal['rr']:.2f}")

if __name__ == "__main__":
    main()
