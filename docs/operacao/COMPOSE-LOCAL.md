# Como executar o laboratório de infraestrutura local (Windows 11)

**Escopo:** PostgreSQL e sonda de saúde, somente `localhost`. **Não é o MVP**: ainda não há UI, API de domínio, Tank Royale, autenticação de alunos ou sandbox de bots.

## 1. Preparar — sem alterar seus outros contêineres

Abra **PowerShell** na pasta clonada do projeto:

```powershell
cd H:\projetos\project-robocopa-ifma
git fetch origin
git switch feat/infra-local-compose
git pull --ff-only
```

Não execute estes comandos dentro da pasta de outro projeto.

## 2. Gerar credencial local sem publicá-la

```powershell
python scripts/init_local_env.py
```

O script cria **somente se não existir** um `.env` na raiz do projeto, com senha aleatória para o banco. Se já houver `.env`, ele **não sobrescreve**; nesse caso revise a configuração existente. O arquivo `.env` é ignorado pelo Git.

**Não cole `docker compose config` sem `--quiet` nesta conversa:** essa saída pode mostrar a senha do banco.

## 3. Validar a configuração (nenhum contêiner criado)

```powershell
docker compose -f compose.local.yaml config --quiet
python scripts/validate_local_compose.py
python scripts/preflight_local.py
```

O validador verifica o contrato de isolamento. O **preflight**, sem mudanças no host, detecta o projeto Compose já existente, a ocupação da porta local, acesso ao daemon e espaço básico na unidade do repositório. Ele **não identifica a unidade onde está o VHDX do Docker**. Se alguma verificação informar BLOCKED, não execute o próximo passo antes de revisar.

## 4. Iniciar — somente quando desejar executar o laboratório

```powershell
docker compose -f compose.local.yaml up -d --wait
```

O Docker poderá baixar imagens oficiais `postgres:17-alpine` e `node:24-alpine`. O primeiro início cria um volume vazio próprio. Os serviços não reiniciarão automaticamente após a máquina ser reiniciada (`restart: "no"`).

## 5. Validar a execução

```powershell
docker compose -f compose.local.yaml ps
Invoke-RestMethod http://127.0.0.1:18080/health
docker compose -f compose.local.yaml exec -T database pg_isready -U robocopa -d robocopa
```

Resposta esperada na sonda: `status: ok`, `service: robocopa-ifma-infra-probe`. Isso prova que a sonda respondeu, não que o sistema de competição esteja pronto.

Se houver erro de porta ocupada, mude `ROBOCOPA_HOST_PORT` no `.env` para outra porta livre acima de 1024 e use essa porta na URL. A porta 5432 **não** precisa estar livre no Windows: o Postgres do laboratório não a publica.

## 6. Consultar e parar sem apagar dados

```powershell
docker compose -f compose.local.yaml logs --tail 60
docker compose -f compose.local.yaml down
```

`down` para somente os serviços do projeto. **Não use `down -v`**, que apagaria o volume persistente desta infraestrutura. **Não use `docker system prune`**, pois pode atingir outros projetos.

O Docker mantém os volumes no local do disco virtual gerenciado pelo Desktop; a pasta do Git e o caminho Linux `/var/lib/docker` não garantem que os dados estejam na unidade H: ou G:.

## 7. O que permanece pendente

- Localizar a **Disk image location** no Docker Desktop em `Settings → Resources → Advanced`, verificar espaço e decidir eventual mudança de armazenamento com backup.
- Medir upload/CGNAT e definir acesso remoto com TLS, autorização e autenticação; **não abrir portas agora**.
- Definir backup independente e testar restauração.
- Realizar spikes de Tank Royale, editor de programação no celular e isolamento de código não confiável.
- Validar execução local no computador do responsável; testes no CI são evidência de outro ambiente.

**Inspeção importante:** o arquivo Compose possui o projeto nomeado `robocopa-ifma-local`. O preflight **bloqueia** se encontrar um projeto existente com esse nome. Depois da primeira inicialização, não rode o preflight como condição obrigatória para reiniciar o mesmo projeto: inspecione o Compose existente e opere-o conscientemente. Não faça `up` em um projeto desconhecido com o mesmo nome.
