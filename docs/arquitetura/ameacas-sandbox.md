# Modelo de ameaças — RoboCopa IFMA / S04-T04

**Versão:** 0.1 (proposta) · **Estado:** análise documental; **nenhum teste de ataque executado**.  
**Fontes internas:** constituição III/V/VI/VII, ADR-001/002/003, features 002/003, issues #5 e #15.  
**Método:** STRIDE + inventário de ativos/fronteiras; a gravidade é avaliação preliminar, sujeita à revisão humana. Não há dados reais de alunos nestes documentos.

## Ativos protegidos

A1 — computador pessoal, credenciais e contas do responsável; A2 — outros projetos, seus containers/volumes/VHDX; A3 — banco e metadados da RoboCopa; A4 — dados/estratégias de outros estudantes; A5 — motor/árbitro e integridade do placar; A6 — rede doméstica e serviços LAN; A7 — disponibilidade de CPU/RAM/disco/conexão; A8 — logs/replays e cadeia de evidência.

## Atores e confiança

- Participante autenticado (ou sua sessão comprometida): pode submeter comandos válidos/invalidos, não administrar infraestrutura.
- Atacante externo: pode explorar endpoint público **somente quando existir**, executar requisições repetidas e tentar acionar fluxos privilegiados.
- Código do robô gerado a partir da DSL: considerado **não confiável**, ainda que compilado por template.
- Operador/CI: tem permissões de implementação/revisão; não deve colocar segredo em logs ou conceder privilégios desnecessários.
- Dependência/imagem do motor comprometida: ameaça à cadeia de fornecimento, distinta da entrada do aluno.

## Fronteiras de confiança

```text
[TB1] navegador/estudante -- HTTP --> [API de aplicação (futura)]
[TB2] API -- contrato tipado --> [fila, broker e supervisor confiáveis]
[TB3] supervisor -- canal restrito/autenticado --> [worker em VM Linux dedicada]
[TB4] worker -- job imutável --> [sandbox efêmero por submissão]
[TB5] bot -- canal mínimo de jogo --> [árbitro Tank Royale separado]
[TB6] árbitro/worker -- resultado e replay validados --> [persistência no plano de controle]
```

**Observação:** TB2–TB6 ainda são desenho candidato; não aparecem na aplicação atual. Hoje o servidor local chama a Docker CLI **no host** (risco prioritário a remover antes de publicação).

## Inventário STRIDE e provas esperadas

| ID | Ameaça | Categoria | Ativo | Severidade preliminar | Controle pretendido | Evidência de teste exigida |
|---|---|---|---|---|---|---|
| TH-01 | Endpoint HTTP público aciona Docker do host | E/T | A1/A2 | CRÍTICA | FR-003/004/020; broker segregado e flags fail-closed | TB1→TB3 negada sem permissão; nenhum job no host |
| TH-02 | Escape do contêiner ou daemon compartilhado | E | A1/A2 | CRÍTICA | FR-005/007/018; VM dedicada, sem socket | Sondas negativas **somente** na VM isolada; fronteira verificada |
| TH-03 | Código malicioso usa filesystem/binds/symlink | I/T | A1/A2/A4 | CRÍTICA | FR-005/007/018 | Tentativas sintéticas negadas; nenhum arquivo pessoal presente no ambiente |
| TH-04 | Exfiltração à internet, LAN ou metadata | I | A1/A3/A4/A6 | ALTA | FR-006/018 | Tráfego negado em policy efetiva, exceções do árbitro comprovadas |
| TH-05 | Acesso ao banco/segredos/tokens por subprocessos | I/E | A1/A3 | CRÍTICA | FR-003/004/007/014 | Segredos ausentes do ambiente e saída; endpoint inacessível |
| TH-06 | Falha de parser/template gera execução não permitida | T/E | A1/A5 | ALTA | FR-001/002/015/018 | Negativos de AST, limites e injeção sem criação de job |
| TH-07 | CPU/RAM/PIDs/disco exauridos, fork e stdout ilimitado | D | A2/A7 | ALTA | FR-008/009/017 | Quotas medidas com cargas sintéticas controladas e teto configurado |
| TH-08 | Job travado ou órfão após timeout/cancelamento | D | A7/A8 | ALTA | FR-009/010/016 | Recovery determinístico e inspeção de zero órfãos |
| TH-09 | Um aluno acessa código/replay/estado de outro | I/S | A4 | ALTA | FR-003/005/011/014 | Jobs de identidades sintéticas isolados; autorização negativa |
| TH-10 | Replay ou resultado adulterado altera ranking | T/R | A5/A8 | ALTA | FR-011/012/013 | Fixtures com hash/rounds divergentes rejeitados |
| TH-11 | Retry duplica pontuação, eventos ou contabilização | T/R | A5 | ALTA | FR-010/011/013 | Testes de concorrência e deduplicação |
| TH-12 | Logs e artefatos vazam identidade e segredos | I/R | A1/A4/A8 | ALTA | FR-014/015 | Varredura de valores sentinela e esquema sanitizado |
| TH-13 | Dependência/imagem oficial adulterada ou atualizada | T | A5/A8 | ALTA | FR-015/018 | Verificação digest/versão antes de uso, sem downloads durante job |
| TH-14 | Worker falha e sistema volta automaticamente para host | E/D | A1/A2 | CRÍTICA | FR-016/019/020 | Provar fail-closed sem fallback e sem alterar Compose alheio |
| TH-15 | Bot interfere no árbitro/placar no mesmo ambiente | T/E | A5 | CRÍTICA | FR-005/006/012 | Spike de isolamento bot↔árbitro; integridade do replay verificável |
| TH-16 | Requisições concorrentes contornam limite de filas | D/T | A7 | ALTA | FR-008/013/017 | Saturação com cargas sintéticas, admissão e quotas observadas |

Legenda STRIDE: **S** spoofing, **T** tampering, **R** repudiation, **I** information disclosure, **D** denial of service, **E** elevation of privilege.

## Política de testes e exclusões

1. Primeira etapa: fixtures/offline estáticos e revisão dos contratos; não há exploits rodando nesta documentação.
2. Ensaios de recursos, chamadas de rede/arquivo e falhas deliberadas **apenas** em runner GitHub efêmero ou VM descartável e separada, sem acesso a IP real, LAN pessoal, banco ou volumes do responsável.
3. Registrar contexto (kernel/runtime), política pretendida versus **efetiva** (`inspect`/runtime), cenário, estado observado, duração e limpeza. Dados de teste sintéticos apenas.
4. Um teste que simule negação sem observar a política efetiva é **INCONCLUSIVO**. Ausência de fuga no conjunto testado não equivale a prova absoluta.
5. Em produção, exigir avaliação independente das fronteiras, plano de resposta, backups e aceites humanos. O teste de DR, rede pública ou alteração do host não está autorizado pela S04-T04 documental.

## Riscos residuais e decisões em aberto

- **R-01 crítico:** a interface Python hoje tem capacidade de invocar a CLI Docker do host. Não abrir `127.0.0.1:18081` para LAN ou internet.
- **R-02 crítico:** contêiner que hospeda motor+bot compartilha um ambiente; a separação de árbitro e bot deve ser tecnicamente demonstrada.
- **R-03 alto:** VM própria é opção, não solução instalada ou aprovada; privilégios do hipervisor e arquivos compartilhados importam.
- **R-04 alto:** disponibilidade do computador doméstico, falha de energia, disco/backup e rede externa ainda não validados.
- **R-05 alto:** política de retenção/privacidade de menores e papéis administrativos ainda precisa revisão institucional.
- **R-06 alto:** pontuação empatada exibida com ranks diferentes (issue #15) requer regra explícita S03-T03 antes de ranking definitivo.

**Gate:** nenhum código geral de estudantes ou acesso externo é autorizado por este documento. Priorizar D1–D5 em `specs/004-isolamento-execucao/clarifications.md`.

## Adendo de fronteira I3-02 (2026-10-10; planejamento, não evidência)

Diante das ameaças TH-01/TH-05/TH-09/TH-14, o plano [I3-02](../../specs/004-isolamento-execucao/i3-02-auth-plan.md) separa TLS autenticado de mera reivindicação de identidade por payload. A identidade deve ser extraída exclusivamente do certificado do socket autenticado, com CA do laboratório, URI SAN, digest exato, escopo e operação. Acesso a jogos e Docker continua negado. Revogação em memória é prova limitada, sem persistência/revogação de PKI operacional. Não considerar ausência de acesso em loopback como segurança de uma rede pública.
