#!/usr/bin/env python3
"""
CLI para aplicação de análise de apontamento
"""

from datetime import datetime
from time_tracker import TimeTracker, TimeAnalyzer


def print_menu():
    """Exibe menu principal"""
    print("\n" + "=" * 60)
    print("APLICAÇÃO DE ANÁLISE DE APONTAMENTO")
    print("=" * 60)
    print("1. Adicionar novo apontamento")
    print("2. Completar apontamento")
    print("3. Listar apontamentos")
    print("4. Gerar relatório de análise")
    print("5. Salvar dados")
    print("6. Sair")
    print("=" * 60)


def get_datetime_input(prompt: str) -> datetime:
    """Solicita entrada de data/hora"""
    while True:
        try:
            date_str = input(f"{prompt} (formato: YYYY-MM-DD HH:MM): ")
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except ValueError:
            print("Formato inválido. Use: YYYY-MM-DD HH:MM")


def add_entry(tracker: TimeTracker):
    """Adiciona novo apontamento"""
    print("\n--- Adicionar Novo Apontamento ---")
    project = input("Nome do projeto: ")
    description = input("Descrição: ")
    start_time = get_datetime_input("Data/hora de início")
    
    complete = input("Apontamento já está completo? (s/n): ").lower()
    end_time = None
    if complete == 's':
        end_time = get_datetime_input("Data/hora de término")
    
    entry = tracker.add_entry(project, description, start_time, end_time)
    print(f"✓ Apontamento #{entry.id} adicionado com sucesso!")


def complete_entry(tracker: TimeTracker):
    """Completa um apontamento existente"""
    print("\n--- Completar Apontamento ---")
    try:
        entry_id = int(input("ID do apontamento: "))
        entry = tracker.get_entry(entry_id)
        
        if not entry:
            print(f"✗ Apontamento #{entry_id} não encontrado!")
            return
        
        if entry.end_time:
            print(f"✗ Apontamento #{entry_id} já está completo!")
            return
        
        end_time = get_datetime_input("Data/hora de término")
        entry.complete(end_time)
        print(f"✓ Apontamento #{entry_id} completado! Duração: {entry.duration_hours():.2f}h")
    except ValueError:
        print("✗ ID inválido!")


def list_entries(tracker: TimeTracker):
    """Lista todos os apontamentos"""
    print("\n--- Lista de Apontamentos ---")
    entries = tracker.get_all_entries()
    
    if not entries:
        print("Nenhum apontamento registrado.")
        return
    
    for entry in entries:
        status = "✓ Completo" if entry.end_time else "⏳ Em andamento"
        hours = entry.duration_hours()
        print(f"\nID: {entry.id} | {status}")
        print(f"  Projeto: {entry.project}")
        print(f"  Descrição: {entry.description}")
        print(f"  Início: {entry.start_time.strftime('%Y-%m-%d %H:%M')}")
        if entry.end_time:
            print(f"  Fim: {entry.end_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"  Duração: {hours:.2f}h")


def generate_report(tracker: TimeTracker):
    """Gera e exibe relatório de análise"""
    print("\n")
    report = TimeAnalyzer.generate_report(tracker)
    print(report)


def main():
    """Função principal"""
    tracker = TimeTracker()
    data_file = "apontamentos.json"
    
    # Tenta carregar dados existentes
    tracker.load_from_file(data_file)
    print(f"✓ Dados carregados de {data_file}")
    
    while True:
        print_menu()
        choice = input("\nEscolha uma opção: ")
        
        if choice == '1':
            add_entry(tracker)
        elif choice == '2':
            complete_entry(tracker)
        elif choice == '3':
            list_entries(tracker)
        elif choice == '4':
            generate_report(tracker)
        elif choice == '5':
            tracker.save_to_file(data_file)
            print(f"✓ Dados salvos em {data_file}")
        elif choice == '6':
            # Salva automaticamente ao sair
            tracker.save_to_file(data_file)
            print(f"\n✓ Dados salvos. Até logo!")
            break
        else:
            print("✗ Opção inválida!")


if __name__ == "__main__":
    main()
