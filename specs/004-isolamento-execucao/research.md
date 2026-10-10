# Research — opções de isolamento e evidência técnica

**Data de consulta:** 2026-10-09. **Natureza:** referências externas complementam fontes do projeto; alternativas não estão instaladas nem validadas no host.  
**Escopo:** selecionar abordagem para provas controladas S04-T04, sem tocar nos contêineres pessoais.

## Evidência disponível no projeto (não extrapolar)

- O executor de referência de S04-T02 e o protótipo de autoria S04-T03 usam Docker `--network none`, usuário `10001`, rootfs somente leitura, `cap-drop ALL`, `no-new-privileges`, quotas e tmpfs. Foram verificadas onze propriedades **daqueles contêineres**.
- O servidor HTTP de desenvolvimento em `127.0.0.1:18081` invoca uma função Python que, no host, chama a CLI Docker. **Não é plano de controle seguro para público**.
- Testes reproduziram movimentos reais de robôs e replays, não ataques de isolamento.
- Docker Desktop em Windows/WSL 2 hospeda projetos pessoais no mesmo computador; falta localização do VHDX, backup/restauração e segmentação forte do executor.

## Comparação das alternativas

| Alternativa | Benefício | Limite principal | Veredito para S04-T04 |
|---|---|---|---|
| A. Endurecer contêineres no daemon Docker Desktop atual | Simples, reaproveita pipeline e recursos | Mesma infraestrutura de controle e computador pessoal; ataque ao kernel/daemon afeta outros projetos; processo host possui acesso à CLI | **Não candidata isolada para código de alunos** |
| B. **VM Linux dedicada + daemon de execução próprio**, sem acesso a drives pessoais | Fronteira adicional entre código de alunos e host; fácil suspender, restaurar snapshot e inspecionar | Hipervisor e configuração devem ser avaliados; separação de rede/bot/árbitro precisa de prova | **Candidata preferida para experimento, não aprovada** |
| C. Executor em máquina remota isolada (nuvem ou hardware dedicado) | Limita impacto físico sobre máquina pessoal; fronteira independente | Custos, rede, disponibilidade, credenciais e operação adicionais | **Alternativa se B falhar** |
| D. gVisor `runsc` no worker Linux | Kernel de aplicação adiciona camada de contenção de syscalls | Dependência de runtime/compatibilidade/overhead; não existe garantia automática | **Camada defensiva experimental** |
| E. Rootless Docker ou userns-remap | Reduz privilégios do daemon/IDs mapeados conforme modo | Não resolve sozinho rede, vazamento de dados, falhas do executor, gestão de resultados | **Avaliar complementarmente dentro da fronteira B/C** |
| F. Apenas interpreter/DSL sem runtime de bots | Menor expressividade, superfície de execução potencialmente reduzida | Exige adaptação do motor e revisão formal das regras; não é o pipeline atual | **Alternativa futura, não presumida** |

## Observações de segurança

1. A documentação oficial Docker diferencia **rootless mode** (daemon e contêineres sem root) e **userns-remap** (daemon ainda privilegiado). São mitigadores, não substitutos de separação de fronteiras. [Docker rootless](https://docs.docker.com/engine/security/rootless/) · [Docker userns-remap](https://docs.docker.com/engine/security/userns-remap/).
2. O socket/daemon Docker tem alto privilégio. Não disponibilizar API Docker a serviços de estudante; acesso administrativo exige controles próprios. [Proteção do Docker daemon](https://docs.docker.com/engine/security/protect-access/).
3. Controles como AppArmor/seccomp exigem verificação do **perfil efetivo e do kernel alvo**; restrições declaradas não garantem aplicação. [Docker AppArmor](https://docs.docker.com/engine/security/apparmor/) · [Segurança Docker](https://docs.docker.com/engine/security/).
4. O `runsc` do gVisor é OCI-compatible e intermedeia syscalls por um kernel de aplicação, mas precisa avaliação de compatibilidade e não substitui política de rede e quotas. [gVisor Architecture](https://gvisor.dev/docs/architecture_guide/intro/) · [gVisor Security Model](https://gvisor.dev/docs/architecture_guide/security/).
5. O motor Tank Royale usa API de comunicação com servidor; **a topologia com bot/árbitro em ambientes distintos continua objeto do spike**, não deve ser assumida funcional. [Tank Royale](https://robocode.dev/articles/tank-royale.html) · [Battle Runner](https://robocode.dev/api/battle-runner.html).

## Decisão candidata de pesquisa

**Priorizar B**, mantendo C como saída caso não exista isolamento demonstrável/administrável na máquina doméstica. Dentro da VM, testar camadas de defesa e canal estreito com o árbitro. Um protótipo com **somente RoboDSL restrita** é preferível ao de código Java livre, mas ainda exige análise de abuso de parser, código gerado e runtime.

## Lacunas de prova

- VM dedicada ainda não existe nem foi inventariada.
- Não há medição de recursos (CPU/memória/disco e capacidade concorrente) em VM própria.
- Nenhuma tentativa controlada de negação de acesso à rede do host ou drives pessoais foi executada.
- Ainda não sabemos se é possível colocar processo bot e processo árbitro em boundaries separados mantendo Battle Runner 1.4.0 e replay confiável.
- Não há auditoria independente de segurança nem avaliação da retenção de dados de alunos.

**Conclusão limitada:** há estratégia de teste justificável, não conclusão de segurança. Não implementar acesso público antes da resolução das lacunas.
