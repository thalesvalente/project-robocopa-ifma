# D-005 — VM dedicada e autorização do primeiro incremento de segurança

**Data:** 2026-10-10. **Origem:** o responsável concordou com a VM Linux dedicada e solicitou pesquisa web, planejamento Spec Kit e início das implementações/testes.

## Decisões e alcance

**D1 — escopo:** RoboDSL básica no MVP. Recursos intermediários, blocos e linguagens gerais continuam pós-MVP. Esta decisão não habilita Java/JS livre nem amplia o compilador.

**D2 — fronteira:** VM Linux dedicada, com daemon e disco próprios, sem compartilhamento de drives pessoais ou do Docker dos outros projetos, foi aprovada como **direção preferencial**. Não significa instalação ou isolamento já testado no Windows.

**G-EXP — autorização de engenharia:** pesquisa, revisão do plano, implementação de módulos delimitados e provas sintéticas pequenas em GitHub-hosted Ubuntu descartável estão autorizadas nesta rodada. Isso permite produzir os controles e as evidências necessários à avaliação. Não é necessário ter segurança já comprovada para escrever seus testes; seria uma dependência circular.

**G-PROD — liberação:** continua BLOQUEADA. Alunos, rede externa, VM no host, broker autenticado, árbitro separado, backup e recuperação exigem implementação/evidências/aceites próprios. D3 e D4 têm hipóteses técnicas a testar; D5 não foi aprovado como liberação pública.

## Limites operacionais

Não houve autorização implícita para instalar Hyper-V/VM, editar WSL/Docker Desktop, mover VHDX, abrir portas, alterar firewall/roteador ou publicar o laboratório 18081. Não será usado runner self-hosted. As provas executam apenas código sintético conhecido, com quotas pequenas e cleanup; não são exploits de kernel, varreduras da LAN ou programas recebidos de alunos.

## Planejamento canônico e progresso

O catálogo de 39 tarefas T001–T039 da feature 004 continua válido. Como várias tarefas contêm objetivos de produção, seu checkbox só encerra ao cumprir todo o aceite. O incremento I1-01..I1-08 registra subconjuntos com evidência em `specs/004-isolamento-execucao/iteration-1.md`. S04-T04 pode passar a EM_EXECUCAO sem encerrar S03/S04 nem homologar segurança.

O PR pode publicar projeções do backlog geradas deterministicamente **na própria branch de trabalho**, depois do CI e sem force-push. Nenhuma outra tarefa macro, segredo, estado de produção ou arquivo operacional do host deve ser alterado por essa reconciliação.

## Fontes e revisão

Pesquisa oficial: `docs/arquitetura/pesquisa-isolamento-2026-10-10.md`. A referência principal do desenho continua ADR-004; atualizações deste registro resolvem a autorização de início experimental, não todos os riscos da ADR. A constituição e a baseline S03 não são ratificadas automaticamente.
