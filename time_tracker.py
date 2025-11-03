"""
Aplicação de Análise de Apontamento
Time tracking and analysis application
"""

from datetime import datetime
from typing import List, Dict, Optional
import json


class TimeEntry:
    """Representa um apontamento de tempo"""
    
    def __init__(self, project: str, description: str, start_time: datetime, 
                 end_time: Optional[datetime] = None, entry_id: Optional[int] = None):
        self.id = entry_id
        self.project = project
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
    
    def complete(self, end_time: datetime):
        """Marca o apontamento como completo"""
        self.end_time = end_time
    
    def duration_hours(self) -> float:
        """Retorna a duração em horas"""
        if not self.end_time:
            return 0.0
        delta = self.end_time - self.start_time
        # Retorna 0 se end_time for anterior a start_time
        return max(0.0, delta.total_seconds() / 3600)
    
    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'project': self.project,
            'description': self.description,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TimeEntry':
        """Cria TimeEntry a partir de dicionário"""
        return cls(
            project=data['project'],
            description=data['description'],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
            entry_id=data.get('id')
        )


class TimeTracker:
    """Gerencia apontamentos de tempo"""
    
    def __init__(self):
        self.entries: List[TimeEntry] = []
        self.next_id = 1
    
    def add_entry(self, project: str, description: str, start_time: datetime, 
                  end_time: Optional[datetime] = None) -> TimeEntry:
        """Adiciona novo apontamento"""
        entry = TimeEntry(project, description, start_time, end_time, self.next_id)
        self.entries.append(entry)
        self.next_id += 1
        return entry
    
    def get_entry(self, entry_id: int) -> Optional[TimeEntry]:
        """Busca apontamento por ID"""
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None
    
    def get_all_entries(self) -> List[TimeEntry]:
        """Retorna todos os apontamentos"""
        return self.entries.copy()
    
    def get_entries_by_project(self, project: str) -> List[TimeEntry]:
        """Retorna apontamentos de um projeto específico"""
        return [entry for entry in self.entries if entry.project == project]
    
    def total_hours(self) -> float:
        """Calcula total de horas apontadas"""
        return sum(entry.duration_hours() for entry in self.entries)
    
    def total_hours_by_project(self) -> Dict[str, float]:
        """Calcula total de horas por projeto"""
        result = {}
        for entry in self.entries:
            project = entry.project
            hours = entry.duration_hours()
            result[project] = result.get(project, 0.0) + hours
        return result
    
    def save_to_file(self, filename: str):
        """Salva apontamentos em arquivo JSON"""
        data = {
            'next_id': self.next_id,
            'entries': [entry.to_dict() for entry in self.entries]
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, filename: str):
        """Carrega apontamentos de arquivo JSON"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.next_id = data.get('next_id', 1)
            self.entries = [TimeEntry.from_dict(entry_data) 
                          for entry_data in data.get('entries', [])]
        except FileNotFoundError:
            pass


class TimeAnalyzer:
    """Analisa dados de apontamentos"""
    
    @staticmethod
    def generate_report(tracker: TimeTracker) -> str:
        """Gera relatório de análise"""
        report = ["=" * 60]
        report.append("RELATÓRIO DE ANÁLISE DE APONTAMENTOS")
        report.append("=" * 60)
        report.append("")
        
        total_hours = tracker.total_hours()
        report.append(f"Total de Horas: {total_hours:.2f}h")
        report.append(f"Total de Apontamentos: {len(tracker.entries)}")
        report.append("")
        
        report.append("Horas por Projeto:")
        report.append("-" * 60)
        hours_by_project = tracker.total_hours_by_project()
        for project, hours in sorted(hours_by_project.items()):
            percentage = (hours / total_hours * 100) if total_hours > 0 else 0
            report.append(f"  {project}: {hours:.2f}h ({percentage:.1f}%)")
        
        report.append("")
        report.append("Detalhes dos Apontamentos:")
        report.append("-" * 60)
        for entry in tracker.get_all_entries():
            status = "Completo" if entry.end_time else "Em andamento"
            hours = entry.duration_hours()
            report.append(f"  ID: {entry.id} | Projeto: {entry.project}")
            report.append(f"    Descrição: {entry.description}")
            report.append(f"    Início: {entry.start_time.strftime('%Y-%m-%d %H:%M')}")
            if entry.end_time:
                report.append(f"    Fim: {entry.end_time.strftime('%Y-%m-%d %H:%M')}")
            report.append(f"    Duração: {hours:.2f}h | Status: {status}")
            report.append("")
        
        report.append("=" * 60)
        return "\n".join(report)
