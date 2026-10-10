# ADR-001 — Stack candidata para o MVP RoboCopa IFMA

**Data:** 2026-10-09 · **Estado:** proposta técnica, não ratificada.  
**Relacionamento:** S04-T01; pré-requisitos formais S03-T06 ainda pendentes.

## Contexto e forças

O estudante deve **aprender, programar a lógica de um robô, salvar, testar e competir pelo celular**, sem precisar saber desenvolver um site ou aplicativo. Um único computador físico hospedará o piloto. Código submetido por participantes é não confiável. O projeto precisa ser compreensível, reversível, auditável e econômico em operação. A plataforma RoboCopa não se confunde com o motor Robocode Tank Royale.

## Comparação de opções

| Dimensão | Opção A | Opção B | Direção candidata |
|---|---|---|---|
| Interface | React + TypeScript como PWA responsiva | Aplicativos Android/iOS separados | **A**, uma base acessível em navegador, com editor amigável no celular |
| API de domínio | Node.js/TypeScript, API modular | Python/FastAPI | **Node/TypeScript**, reuso de tipos e integração com a interface; decisão revisável |
| Dados | PostgreSQL relacional | SQLite | **PostgreSQL**, transações para submissões, versões e resultados |
| Fila durável inicial | Tabela de jobs PostgreSQL com reivindicação transacional e `SKIP LOCKED` | Redis + broker separado | **PostgreSQL inicialmente**, menos serviços para um host e concorrência piloto reduzida |
| Motor | Adaptador próprio para Tank Royale (servidor/battle runner) | Motor criado internamente | **Adaptador**, a validar em spike real S04-T02 |
| Executor de bots | Ambiente segregado por job com revisão, limites e canais mínimos | Execução no mesmo processo da API | **Segregação obrigatória**, mecanismo exato definido após spike de segurança S04-T04 |

A direção candidata não fixa ainda uma linguagem de programação dos **robôs**: essa decisão exige validação de autoria móvel (S04-T03). Não pressupor que TypeScript no backend implica programar robôs nessa linguagem.

## Decisão provisória

A plataforma ficará organizada em módulos de **identidade/perfis**, **projetos/versões de robôs**, **treino**, **inscrições**, **partidas**, **classificação**, **auditoria** e **administração**. Uma API modular separa a interface dos serviços de dados e execução. A UI PWA é cliente de APIs, não executor de código de alunos.

O primeiro Compose é intencionalmente menor: **PostgreSQL 17** e **sonda HTTP isolada**. Não contém UI, API real, worker, motor, lógica de competição ou sandbox. É uma **prova de infraestrutura**, não um MVP funcional.

## Restrições de segurança

- Acesso ao host via `127.0.0.1` por padrão; acesso remoto é decisão posterior.
- Somente a sonda expõe porta local; PostgreSQL não publica portas.
- Contêiner que receba código não confiável **não** poderá ter socket Docker, credenciais do banco, acesso à rede do host ou montagem do diretório pessoal.
- O uso de contêineres **não constitui, por si, sandbox suficiente para código hostil**. A definição e os testes são gate antes de qualquer submissão pública.
- Credenciais do Compose local não serão commits; o arquivo `.env` contém senha de teste gerada localmente. Política de secrets de produção será definida na S08.

## Alternativas e gatilhos de revisão

Se as medições mostrarem filas longas, alta taxa de treino ou necessidade de escala distribuída, revisar o mecanismo de jobs e considerar Redis ou outro broker. Caso o framework ou a linguagem escolhidos dificultem a autoria pelo celular, priorizar a finalidade pedagógica e rever a stack.

## Referências técnicas

- Tank Royale — arquitetura baseada em WebSocket: https://robocode.dev/articles/tank-royale.html
- API e battle runner: https://robocode.dev/api/apis.html
- Docker — práticas de isolamento e execução dos bots: https://robocode.dev/articles/booter.html
- Imagem oficial PostgreSQL e montagem para PG 17: https://hub.docker.com/_/postgres

## Evidência e aprovação

O arquivo não comprova battle runner integrado, desempenho, segurança contra código não confiável ou validação pedagógica. Essas questões exigem testes e aceites próprios antes da baseline de arquitetura.

## Decisão posterior para o MVP — persistência remota (2026-10-10)

A escolha candidata **PostgreSQL** foi confirmada pelo responsável; para o MVP, o banco canônico ficará **no Supabase**, com Supabase Auth/Storage, PWA na **Vercel** e execução Tank Royale em **VMs Linux dedicadas no PC do responsável**. SQLite do I3-01 permanece fixture experimental, **não** segundo banco de produção. Local Compose/Postgres permanece laboratório/teste histórico. Esquema/RLS/auth, adaptador PostgreSQL da fila I3-03, replay remoto e broker de conexão outbound ainda exigem plano/testes/aceite antes de implantação. O backend Node/TypeScript continua candidato e a localização exata do broker com mTLS requer verificação de compatibilidade do provider. [ADR-005](ADR-005-hospedagem-hibrida-mvp.md), [D-006](../planejamento/decisoes/D-006-hospedagem-hibrida-e-persistencia-remota.md).
