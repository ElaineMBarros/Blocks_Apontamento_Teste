# Blocks_Apontamento_Teste
Aplicação de Análise de Apontamento - Teste

## Descrição

Sistema de análise e gerenciamento de apontamentos de tempo para projetos. Permite registrar, acompanhar e analisar o tempo dedicado a diferentes projetos e tarefas.

## Funcionalidades

- ✅ Adicionar apontamentos de tempo com projeto, descrição, início e fim
- ✅ Completar apontamentos em andamento
- ✅ Listar todos os apontamentos
- ✅ Gerar relatórios de análise
- ✅ Calcular horas totais e por projeto
- ✅ Persistência de dados em JSON
- ✅ Interface CLI interativa

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/ElaineMBarros/Blocks_Apontamento_Teste.git
cd Blocks_Apontamento_Teste
```

2. (Opcional) Crie um ambiente virtual:
```bash
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Uso

### Interface CLI

Execute a aplicação interativa:
```bash
python3 cli.py
```

Menu disponível:
1. Adicionar novo apontamento
2. Completar apontamento
3. Listar apontamentos
4. Gerar relatório de análise
5. Salvar dados
6. Sair

### Uso Programático

```python
from datetime import datetime, timedelta
from time_tracker import TimeTracker, TimeAnalyzer

# Criar tracker
tracker = TimeTracker()

# Adicionar apontamentos
start = datetime(2025, 11, 1, 9, 0)
end = datetime(2025, 11, 1, 17, 0)
tracker.add_entry("Projeto A", "Desenvolvimento de features", start, end)
tracker.add_entry("Projeto B", "Code review", start, start + timedelta(hours=2))

# Calcular horas totais
total_hours = tracker.total_hours()
print(f"Total: {total_hours}h")

# Calcular horas por projeto
hours_by_project = tracker.total_hours_by_project()
for project, hours in hours_by_project.items():
    print(f"{project}: {hours}h")

# Gerar relatório
report = TimeAnalyzer.generate_report(tracker)
print(report)

# Salvar dados
tracker.save_to_file("apontamentos.json")
```

## Testes

Execute os testes unitários:
```bash
pytest test_time_tracker.py -v
```

Com cobertura de código:
```bash
pytest test_time_tracker.py -v --cov=time_tracker --cov-report=html
```

## Estrutura do Projeto

```
Blocks_Apontamento_Teste/
├── README.md                 # Documentação
├── requirements.txt          # Dependências Python
├── .gitignore               # Arquivos ignorados pelo Git
├── time_tracker.py          # Classes principais (TimeEntry, TimeTracker, TimeAnalyzer)
├── cli.py                   # Interface CLI
├── test_time_tracker.py     # Testes unitários
└── apontamentos.json        # Dados persistidos (gerado automaticamente)
```

## Modelo de Dados

### TimeEntry
Representa um apontamento individual com:
- `id`: Identificador único
- `project`: Nome do projeto
- `description`: Descrição da atividade
- `start_time`: Data/hora de início
- `end_time`: Data/hora de término (opcional)

### TimeTracker
Gerencia coleção de apontamentos com métodos para:
- Adicionar e buscar apontamentos
- Filtrar por projeto
- Calcular horas totais e por projeto
- Persistir e carregar dados

### TimeAnalyzer
Gera relatórios de análise com:
- Total de horas e apontamentos
- Distribuição de horas por projeto
- Detalhes de cada apontamento

## Exemplos de Relatório

```
============================================================
RELATÓRIO DE ANÁLISE DE APONTAMENTOS
============================================================

Total de Horas: 10.00h
Total de Apontamentos: 2

Horas por Projeto:
------------------------------------------------------------
  Projeto A: 8.00h (80.0%)
  Projeto B: 2.00h (20.0%)

Detalhes dos Apontamentos:
------------------------------------------------------------
  ID: 1 | Projeto: Projeto A
    Descrição: Desenvolvimento de features
    Início: 2025-11-01 09:00
    Fim: 2025-11-01 17:00
    Duração: 8.00h | Status: Completo

  ID: 2 | Projeto: Projeto B
    Descrição: Code review
    Início: 2025-11-01 09:00
    Fim: 2025-11-01 11:00
    Duração: 2.00h | Status: Completo

============================================================
```

## Licença

Este é um projeto de teste para demonstração de funcionalidades.
