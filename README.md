# Alarme de Agenda

Alarme insistente para eventos do Google Agenda no Windows: pop-up modal com beep contínuo que só para ao confirmar manualmente.

Feito para eventos críticos que a notificação padrão do Google Agenda deixa passar em branco.

## Como funciona

- Consulta a Google Calendar API a cada 2 minutos (configurável).
- Ao detectar um evento próximo, abre uma janela modal e dispara um beep em loop.
- O alarme só para quando o usuário clica em **OK, vi!**.
- Dois disparos por evento: cinco minutos antes e no horário exato (configurável).
- Estado persistido em `alerted.json` para não repetir alertas.

## Pré-requisitos

- Windows
- Python 3.10+
- Conta Google com Calendar habilitado

## Setup

### 1. Dependências

```bash
pip install -r requirements.txt
```

### 2. Credenciais OAuth

1. Em [console.cloud.google.com](https://console.cloud.google.com), crie um projeto.
2. Em **APIs e serviços → Biblioteca**, ative a **Google Calendar API**.
3. Em **Tela de permissão OAuth**, configure o app (Interno para Workspace, Externo para conta pessoal).
4. Em **Credenciais → Criar credenciais → ID do cliente OAuth**, escolha o tipo **App para computador**.
5. Baixe o JSON e salve como `credentials.json` na raiz do projeto.

Formato em `credentials.json.example`.

### 3. Primeira execução

```bash
python alarme.py
```

Um navegador abre para autorização. Após aprovar, `token.json` é gerado e reutilizado nas execuções seguintes.

## Configuração

Edite `config.json`:

| Campo | Descrição | Default |
|---|---|---|
| `calendarId` | ID da agenda (`"primary"` para a principal) | `"primary"` |
| `alertMinutesBefore` | Antecedências para disparar o alarme | `[5, 0]` |
| `pollIntervalSeconds` | Intervalo de consulta à API | `120` |
| `beepFrequency` | Frequência do beep em Hz | `880` |
| `beepDurationMs` | Duração de cada beep em ms | `400` |
| `beepIntervalMs` | Intervalo entre beeps em ms | `1500` |

## Executando em background

Use `iniciar_oculto.vbs` — roda via `pythonw.exe`, sem janela de console.

Para iniciar com o Windows, coloque um atalho do `.vbs` em `shell:startup`.

Para debug, use `iniciar.bat` — abre console visível.

## Estrutura

```
alarme.py                 Script principal
config.json               Configuração
credentials.json          Credenciais OAuth (não versionado)
credentials.json.example  Template das credenciais
token.json                Token OAuth gerado no primeiro login (não versionado)
alerted.json              Estado de alertas disparados (não versionado)
alarme.log                Log da execução (não versionado)
iniciar.bat               Runner com console
iniciar_oculto.vbs        Runner sem console
requirements.txt          Dependências Python
```
