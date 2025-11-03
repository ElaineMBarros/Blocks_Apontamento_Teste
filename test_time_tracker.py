"""
Testes para aplicação de análise de apontamento
"""

import pytest
from datetime import datetime, timedelta
from time_tracker import TimeEntry, TimeTracker, TimeAnalyzer


class TestTimeEntry:
    """Testes para classe TimeEntry"""
    
    def test_create_entry(self):
        """Testa criação de apontamento"""
        start = datetime(2025, 11, 1, 9, 0)
        entry = TimeEntry("Projeto A", "Desenvolvimento", start)
        
        assert entry.project == "Projeto A"
        assert entry.description == "Desenvolvimento"
        assert entry.start_time == start
        assert entry.end_time is None
    
    def test_complete_entry(self):
        """Testa completar apontamento"""
        start = datetime(2025, 11, 1, 9, 0)
        end = datetime(2025, 11, 1, 17, 0)
        entry = TimeEntry("Projeto A", "Desenvolvimento", start)
        
        entry.complete(end)
        assert entry.end_time == end
    
    def test_duration_hours(self):
        """Testa cálculo de duração"""
        start = datetime(2025, 11, 1, 9, 0)
        end = datetime(2025, 11, 1, 17, 0)
        entry = TimeEntry("Projeto A", "Desenvolvimento", start, end)
        
        assert entry.duration_hours() == 8.0
    
    def test_duration_hours_incomplete(self):
        """Testa duração de apontamento incompleto"""
        start = datetime(2025, 11, 1, 9, 0)
        entry = TimeEntry("Projeto A", "Desenvolvimento", start)
        
        assert entry.duration_hours() == 0.0
    
    def test_duration_hours_negative(self):
        """Testa duração quando end_time é anterior a start_time"""
        start = datetime(2025, 11, 1, 17, 0)
        end = datetime(2025, 11, 1, 9, 0)
        entry = TimeEntry("Projeto A", "Desenvolvimento", start, end)
        
        # Deve retornar 0 ao invés de valor negativo
        assert entry.duration_hours() == 0.0
    
    def test_to_dict(self):
        """Testa conversão para dicionário"""
        start = datetime(2025, 11, 1, 9, 0)
        end = datetime(2025, 11, 1, 17, 0)
        entry = TimeEntry("Projeto A", "Desenvolvimento", start, end, entry_id=1)
        
        data = entry.to_dict()
        assert data['id'] == 1
        assert data['project'] == "Projeto A"
        assert data['description'] == "Desenvolvimento"
        assert data['start_time'] == start.isoformat()
        assert data['end_time'] == end.isoformat()
    
    def test_from_dict(self):
        """Testa criação a partir de dicionário"""
        data = {
            'id': 1,
            'project': "Projeto A",
            'description': "Desenvolvimento",
            'start_time': "2025-11-01T09:00:00",
            'end_time': "2025-11-01T17:00:00"
        }
        
        entry = TimeEntry.from_dict(data)
        assert entry.id == 1
        assert entry.project == "Projeto A"
        assert entry.description == "Desenvolvimento"
        assert entry.start_time == datetime(2025, 11, 1, 9, 0)
        assert entry.end_time == datetime(2025, 11, 1, 17, 0)


class TestTimeTracker:
    """Testes para classe TimeTracker"""
    
    def test_add_entry(self):
        """Testa adicionar apontamento"""
        tracker = TimeTracker()
        start = datetime(2025, 11, 1, 9, 0)
        
        entry = tracker.add_entry("Projeto A", "Desenvolvimento", start)
        
        assert entry.id == 1
        assert len(tracker.entries) == 1
        assert tracker.next_id == 2
    
    def test_get_entry(self):
        """Testa buscar apontamento por ID"""
        tracker = TimeTracker()
        start = datetime(2025, 11, 1, 9, 0)
        
        entry1 = tracker.add_entry("Projeto A", "Desenvolvimento", start)
        entry2 = tracker.get_entry(1)
        
        assert entry1 == entry2
    
    def test_get_entry_not_found(self):
        """Testa buscar apontamento inexistente"""
        tracker = TimeTracker()
        
        entry = tracker.get_entry(999)
        assert entry is None
    
    def test_get_all_entries(self):
        """Testa listar todos os apontamentos"""
        tracker = TimeTracker()
        start = datetime(2025, 11, 1, 9, 0)
        
        tracker.add_entry("Projeto A", "Desenvolvimento", start)
        tracker.add_entry("Projeto B", "Testes", start)
        
        entries = tracker.get_all_entries()
        assert len(entries) == 2
    
    def test_get_entries_by_project(self):
        """Testa filtrar apontamentos por projeto"""
        tracker = TimeTracker()
        start = datetime(2025, 11, 1, 9, 0)
        
        tracker.add_entry("Projeto A", "Desenvolvimento", start)
        tracker.add_entry("Projeto B", "Testes", start)
        tracker.add_entry("Projeto A", "Revisão", start)
        
        entries_a = tracker.get_entries_by_project("Projeto A")
        assert len(entries_a) == 2
        
        entries_b = tracker.get_entries_by_project("Projeto B")
        assert len(entries_b) == 1
    
    def test_total_hours(self):
        """Testa cálculo de horas totais"""
        tracker = TimeTracker()
        start = datetime(2025, 11, 1, 9, 0)
        end = datetime(2025, 11, 1, 17, 0)
        
        tracker.add_entry("Projeto A", "Desenvolvimento", start, end)
        tracker.add_entry("Projeto B", "Testes", start, start + timedelta(hours=2))
        
        assert tracker.total_hours() == 10.0
    
    def test_total_hours_by_project(self):
        """Testa cálculo de horas por projeto"""
        tracker = TimeTracker()
        start = datetime(2025, 11, 1, 9, 0)
        
        tracker.add_entry("Projeto A", "Desenvolvimento", start, start + timedelta(hours=8))
        tracker.add_entry("Projeto B", "Testes", start, start + timedelta(hours=2))
        tracker.add_entry("Projeto A", "Revisão", start, start + timedelta(hours=3))
        
        hours_by_project = tracker.total_hours_by_project()
        assert hours_by_project["Projeto A"] == 11.0
        assert hours_by_project["Projeto B"] == 2.0
    
    def test_save_and_load(self, tmp_path):
        """Testa salvar e carregar dados"""
        filename = tmp_path / "test_data.json"
        
        # Criar e salvar dados
        tracker1 = TimeTracker()
        start = datetime(2025, 11, 1, 9, 0)
        end = datetime(2025, 11, 1, 17, 0)
        tracker1.add_entry("Projeto A", "Desenvolvimento", start, end)
        tracker1.add_entry("Projeto B", "Testes", start, start + timedelta(hours=2))
        tracker1.save_to_file(str(filename))
        
        # Carregar dados
        tracker2 = TimeTracker()
        tracker2.load_from_file(str(filename))
        
        assert len(tracker2.entries) == 2
        assert tracker2.next_id == 3
        assert tracker2.entries[0].project == "Projeto A"
        assert tracker2.entries[1].project == "Projeto B"
    
    def test_load_nonexistent_file(self):
        """Testa carregar arquivo inexistente"""
        tracker = TimeTracker()
        tracker.load_from_file("nonexistent_file.json")
        
        assert len(tracker.entries) == 0
        assert tracker.next_id == 1


class TestTimeAnalyzer:
    """Testes para classe TimeAnalyzer"""
    
    def test_generate_report(self):
        """Testa geração de relatório"""
        tracker = TimeTracker()
        start = datetime(2025, 11, 1, 9, 0)
        end = datetime(2025, 11, 1, 17, 0)
        
        tracker.add_entry("Projeto A", "Desenvolvimento", start, end)
        tracker.add_entry("Projeto B", "Testes", start, start + timedelta(hours=2))
        
        report = TimeAnalyzer.generate_report(tracker)
        
        assert "RELATÓRIO DE ANÁLISE DE APONTAMENTOS" in report
        assert "Total de Horas: 10.00h" in report
        assert "Total de Apontamentos: 2" in report
        assert "Projeto A: 8.00h" in report
        assert "Projeto B: 2.00h" in report
    
    def test_generate_report_empty(self):
        """Testa geração de relatório sem dados"""
        tracker = TimeTracker()
        report = TimeAnalyzer.generate_report(tracker)
        
        assert "RELATÓRIO DE ANÁLISE DE APONTAMENTOS" in report
        assert "Total de Horas: 0.00h" in report
        assert "Total de Apontamentos: 0" in report
