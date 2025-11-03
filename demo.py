#!/usr/bin/env python3
"""
Script de demonstração da aplicação de análise de apontamento
"""

from datetime import datetime, timedelta
from time_tracker import TimeTracker, TimeAnalyzer


def demo():
    """Executa demonstração da aplicação"""
    print("=" * 60)
    print("DEMONSTRAÇÃO - APLICAÇÃO DE ANÁLISE DE APONTAMENTO")
    print("=" * 60)
    print()
    
    # Criar tracker
    tracker = TimeTracker()
    
    # Simular alguns apontamentos
    print("1. Adicionando apontamentos...")
    base_date = datetime(2025, 11, 1, 9, 0)
    
    # Apontamento 1: Desenvolvimento - 8 horas
    tracker.add_entry(
        "Projeto A - Sistema Web",
        "Desenvolvimento de novas features",
        base_date,
        base_date + timedelta(hours=8)
    )
    print("   ✓ Apontamento #1: Projeto A - 8h")
    
    # Apontamento 2: Code Review - 2 horas
    tracker.add_entry(
        "Projeto B - API REST",
        "Revisão de código e merge requests",
        base_date,
        base_date + timedelta(hours=2)
    )
    print("   ✓ Apontamento #2: Projeto B - 2h")
    
    # Apontamento 3: Testes - 3 horas
    tracker.add_entry(
        "Projeto A - Sistema Web",
        "Testes unitários e integração",
        base_date + timedelta(days=1),
        base_date + timedelta(days=1, hours=3)
    )
    print("   ✓ Apontamento #3: Projeto A - 3h")
    
    # Apontamento 4: Documentação - 1.5 horas
    tracker.add_entry(
        "Projeto C - Mobile App",
        "Documentação técnica",
        base_date + timedelta(days=1),
        base_date + timedelta(days=1, hours=1, minutes=30)
    )
    print("   ✓ Apontamento #4: Projeto C - 1.5h")
    
    # Apontamento 5: Em andamento (sem fim)
    tracker.add_entry(
        "Projeto B - API REST",
        "Implementação de novos endpoints",
        base_date + timedelta(days=2)
    )
    print("   ✓ Apontamento #5: Projeto B - Em andamento")
    
    print()
    print("2. Calculando estatísticas...")
    total_hours = tracker.total_hours()
    print(f"   Total de horas: {total_hours:.2f}h")
    
    hours_by_project = tracker.total_hours_by_project()
    print("   Horas por projeto:")
    for project, hours in sorted(hours_by_project.items()):
        print(f"     - {project}: {hours:.2f}h")
    
    print()
    print("3. Gerando relatório completo...")
    print()
    report = TimeAnalyzer.generate_report(tracker)
    print(report)
    
    # Salvar dados
    filename = "demo_apontamentos.json"
    tracker.save_to_file(filename)
    print()
    print(f"✓ Dados salvos em {filename}")
    print()
    print("=" * 60)
    print("Demonstração concluída com sucesso!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
