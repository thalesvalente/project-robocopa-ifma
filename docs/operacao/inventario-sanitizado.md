# Inventário sanitizado e estado de preparação da hospedagem

**Data das coletas:** 2026-10-09 · **Origem:** inventário local fornecido pelo responsável (v1, v2 e v3), seguido de testes Docker no PowerShell.  
**Classificação:** inventário parcialmente confirmado; prontidão de hospedagem externa **não comprovada**.

## Ambiente técnico confirmado

- Windows 11 Pro, arquitetura x86-64, CPU multicore e memória abundante para um laboratório inicial.
- Docker Desktop com engine Linux 28.1.1, Compose 2.35.1 e WSL 2 operacionais.
- Distribuições `docker-desktop` e `Ubuntu` em WSL 2, presentes e em execução no inventário.
- O comando `docker run --rm hello-world` foi executado pelo responsável e concluiu com sucesso.
- Docker Engine e Compose responderam a consultas em PowerShell e o daemon estava acessível no inventário v3.
- Já existem imagens, contêineres e volumes de outros projetos no host. **Não limpar nem migrar automaticamente**.
- Há um volume de trabalho com espaço disponível reduzido; planejar banco/logs considerando unidade de maior capacidade após avaliar disco virtual do Docker Desktop.

## Dados deliberadamente não publicados

Identificadores da máquina, IPs, MACs, hostname, nome de usuário, SSID, caminho completo do usuário, portas específicas em uso, nome dos contêineres existentes, conteúdo do banco e senhas **não** são versionados. JSONs locais `.local/inventory*.json` são ignorados pelo Git.

## Itens pendentes

| Item | Estado |
|---|---|
| Máquina compatível com Docker e WSL 2 | Confirmado por saídas fornecidas |
| Contêiner de referência executado | Confirmado pelo responsável |
| Deploy real deste Compose na máquina | Pendente |
| Local físico do disco virtual do Docker Desktop | Pendente |
| Teste de backup/restauração externo | Pendente |
| Upload, CGNAT e estabilidade da conexão | Pendente |
| Monitoramento de suspensão, energia e retomada | Pendente |
| Segurança de execução de código de estudantes | Pendente |
| Homologação de infraestrutura exposta à internet | Pendente |

## Próximo passo

Consultar `docs/operacao/COMPOSE-LOCAL.md`, executar os comandos voluntariamente na máquina e retornar **somente os resultados não sensíveis** de saúde e status. Nenhum comando deve abrir porta no roteador nem alterar firewall.
