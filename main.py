#!/usr/bin/env python3
"""
DAPS-SIGNALS Ω X10 ULTRA — Punto de entrada principal
Ejecuta el escáner y genera señales en consola.
"""

import sys
import os
import yaml
from scanner import Scanner

def main():
    print("\n" + "="*60)
    print("  DAPS-SIGNALS Ω X10 ULTRA  ")
    print("="*60 + "\n")

    # Verificar que config.yaml existe
    if not os.path.exists("config.yaml"):
        print("❌ ERROR: Archivo config.yaml no encontrado.")
        print("   Debes crear config.yaml con la configuración del sistema.")
        return

    # Cargar configuración
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        print("✅ Configuración cargada correctamente.")
    except yaml.YAMLError as e:
        print(f"❌ Error en config.yaml: {e}")
        return

    # Ejecutar scanner
    scanner = Scanner(config)
    signals = scanner.scan()

    # Imprimir resultados
    if not signals:
        print("\n🔍 No se encontraron señales operables en este momento.")
        return

    print(f"\n📊 Señales encontradas: {len(signals)}\n")
    print("-" * 80)
    for i, signal in enumerate(signals[:10], 1):
        print(f"{i:2d}. {signal['asset']:12s} {signal['direction']:5s}  "
              f"Score: {signal['score']:.1f}%  "
              f"Entrada: {signal['entry']:.4f}  "
              f"SL: {signal['sl']:.4f}  TP: {signal['tp']:.4f}  R:R: {signal['rr']:.2f}")
    print("-" * 80)

if __name__ == "__main__":
    main()
