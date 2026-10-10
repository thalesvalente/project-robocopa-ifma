# ADR-005 — MVP com persistência remota e execução em VMs locais

**Data:** 2026-10-10 · **Estado:** direção arquitetural escolhida pelo responsável; implementação, operação e autorização de produção PENDENTES.
**Substitui, apenas no escopo alvo do MVP:** hipótese de armazenar os dados definitivos no PostgreSQL do computador pessoal na ADR-003.
**Preserva:** laboratório Compose/PostgreSQL local como experimento/teste, sem migração automática ou remoção de dados.
**Rastreabilidade:** [D-006](../planejamento/decisoes/D-006-hospedagem-hibrida-e-persistencia-remota.md), [Spec Kit feature 001 — evolução híbrida](../../specs/001-hosting-local/hybrid-mvp.md), ADR-001/003/004; S04-T01/S04-T05/S08; I3-03..I3-07, I4 e I5.

## Decisão do responsável e motivação

A RoboCopa IFMA utilizará **Vercel como frontend responsivo/PWA, Supabase PostgreSQL como banco canônico, Supabase Auth para identidades e Supabase Storage privado para replays e objetos**. O computador do responsável poderá hospedar VMs Linux dedicadas **exclusivamente para processamento e execução isolada de partidas** durante o MVP. Não concentrar dados permanentes de estudantes, inscrições, versões, fila, resultados e arquivos de replay no PC pessoal.

Esta aprovação é uma direção de produto, NÃO autoriza instalar VMs, expor serviços, abrir portas, registrar estudantes ou ativar execução de código não confiável. G-EXP continua separado de G-PROD; a constituição, S03/S04 e homologação devem ser cumpridas.

## Visão das fronteiras

    Estudante/Professor navegador (PWA Vercel)
                |
             HTTPS/Auth
                v
       API de domínio curta (hospedagem a definir por componente)
                |
        +-------+------------------------+
        |                                |
  Supabase Auth + Postgres        Supabase Storage privado
  identidade, projetos,           replays/artefatos verificados
  versões, jobs, leases,          URLs temporárias e limites
  resultados e classificação
        ^
        | apenas serviço autorizado / transações condicionais
        v
  Broker de execução na nuvem (deploy e identidade a validar)
        ^
        | conexão de saída iniciada pela VM; canal autenticado
        | sem acesso direto do navegador ao árbitro/worker
        v
  PC pessoal -> VM Linux separada -> worker -> sandbox de cada bot
                                        -> árbitro Tank Royale

**Acesso doméstico:** o navegador não conecta ao IP residencial do operador. Worker faz chamadas de saída ao plano de controle; não expor Docker remoto, porta de VM, PostgreSQL ou túnel público por inferência. O experimento I3-02 demonstrou apenas mTLS em loopback CI; o modo de término TLS/autorização na infraestrutura cloud precisará ser testado antes de produção. Vercel Functions não constitui processo confiável sempre ativo nem hospedagem automática do árbitro; suporte WebSocket não torna suas instâncias persistentes.

## Estado e persistência dos dados

| Categoria | Registro canônico | Local de cálculo/armazenamento temporário |
|---|---|---|
| Identidade, consentimentos, papéis | Supabase Auth/Postgres sob políticas RLS | VM não recebe PII nem service-role |
| Código-fonte RoboDSL/versão imutável e hashes | PostgreSQL, com controle de autorização por dono | Apenas cópia de job autorizada e limitada durante execução |
| Jobs, idempotência, leases e tentativas | PostgreSQL remoto, transações/fencing | Cache de execução somente enquanto necessário |
| Resultado, score e histórico de competição | PostgreSQL, efetivado apenas após validação e commit idempotente | Dados de cálculo/validação temporários |
| Replay e artefatos maiores | Supabase Storage, buckets privados + metadados/hash no PostgreSQL | Upload temporário; spool de retry opcional, limitado, protegido e eliminado após confirmação |
| Imagem do sistema VM, motor/Java e configuração | Discos da VM local sob isolamento e backup do sistema conforme I4 | Persistência operacional local inevitável, sem banco definitivo do evento |

**Regra de verdade:** nenhum placar pode ser considerado publicado apenas porque o worker produziu um arquivo. O plano de controle somente marca resultado terminal após validação e confirmação transacional da persistência remota. A conexão perdida gera estado PENDENTE/LEASE EXPIRADO para recuperação, sem duplicar pontuação nem confundir execução concluída com resultado persistido. O projeto deve testar a janela crash-antes/depois-commit e a expiração de lease com fencing token.

A VM pode precisar de spool **temporário, cifrado ou minimizado**, com tamanho/TTL e limpeza controlados, para reenviar artefatos após perda de rede. Não prometer zero escrita em disco do PC: SO/VM, swap autorizado e arquivos temporários geram escrita. Minimizar e destruir cópias após confirmação remota, sem montar pastas pessoais no guest.

## Conectividade e disponibilidade

- PC/VM desligados: estudantes continuam podendo visualizar e editar projetos persistidos remotamente; novos treinos ficam enfileirados ou recebem status indisponível até o worker voltar. Não prometer partidas em tempo real sem host conectado.
- Falha de internet/energia: nenhum fallback para Docker Desktop pessoal; leases expiram e jobs são reprocessados somente sob política de tentativas e fencing. Replays só passam a definitivos após confirmação de upload e registro.
- Plano de controle cloud deve validar a identidade/escopo do worker, aplicar quotas, revogação, idempotência, resultado do árbitro e autorização de usuário sem repassar credencial administrativa ou connection string ao ambiente de bot.
- Backup: Supabase como serviço gerenciado NÃO dispensa cópia independente de banco e objetos, restore testado, política de retenção e controle de acesso. A política precisa cumprir LGPD e contexto educacional, especialmente quando houver menores.

## Escolhas técnicas e limites ainda abertos

1. **PostgreSQL = banco definitivo**. O SQLite do I3-01 é apenas fixture de transações e teste; não será fonte de verdade de produção nem segunda fila operacional. I3-03 deve planejar e testar um adaptador PostgreSQL/SQL de claim/leases/fencing no CI, sem tocar no banco pessoal ou em projeto real de Supabase.
2. **Front Vercel**: React/TypeScript/PWA. Operações curtas de domínio podem usar API serverless; o desenho do broker de serviço e mTLS exige validação separada de compatibilidade e credenciais. Nenhum segredo administrativo no navegador.
3. **Supabase PostgreSQL**: RLS obrigatória nas tabelas expostas; permissões mínimas, nenhum segredo service-role no cliente ou VM de bot; considerar pooler adequado ao runtime. Uma API serverless usa em geral o pooler em transaction mode, sem prepared statements nesse modo.
4. **Supabase Storage**: buckets privados por padrão, signed URLs curtas emitidas somente por serviço confiável, limites/tipos, metadados e hash validados. Sem exposição universal de replay/código do aluno sem regra específica.
5. **VM local**: hypervisor, disco de VM independente, rede, switches, segmentação, credenciais, disponibilidade, logs e plano de recuperação exigem I4; não configurar o Windows ou Docker Desktop nesta decisão.
6. **Planos gratuitos e preferência de hospedagem (D-008)**: **Vercel é a primeira opção para a PWA estática** por decisão do responsável, **sob confirmação do enquadramento contratual Hobby**; Cloudflare Pages é alternativa portável. Gratuidade, ausência de fins lucrativos ou vínculo com instituição pública não equivalem, isoladamente, a autorização da Vercel. Verificar se a produção/desenvolvimento remunerado se enquadra nas Fair Use Guidelines, colaboração/deploy e quotas, obter resposta escrita do fornecedor para o uso institucional quando necessário e registrar fallback antes da publicação oficial. Permanecem as verificações de pausa/quota Supabase Free, disponibilidade e custos.

## Critérios para implementar e considerar segura a migração ao alvo

- [ ] Contratos de dados/versionamento, RLS, papéis e rotas especificados antes de code-first e validados por testes negativos.
- [ ] PostgreSQL de CI isolado comprova reserva transacional de jobs, SKIP LOCKED quando apropriado, leases, fencing, retries e concorrência, sem dupla publicação; não importar automaticamente fila SQLite experimental.
- [ ] Auth e sessão com autorização por objeto: usuário A não lê/escreve versões, resultados privados ou artefatos de B; backend não aceita owner_ref autodeclarado.
- [ ] Broker remoto e worker outbound demonstrados com credenciais escopadas, revogação e transporte compatíveis com o deploy escolhido; sem endpoint doméstico público.
- [ ] Storage privado com upload/replay íntegros, limites, URLs expirando e recuperação após falha; apagar staging temporário e rejeitar score não confirmado.
- [ ] Desligar a VM durante jobs: fila ainda íntegra remotamente, novos jobs não processados, recuperação/timeout sem perda ou placar duplicado após religar.
- [ ] Backup e restauração independentes testados, política de retenção/custos documentada e gate pedagógico/institucional aprovado.
- [ ] VM dedicada e controles de isolamento efetivo aprovados; nenhum bot de estudante antes dos gates I3/I4/I5/G-PROD.

## Fontes oficiais consultadas em 2026-10-10

- Supabase — conexões/poolers: https://supabase.com/docs/guides/database/connecting-to-postgres
- Supabase — RLS/keys: https://supabase.com/docs/guides/database/postgres/row-level-security
- Supabase — Storage privado/signed URLs: https://supabase.com/docs/guides/storage/buckets/fundamentals
- Supabase — quotas Storage Free: https://supabase.com/docs/guides/storage/pricing
- Supabase — pausa por inatividade: https://supabase.com/docs/guides/platform/free-project-pausing
- Vercel — Hobby: https://vercel.com/docs/plans/hobby
- Vercel — WebSocket beta: https://vercel.com/changelog/websocket-support-is-now-in-public-beta

**Não há implantação Supabase/Vercel/VM nesta ADR.** Trata-se da decisão aprovada quanto à direção da arquitetura do MVP e dos critérios verificáveis necessários para executá-la.


## Adendo de precedência — D-008 / Vercel Hobby (2026-10-10)

**Decisão atual:** preservar Vercel como **preferência técnica e de experiência de desenvolvimento para o frontend React/TypeScript/PWA**, incluindo preparação de builds/testes, e **não substituí-la automaticamente por Cloudflare Pages**. Se o fornecedor confirmar que o caso educacional/institucional é elegível ao Hobby, poderá ser adotada como hospedagem oficial dentro dos limites documentados. Cloudflare Pages permanece opção de contingência se a confirmação for negativa, insuficiente ou as condições/limites inviabilizarem o evento. A arquitetura deve produzir frontend estático portável, sem dependência obrigatória de funções proprietárias Vercel.

**Interpretação contratual revisada:** a seção 4 dos [Terms of Service](https://vercel.com/legal/terms) diz *personal or non-commercial use*; as [Fair Use Guidelines](https://vercel.com/docs/limits/fair-use-guidelines#commercial-usage) também restringem o Hobby a projetos pessoais não comerciais e definem uso comercial a partir de ganho financeiro por participantes da produção, citando funcionários pagos/consultores. Resposta de [Vercel Staff no fórum oficial](https://community.vercel.com/t/question-about-commercial-usage/23321/4) aceita um projeto **voluntário e não remunerado** desenvolvido para organização sem fins lucrativos. **Isso não é dispensa genérica para qualquer atividade de servidor público/instituição.** A elegibilidade dependerá da natureza concreta da participação remunerada e dos termos aplicáveis à conta/deploy.

**Critério de publicação:** esclarecer o enquadramento se houver desenvolvimento ou manutenção como atribuição remunerada/institucional. Registrar resposta oficial documentada ou avaliação institucional fundamentada antes de usar o Hobby como **hospedagem oficial para estudantes**; se não houver elegibilidade, trocar **somente o frontend** para provedor permitido, sem alterar Supabase nem worker/VM. Enquanto isso, não declarar o Hobby institucionalmente aprovado nem contratar plano Pro sem aprovação específica.

**Restrições que não mudam:** nenhum endpoint de estudante, worker/árbitro, socket Docker, chave Supabase privilegiada ou dado pessoal é hospedado/despachado pela PWA. Limites do Hobby, retenção de deployments, disponibilidade e colaboração devem ser monitorados. D-008 modifica a prioridade de hospedagem de D-007/ADR-006, **não** a decisão D-006 de banco/VM, nem libera G-PROD.

Fontes: [Hobby](https://vercel.com/docs/plans/hobby), [Terms](https://vercel.com/legal/terms), [Fair Use](https://vercel.com/docs/limits/fair-use-guidelines), [Community Vercel Staff](https://community.vercel.com/t/question-about-commercial-usage/23321/4), [colaboração](https://vercel.com/docs/deployments/troubleshoot-project-collaboration).

**Privacidade adicional do plano Hobby:** os [Terms §3](https://vercel.com/legal/terms) permitem à Vercel usar conteúdo de contas Hobby para treinamento de modelos, com **opt-out nas configurações da equipe**. Antes de inserir quaisquer conteúdos sensíveis ou usar o deploy institucionalmente, revisar a configuração e documentar a opção; o frontend estático não deve conter códigos privados, informações de estudantes, credenciais Supabase ou variáveis secretas embutidas. D-008/HYB-09 contemplam essa verificação.
