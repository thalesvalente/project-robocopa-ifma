# Estado atual — baseline pós-revisão e núcleo PostgreSQL

**Atualizado:** 2026-10-10. **Ramo desta visão:** `feat/s04-i3-03-postgres-leases`, PR #26. **Macro S04-T04:** EM_EXECUCAO. **G-PROD:** BLOQUEADO. **Demonstração completa à diretoria:** ainda depende da jornada integrada/ensaio.

Este arquivo consolida o estado vigente. A cronologia detalhada, placares e limites dos lotes anteriores permanecem nos relatórios vinculados e no histórico Git; não reinterpretar evidência de laboratório como implantação.

## Decisões vigentes e finalidade

Somente RoboDSL básica no MVP; linguagens gerais, níveis intermediário/avançado e transmissão contínua ficam depois. Primeiro marco é demonstração privada com identidades sintéticas e estratégias verificadas; piloto de estudantes exige outros gates.

[D-006](decisoes/D-006-hospedagem-hibrida-e-persistencia-remota.md)/[ADR-005](../arquitetura/ADR-005-hospedagem-hibrida-mvp.md): dados canônicos no Supabase PostgreSQL, Auth e Storage privado; PC apenas hospeda VMs Linux segregadas para computação/staging limitado. SQLite I3-01 é teste, não banco final.

[D-007](decisoes/D-007-execucao-pos-revisao-mvp.md)/[ADR-006](../arquitetura/ADR-006-demo-gratuita-plano-controle.md), **retificadas pela [D-008](decisoes/D-008-revisao-hobby-vercel-ifma.md)**: Vercel como primeira opção CONDICIONAL à elegibilidade Hobby, Cloudflare Pages como fallback; API cloud curta candidata em Supabase Edge Functions, sem batalha/worker permanente; status/replay antes de streaming. pgmq foi avaliado; núcleo inicial usa uma tabela de jobs/tentativas PostgreSQL com reserva transacional, sem fila paralela. Isso exige ledger separado de efeitos únicos em I3-04.

## Repositório e rastreabilidade

A main verificada nesta rodada é `64863ec2d5a66da4dd024ec660bcb68c929341c0`: inclui os PRs #11/#12/#13/#14/#16/#17/#19, documentação #22 e arquitetura híbrida #25. #18/#20/#21 estão fechados sem merge. [Trilha de integração](INTEGRACAO-PRs-2026-10-10.md).

PRs #23 (I3-01), #24 (I3-02) e #26 (núcleo PostgreSQL) permanecem em rascunho. #26 contém a ancestralidade de #24 e da main reconciliada, sem force-push, sem alterar os PRs anteriores ou integrar código novo à main. O fechamento dos recortes não equivale ao merge dos PRs.

Spec Kit v1.1.2 continua fixado em `959e866caa3618bf3dc290d5dca33394365af9c6`. Backlog JSON é canônico (10 sprints/60 tarefas). Os 39 itens amplos T001–T039 e 18 gates continuam sujeitos a seus aceites; S00-T06, baseline S03 e homologação arquitetural não foram ratificados automaticamente. Minutas S01/S02 não são pesquisa de campo nem aprovação institucional.

## Entregas experimentais e evidências

| Recorte | Estado demonstrado | Fonte detalhada |
|---|---|---|
| Infraestrutura local Compose | CI e execução inicial no PC informada pelo responsável; somente banco/sonda privados | [INFRA-LOCAL-HOST](../qualidade/evidencias/INFRA-LOCAL-HOST.md) |
| Tank Royale/editor/RoboDSL | Batalhas CI e reproduções no PC; telefone físico e revisão pedagógica pendentes; empate/rank na issue #15 | [TANK-ROYALE-HOST](../qualidade/evidencias/TANK-ROYALE-HOST.md), [AUTORIA-MOBILE-HOST](../qualidade/evidencias/AUTORIA-MOBILE-HOST.md) |
| I1 | Contratos/quotas/9 sondas CI, sem VM pessoal | [I1](../qualidade/evidencias/S04-T04-I1.md) |
| I2 | Batalhas separadas, gateway, auditoria, abortos/timeout/cleanup; reconciliação encerrada no recorte | [I2 reconciliação](../qualidade/evidencias/S04-T04-I2-RECONCILIACAO.md) |
| I3-01 | SQLite e broker interno OFF por padrão, somente laboratório | [I3-01](../qualidade/evidencias/S04-T04-I3-01.md) |
| I3-02 | mTLS real de probe em loopback CI; não autenticação cloud operacional | [I3-02](../qualidade/evidencias/S04-T04-I3-02.md) |
| I3-03 / PG-01..06 | PostgreSQL 17.11 real: jobs, leases/fencing, cancelamento/retry/reap, privilégios e restart | [I3-03 núcleo](../qualidade/evidencias/S04-T04-I3-03.md) |

Núcleo PostgreSQL na fonte `0b97ee6`: **30 testes reais PASS**, cleanup confirmado, **382 regressões** reproduzidas na sessão e seis workflows no mesmo SHA aprovados, incluindo arena I2 real. ZIPs PostgreSQL/fonte/I2 conferidos fora do runner com hashes, CRC, source/run e semântica. F01 (prontidão), F02 (reap) e C02 (erro de cleanup) corrigidos com plano anterior ao patch. Conferência própria não é revisão independente. Não houve execução PostgreSQL local nesta sessão; os testes de banco rodaram no CI.

## Próximos gates — não encerrados

[I3-03](../../specs/004-isolamento-execucao/i3-03-postgres-plan.md) **integral continua EM_EXECUCAO**: ligar admissão/identidade à API cloud, testar permissões/migration no Supabase e transporte outbound do worker. NÃO expor `rc_broker` ao navegador/VM, NÃO reutilizar LabGate/probe como autenticação de produção.

I3-04: resultado/replay validado e commit único do placar. I3-05/06/07: quotas/polling econômico, recuperação ampliada e integração. I4: provisionar e provar a VM real com autorização específica. I5: 20 ciclos, backup de banco/objetos, restauração, revisão e ensaio go/no-go. [Plano híbrido HYB-01..10](../../specs/001-hosting-local/hybrid-mvp.md) continua com aceites próprios. Auth/SMTP/RLS por estudante, consentimentos/retencão, disponibilidade e custos também precisam de validação.

## Restrições operacionais

Nenhum deploy Supabase/Cloudflare/Vercel, serviço pago contratado, VM instalada, dados reais ou alunos liberados nesta rodada. Não houve alteração de Windows/WSL/Docker Desktop/.env/Compose/banco/roteador/firewall/discos pessoais. O laboratório 18081 ainda tem acesso à CLI Docker do host e não deve ser exposto à internet/LAN. Nenhum teste do CI homologa esse servidor como API pública.

## D-008 — revisão contratual da preferência de frontend (2026-10-10)

A preferência **Cloudflare primeiro** foi superada: **Vercel primeiro, sujeita ao enquadramento Hobby**; Cloudflare como alternativa. Fonte: Terms §4, Fair Use, manifestação contextual da equipe Vercel sobre voluntariado em organização sem fins lucrativos e regras de colaboração. Gratuidade do IFMA/RoboCopa não é certificação suficiente; remunerados envolvidos na produção precisam ser considerados. HYB-09 e G-PROD não foram encerrados. A PWA deve continuar um build estático portátil, com conteúdo sensível no Supabase e revisão/opt-out de treinamento em conta Hobby quando aplicável. [D-008](decisoes/D-008-revisao-hobby-vercel-ifma.md). A alteração NÃO muda o aceite PostgreSQL experimental do PR #26 ou libera deploy.
