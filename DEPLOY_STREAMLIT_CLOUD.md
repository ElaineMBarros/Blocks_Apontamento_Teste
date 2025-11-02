# 🚀 GUIA DE PUBLICAÇÃO - Streamlit Cloud

## 📋 Pré-requisitos

- ✅ Conta GitHub (gratuita)
- ✅ Conta Streamlit Cloud (gratuita)
- ✅ Dashboard funcionando localmente

---

## 🎯 OPÇÃO 1: Deploy Streamlit Cloud (Recomendado)

### Vantagens:
- ✅ **Totalmente gratuito**
- ✅ Deploy automático a cada commit
- ✅ HTTPS gratuito
- ✅ URL personalizada (ex: seu-app.streamlit.app)
- ✅ Fácil de configurar

---

## 📝 Passo a Passo

### 1️⃣ Preparar Repositório GitHub

#### 1.1 Criar repositório no GitHub
```bash
# Ir para: https://github.com/new
# Nome: analise-apontamentos-ml
# Público ou Privado (ambos funcionam)
# Criar repositório
```

#### 1.2 Subir arquivos para GitHub
```bash
# No terminal, na pasta do projeto:
cd c:/Users/elain/Desktop/analise_apontamentos_ml

# Inicializar Git (se ainda não fez)
git init

# Adicionar arquivos
git add app_dashboard_v2.py
git add requirements_streamlit.txt
git add .streamlit/config.toml
git add resultados/dados_com_duracao_*.csv

# Commit
git commit -m "Dashboard V2 completo para deploy"

# Conectar ao GitHub (substituir SEU-USUARIO)
git remote add origin https://github.com/SEU-USUARIO/analise-apontamentos-ml.git

# Subir para GitHub
git branch -M main
git push -u origin main
```

### 2️⃣ Configurar Streamlit Cloud

#### 2.1 Criar conta
```
1. Ir para: https://streamlit.io/cloud
2. Clicar em "Sign up"
3. Conectar com GitHub
4. Autorizar Streamlit
```

#### 2.2 Criar novo app
```
1. Clicar em "New app"
2. Selecionar seu repositório: analise-apontamentos-ml
3. Branch: main
4. Main file path: app_dashboard_v2.py
5. Clicar em "Deploy!"
```

#### 2.3 Configurar Secrets (Opcional - para OpenAI)
```
1. No dashboard do app, clicar em "Settings"
2. Ir em "Secrets"
3. Adicionar:
   OPENAI_API_KEY = "sua-key-aqui"
4. Save
```

### 3️⃣ Aguardar Deploy

```
⏳ Aguarde 2-5 minutos
✅ App estará disponível em: https://seu-app.streamlit.app
```

---

## 🔒 OPÇÃO 2: Deploy com Autenticação

Se quiser adicionar login/senha:

### 2.1 Criar arquivo secrets.toml
```toml
# .streamlit/secrets.toml
[passwords]
# usuario = "senha"
"admin" = "senha123"
"usuario1" = "senha456"
```

### 2.2 Adicionar autenticação ao app
```python
# No início do app_dashboard_v2.py
import streamlit as st

def check_password():
    """Returns `True` if user has correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets["passwords"]:
            if st.session_state["password"] == st.secrets["passwords"][st.session_state["username"]]:
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # Don't store password
            else:
                st.session_state["password_correct"] = False
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show inputs + error
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 User not known or password incorrect")
        return False
    else:
        # Password correct
        return True

if not check_password():
    st.stop()

# Resto do código do dashboard...
```

---

## 🎯 OPÇÃO 3: Deploy em Servidor Próprio

### 3.1 Deploy em VPS (DigitalOcean, AWS, Azure)

```bash
# 1. Conectar ao servidor via SSH
ssh usuario@seu-servidor.com

# 2. Instalar dependências
sudo apt update
sudo apt install python3-pip python3-venv nginx

# 3. Clonar repositório
git clone https://github.com/seu-usuario/analise-apontamentos-ml.git
cd analise-apontamentos-ml

# 4. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 5. Instalar dependências
pip install -r requirements_streamlit.txt

# 6. Rodar com screen (mantém rodando)
screen -S streamlit
streamlit run app_dashboard_v2.py --server.port=8501 --server.address=0.0.0.0

# Ctrl+A+D para sair do screen (deixa rodando)
```

### 3.2 Configurar Nginx como proxy reverso

```nginx
# /etc/nginx/sites-available/streamlit
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
# Ativar configuração
sudo ln -s /etc/nginx/sites-available/streamlit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 📊 URLs Após Deploy

### Streamlit Cloud (Gratuito):
```
https://seu-app.streamlit.app
ou
https://analise-apontamentos.streamlit.app
```

### Servidor Próprio:
```
http://seu-dominio.com
ou
http://seu-ip:8501
```

---

## 🔧 Troubleshooting

### Erro: "requirements.txt não encontrado"
```bash
# Certifique-se que o arquivo existe:
ls requirements_streamlit.txt

# Se não existir, criar:
streamlit --version # para ver versão
echo "streamlit==1.28.0" > requirements_streamlit.txt
echo "pandas==2.1.0" >> requirements_streamlit.txt
echo "plotly==5.17.0" >> requirements_streamlit.txt
echo "openai==1.3.0" >> requirements_streamlit.txt
```

### Erro: "Arquivo dados não encontrado"
```bash
# Opção 1: Subir arquivo CSV
git add resultados/dados_com_duracao_*.csv
git commit -m "Add data file"
git push

# Opção 2: Conectar a banco de dados
# Modificar data_connector.py para usar DB
```

### Erro: "Module not found"
```bash
# Adicionar ao requirements_streamlit.txt:
echo "nome-do-modulo==versao" >> requirements_streamlit.txt
git add requirements_streamlit.txt
git commit -m "Add missing dependency"
git push
```

---

## ✅ Checklist de Deploy

```
Antes de publicar:
[ ] Git repositório criado e configurado
[ ] requirements_streamlit.txt atualizado
[ ] .streamlit/config.toml configurado
[ ] Dados CSV incluídos ou DB configurado
[ ] App testado localmente
[ ] Conta Streamlit Cloud criada
[ ] Repositório conectado ao Streamlit
[ ] App deployado com sucesso
[ ] URL funcionando
[ ] Secrets configurados (se usar OpenAI)
[ ] Compartilhar URL com usuários
```

---

## 🎉 Seu Dashboard Está no Ar!

**URL:** https://seu-app.streamlit.app

**Compartilhe com sua equipe!** 🚀

---

## 📱 Acesso Mobile

O dashboard é **totalmente responsivo** e funciona em:
- 📱 Smartphones
- 📱 Tablets  
- 💻 Desktops
- 🖥️ Monitores grandes

---

## 🔄 Atualizações Automáticas

Qualquer mudança no código:
```bash
git add .
git commit -m "Atualização do dashboard"
git push
```

**O Streamlit Cloud atualiza automaticamente em ~2 minutos!**

---

## 💰 Custos

### Streamlit Cloud (Gratuito):
- ✅ 1 app privado
- ✅ 3 apps públicos
- ✅ 1GB recursos compartilhados
- ✅ Deploy ilimitados

### Streamlit Cloud (Pago - $20/mês):
- ✅ Apps ilimitados privados
- ✅ 16GB RAM dedicados
- ✅ Suporte prioritário
- ✅ Mais recursos

---

## 📞 Suporte

- 📚 Docs: https://docs.streamlit.io/streamlit-community-cloud
- 💬 Forum: https://discuss.streamlit.io
- 🐛 GitHub: https://github.com/streamlit/streamlit

---

🎉 **Boa sorte com seu deploy!**
