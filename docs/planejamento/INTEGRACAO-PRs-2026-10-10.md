# Plano controlado de integração dos PRs de fundação e segurança — 2026-10-10

**Solicitação:** integrar o trabalho técnico até o I2, antes do I3. **Estado inicial:** PLANEJADO, não pressupõe merge ou homologação. **Base:** main `1cbc58a3a8c7c958c35b071332fbb8a5f0a5a1ae`. **Escopo:** PRs #11, #12, #13, #14, #16, #17 e #19. #18/#20/#21 estão encerrados sem merge por alternativas superadas.

## Estratégia

- [ ] INT-01 Congelar inventário de PRs, relação base→head e SHAs; conferir permissões, código, arquivos sensíveis, avaliações e conclusões de workflows. Não instalar VM nem publicar serviços.
- [ ] INT-02 Usar **merge commits** (não squash/rebase/force) para preservar ancestralidade; integrar primeiro #11 em `main`.
- [ ] INT-03 Para cada próximo PR, mudar **somente a base do PR para `main`** após integrar seu antecessor, confirmar novo diff incremental, integridade da árvore e checks, marcar draft como ready (administrativo, não homologação do produto) e realizar merge com `expected_head_sha` congelado. Parar diante de conflito, head mudado, check falho ou alteração inesperada.
- [ ] INT-04 Verificar PRs #11/#12/#13/#14/#16/#17/#19 com `merged=true`, `merged_at` e SHAs de merge; confirmar #18/#20/#21 continuam fechados sem merge, nenhuma outra PR aberta e que `main` contém as fontes/evidências I1/I2.
- [ ] INT-05 Executar regressões na fonte consolidada, Spec Kit/backlog/verificadores e, quando possível, CI das batalhas reais em PR de validação de integração. Não converter artefatos sintéticos em provas de produção.
- [ ] INT-06 Documentar os SHAs de merges, checks efetivos e eventuais limitações em `docs/qualidade/evidencias/INTEGRACAO-PRs-2026-10-10.md`; atualizar estado canônico sem marcar S00-T06, S04-T04, I3, I4 ou I5 concluídos indevidamente.

## Critérios de aceite

Os sete PRs previstos ficam `merged` em `main` e os três alternativos continuam fechados sem merge; conteúdo crítico do I1 e I2 presente na `main`; verificadores sem falhas, proveniência registrada. Se o CI de integração em branch separado produzir novo PR, só encerrar após validar. G-EXP permanece experimental e G-PROD BLOQUEADO, sem contas/alunos, API pública, VM pessoal, alterações de host ou nova linguagem. Histórico/branches não serão apagados. O estado `FECHADO_NO_ESCOPO_EXPERIMENTAL` de I1 e I2 não representa aprovação para executar bots de estudantes.

## Rastreamento inicial de branches

| PR | Base original | Head SHA congelado |
|---|---|---|
| #11 | main | `b64a034d3151bb3c32a91e4c11639a8ce3256463` |
| #12 | chore/s00-fundacao-speckit | `97c31de5b8e3ea1c07f946bb2b0859ac9394d013` |
| #13 | feat/infra-local-compose | `0f2fb81731be49d5e3c20eb59e77642811d4042e` |
| #14 | feat/s04-tank-royale-spike | `bf727b4fa12de919c514c31f429decbf0ea37627` |
| #16 | feat/s04-mobile-authoring | `af6e0a08c1e51069c7ee8ec4c03168f0351c170d` |
| #17 | docs/s04-t04-isolamento-speckit | `668d82b034cf5e0fab909e13552399c2de7213d5` |
| #19 | feat/s04-isolation-validation | `5f07d306662ef9abe81f558f81ea0c11ed499e1e` |

Verificar novamente os SHAs no ato de cada merge; essa tabela é uma fotografia da decisão, não permissão para ignorar alterações concorrentes.
