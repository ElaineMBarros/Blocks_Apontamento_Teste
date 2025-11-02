# 📊 Sistema de Análise de Apontamentos ML

Sistema completo de análise de apontamentos de trabalho com Machine Learning, dashboards interativos e integração com equipes.

## 🎯 Funcionalidades

### 📈 Dashboard V2 (Principal)
- **6 Tabs Completas:**
  - 🚨 Alertas (apontamentos fora do padrão)
  - 📊 Análise Detalhada (por funcionário e dia)
  - 👤 Por Pessoa (análise individual com status 🟢🟡🔴)
  - 📈 Gráficos (interativos com Plotly)
  - 📋 Dados Brutos (exportação CSV)
  - 🤖 Chat IA (integração OpenAI)

### 🔍 Filtros Avançados
- 📅 Período customizável
- 👤 Por validador
- 👨‍💼 Por funcionário
- ⏱️ Faixas de análise (4h/6h/8h)

### 🤖 Inteligência Artificial
- Chat contextualizado com dados filtrados
- Perguntas sugeridas
- Análise automatizada
- Detecção de padrões

## 🚀 Deploy Rápido

### Opção 1: Streamlit Cloud (Gratuito)
```bash
# 1. Criar repositório no GitHub
# 2. Subir arquivos
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/SEU-USUARIO/analise-apontamentos-ml.git
git push -u origin main

# 3. Deploy no Streamlit Cloud
# Acesse: https://streamlit.io/cloud
# Conecte seu repositório
# Deploy automático!
```

### Opção 2: Local
```bash
# Instalar dependências
pip install -r requirements_streamlit.txt

# Rodar dashboard V2
streamlit run app_dashboard_v2.py
```

📖 **Guia Completo:** Veja `DEPLOY_STREAMLIT_CLOUD.md`

## 📦 Arquivos Principais

```
analise_apontamentos_ml/
├── app_dashboard_v2.py          # Dashboard principal (USAR ESTE)
├── app_streamlit.py             # Dashboard V1 (legado)
├── analise_duracao_trabalho.py  # Processamento de dados
├── requirements_streamlit.txt   # Dependências
├── DEPLOY_STREAMLIT_CLOUD.md    # Guia de publicação
├── .streamlit/
│   └── config.toml              # Configurações do Streamlit
└── resultados/                  # Dados processados
    └── dados_com_duracao_*.csv
```

## 🛠️ Tecnologias

- **Frontend:** Streamlit
- **Visualização:** Plotly, Matplotlib
- **Análise:** Pandas, NumPy
- **IA:** OpenAI GPT-3.5
- **Deploy:** Streamlit Cloud

## 📊 Screenshots

### Dashboard Principal
![Dashboard](https://via.placeholder.com/800x400?text=Dashboard+V2)

### Análise Por Pessoa
![Por Pessoa](https://via.placeholder.com/800x400?text=Analise+Por+Pessoa)

### Chat IA
![Chat IA](https://via.placeholder.com/800x400?text=Chat+IA+Integrado)

## 🎯 Casos de Uso

### 1. Gestores
- Monitorar performance da equipe
- Identificar sobrecargas
- Tomar decisões baseadas em dados

### 2. RH
- Acompanhar jornadas de trabalho
- Detectar irregularidades
- Gerar relatórios

### 3. Funcionários
- Autoavaliação
- Comparar com metas
- Identificar oportunidades de melhoria

## 📝 Como Usar

### 1. Processar Dados
```bash
python analise_duracao_trabalho.py
```

### 2. Visualizar Dashboard
```bash
streamlit run app_dashboard_v2.py
```

### 3. Acessar
```
http://localhost:8502
```

## 🔐 Configuração OpenAI (Opcional)

Para usar o Chat IA:

1. Obter API Key: https://platform.openai.com/api-keys
2. No dashboard, colar a key no campo
3. Começar a fazer perguntas!

**Custo:** ~$0.001 por pergunta

## 📊 Status do Projeto

- ✅ Dashboard V2 completo
- ✅ Sistema de filtros avançados
- ✅ Análise por pessoa com status
- ✅ Chat IA integrado
- ✅ Pronto para produção
- ✅ Documentação completa

## 🤝 Contribuindo

```bash
# 1. Fork o projeto
# 2. Criar branch
git checkout -b feature/nova-funcionalidade

# 3. Commit
git commit -m "Add: nova funcionalidade"

# 4. Push
git push origin feature/nova-funcionalidade

# 5. Pull Request
```

## 📄 Licença

MIT License - veja LICENSE para detalhes

## 👥 Autores

- Desenvolvido com IA assistente
- Análise de dados empresariais

## 📞 Suporte

- 📖 Documentação: Veja arquivos `*.md`
- 🐛 Issues: Use GitHub Issues
- 💬 Discussões: GitHub Discussions

## 🎉 Agradecimentos

- Streamlit pela plataforma incrível
- OpenAI pela API
- Comunidade Python

---

**⭐ Se este projeto foi útil, considere dar uma estrela!**

**� Deploy agora:** Siga `DEPLOY_STREAMLIT_CLOUD.md`
