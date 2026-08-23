#!/usr/bin/env python3
"""
DAPS-SIGNALS Ω X10 ULTRA — Ejecución en consola con ranking completo y contador
"""

import sys
import time
import os
import yaml
from scanner import Scanner

def cargar_config():
    if os.path.exists("config.yaml"):
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    else:
        # Configuración por defecto
        return {
            "universe": {"max_assets": 25, "min_volume_usdt": 5000000},
            "scoring": {"thresholds": {"strong": 0.70, "good": 0.50, "weak": 0.30}},
            "risk": {"sl_multiplier": 1.0, "tp_multiplier": 2.5,
                     "trailing_activation": 0.5, "trailing_distance": 1.0, "max_leverage": 1.5},
            "backtest": {"walk_forward_train": 180, "walk_forward_test": 30,
                         "walk_forward_step": 15, "monte_carlo_sims": 5000},
            "streamlit": {"refresh_seconds": 300}
        }

def imprimir_ranking(signals, scanner):
    if not signals:
        print("\n🔍 No se encontraron señales.")
        return

    # Top LONG y SHORT
    top_long = scanner.get_top_long()
    top_short = scanner.get_top_short()

    print("\n" + "="*80)
    print("  🏆 TOP 1 LONG")
    if top_long:
        print(f"  Activo: {top_long['asset']}")
        print(f"  Score: {top_long['score']:.1f}%")
        print(f"  Entrada: ${top_long['entry']:.4f}")
        print(f"  SL: ${top_long['sl']:.4f}  |  TP: ${top_long['tp']:.4f}  |  R:R: {top_long['rr']:.2f}")
        print(f"  Trailing activación: ${top_long['trailing_activation']:.4f}  |  Distancia: ${top_long['trailing_distance']:.4f}")
        print(f"  Tiempo estimado: {top_long['time_to_entry']}")
        print(f"  Razones: {', '.join(top_long['reasons'])}")
    else:
        print("  No hay señales LONG")

    print("\n" + "="*80)
    print("  🏆 TOP 1 SHORT")
    if top_short:
        print(f"  Activo: {top_short['asset']}")
        print(f"  Score: {top_short['score']:.1f}%")
        print(f"  Entrada: ${top_short['entry']:.4f}")
        print(f"  SL: ${top_short['sl']:.4f}  |  TP: ${top_short['tp']:.4f}  |  R:R: {top_short['rr']:.2f}")
        print(f"  Trailing activación: ${top_short['trailing_activation']:.4f}  |  Distancia: ${top_short['trailing_distance']:.4f}")
        print(f"  Tiempo estimado: {top_short['time_to_entry']}")
        print(f"  Razones: {', '.join(top_short['reasons'])}")
    else:
        print("  No hay señales SHORT")

    # Ranking completo
    print("\n" + "="*80)
    print("  📋 RANKING COMPLETO")
    print("-"*80)
    print(f"{'#':<3} {'Activo':<12} {'Dir':<5} {'Score':<6} {'Entrada':<10} {'SL':<10} {'TP':<10} {'R:R':<6} {'Tiempo estimado':<20}")
    print("-"*80)
    for i, s in enumerate(signals[:20], 1):
        print(f"{i:<3} {s['asset']:<12} {s['direction']:<5} {s['score']:<6.1f} "
              f"{s['entry']:<10.4f} {s['sl']:<10.4f} {s['tp']:<10.4f} "
              f"{s['rr']:<6.2f} {s['time_to_entry']:<20}")
    if len(signals) > 20:
        print(f"... y {len(signals)-20} activos más")

def main():
    print("\n" + "="*60)
    print("  DAPS-SIGNALS Ω X10 ULTRA  ")
    print("  Escaneo automático cada 5 minutos")
    print("="*60 + "\n")

    config = cargar_config()
    scanner = Scanner(config)

    while True:
        print(f"\n🔄 Escaneando... ({time.strftime('%H:%M:%S')})")
        signals = scanner.scan_all()
        imprimir_ranking(signals, scanner)

        # Contador regresivo
        for i in range(300, 0, -10):
            print(f"\r⏳ Próximo escaneo en {i//60}m {i%60}s", end="", flush=True)
            time.sleep(10)
        print("\r" + " "*50 + "\r", end="")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Escáner detenido por el usuario.")
