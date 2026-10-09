# S04-T02 — Prova técnica do Tank Royale

**Data:** 09/10/2026 · **Resultado técnico:** PASS · **Estado macro:** EM_REVISAO.  
**Execução:** ChatGPT Pro e GitHub Actions; sem uso de Codex ou R4 nesta tarefa.

## 1. Pergunta e conclusão

**Pergunta:** conseguimos iniciar programaticamente o motor oficial, executar dois robôs de referência, obter pontuação verdadeira e conservar replay sem depender de interface gráfica nem acessar os dados do computador hospedeiro?

**Conclusão:** sim, no ambiente GitHub-hosted testado. Duas batalhas Classic, com cinco rounds cada, terminaram e tiveram resultado, replay e configuração efetiva conferidos. A reprodução do novo spike no Windows do responsável é um aceite separado, ainda pendente. Isso não é validação de segurança de código arbitrário nem entrega do MVP.

## 2. Implementação entregue

| Parte | Decisão implementada |
|---|---|
| Motor | Tank Royale 1.4.0; release e commit upstream fixados |
| Controle | Battle Runner JVM oficial com servidor embutido; wrapper Java chama `startBattleAsync` e `awaitResults` |
| Robôs | Pacote Java oficial: diretórios Walls e SpinBot; identidades Walls v1.0 e Spin Bot v1.0 |
| Partida | Classic, arena 800 × 600, cinco rounds; execução sem limitação visual de FPS |
| Integração local | Um comando Python constrói e executa a imagem; não exige Java/Maven no Windows |
| Evidências | `results.json`, replay `.battle.gz`, log e manifesto por execução |
| Reprodutibilidade de dependências | Artefatos validados por tamanho/SHA-256; imagens base fixadas por digest |

A escolha de amostras Java serve para testar o motor. **Não escolhe a linguagem de autoria dos estudantes** e não exige conhecimento prévio de desenvolvimento web/mobile. A interface móvel continua objeto da S04-T03.

## 3. Resultados efetivamente observados

Lote de referência: [GitHub Actions 38004097096](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38004097096). Fonte do código: `cf7d6b5a98d12b8f42f40214b495aad9357010fd`; checkout testado do PR: `b3900380501a4a861f196d80ee484949de1dfbba`. O checkout de merge do CI não significa merge do PR na main.

| Batalha | Rounds | Walls | Spin Bot | Primeiro lugar nos rounds | Ticks | Duração observada |
|---|---:|---:|---:|---|---:|---:|
| 1 | 5 | **495** | 229 | Walls 4; Spin Bot 1 | 4.899 | 11,391 s |
| 2 | 5 | **465** | 141 | Walls 4; Spin Bot 1 | 4.921 | 11,481 s |

Pontos copiados de `BattleResults`, não calculados por uma simulação própria. Os tempos incluem inicialização/encerramento do runner e excluem construção da imagem; duas partidas não constituem benchmark de capacidade do futuro servidor. Não há seed fixada, e o teste não exige que placares ou vencedor sejam idênticos.

O replay 1 tem 448.209 bytes comprimidos; o replay 2, 471.139. Após baixar o artifact, foram verificadas a integridade gzip, cada linha JSON, cinco eventos de fim de round por batalha, os ticks e o evento final. **Todos os campos de resultado exportados coincidiram com o evento `GameEndedEventForObserver` do respectivo replay.**

Evidência estruturada: [TANK-ROYALE-CI.json](../qualidade/evidencias/TANK-ROYALE-CI.json). O artifact bruto do run tem ID `11650431842`, SHA-256 `28cabec21a4cfad1fc53fb9cf8ca10bc7fe0bf670f412f9c95a2e6c7b8692823` e retenção informada até 08/11/2026. Cópia também foi entregue na conversa. Os resultados deste relatório são o lote fixo acima; regressões posteriores geram novos placares, sem reescrever esta evidência histórica.

## 4. Verificações executadas

| Verificação | Resultado |
|---|---|
| Regressão de planejamento/inventário | 27 testes OK |
| Contratos da infraestrutura/preflight | 13 testes OK |
| Contratos do spike, hashes, ZIP e transporte | 23 testes OK |
| Total unitário | **63 testes OK; zero falhas** |
| Backlog canônico/projeções | 10 sprints, 60 tarefas, sem divergência de geração no run |
| Pré-requisitos nativos do Spec Kit — feature 002 | PASS |
| Batalhas com motor real | 2 execuções PASS, 10 rounds concluídos |
| Política Docker efetiva | 11 verificações PASS em cada execução |
| Limpeza restrita ao contêiner do experimento | Confirmada nas duas execuções |

Fixtures unitárias são dados sintéticos explicitamente identificados. Não foram usadas como substituto dos resultados reais. A conferência semântica dos replays descrita acima foi feita adicionalmente sobre o artifact baixado; o executor automatiza integridade gzip/tamanho/hash e o contrato dos resultados.

## 5. Fronteira de execução

O contêiner roda com rede `none`, sem portas publicadas, sem mounts/binds do host, sem socket Docker e sem acesso à senha/banco da plataforma. UID 10001, raiz read-only, tmpfs limitado, remoção de capabilities, no-new-privileges, limite de 2 CPUs, 2 GiB e 256 PIDs. A configuração foi lida com `docker inspect`, não apenas presumida a partir de um Dockerfile.

Downloads ocorrem **na construção da imagem**; a batalha roda sem rede externa. O motor e os bots usam comunicação local dentro do mesmo contêiner. O controlador Python usa a CLI Docker no host para criar, iniciar e remover somente o contêiner aleatório da sua invocação. Compose, PostgreSQL, `.env`, firewall e outros projetos não são modificados.

Essas restrições não demonstram resistência a código hostil. Os bots são oficiais/conhecidos e compartilham o ambiente com o motor. Testes de abuso, fuga, isolamento entre alunos e gestão de segredos continuam na S04-T04. Timeouts foram configurados; não foi executado um ensaio deliberado de esgotamento de tempo nesta tarefa.

## 6. Problemas encontrados e corrigidos

**Identidade do bot:** a pasta SpinBot declara `name: Spin Bot`. A primeira construção foi corretamente bloqueada por um contrato excessivamente restritivo. O lock passou a registrar separadamente diretório e identidade declarada, preservando o upstream.

**Transferência do replay:** uma batalha inicial concluiu os cinco rounds, mas o `docker cp` após encerramento não conseguiu recuperar dados de tmpfs. O pipeline foi considerado FAILED, não aceito parcialmente. A correção exporta os bytes por stdout antes do término, decodifica somente nomes permitidos e conserva log/manifesto. Assim não foi necessário montar diretórios do computador pessoal.

## 7. Decisão e próximos aceites

O experimento sustenta utilizar o Battle Runner oficial como candidato para a integração do motor. Não é preciso escrever outro simulador para demonstrar uma batalha. A integração de produção ainda exige contratos com fila, versões imutáveis, tratamento de falhas e persistência dos resultados.

A tarefa macro S04-T02 fica **EM_REVISAO**: execução técnica confirmada e documentação entregue, com ratificação da arquitetura e reprodução no host pendentes. Nenhuma dependência S03/S04-T01 foi marcada concluída artificialmente. Próximo experimento funcional do plano: autoria pelo celular; próximo controle de segurança: isolamento para código não confiável.

## 8. Fontes técnicas primárias

- [Release oficial 1.4.0](https://github.com/robocode-dev/tank-royale/releases/tag/v1.4.0)
- [API Battle Runner](https://robocode.dev/api/battle-runner.html)
- [Exemplo Java versionado](https://github.com/robocode-dev/tank-royale/blob/v1.4.0/runner/examples/RunBattle.java)
- [Contrato BattleResults versionado](https://github.com/robocode-dev/tank-royale/blob/v1.4.0/runner/src/main/kotlin/dev/robocode/tankroyale/runner/BattleResults.kt)
- [Metadados Walls](https://github.com/robocode-dev/tank-royale/blob/v1.4.0/sample-bots/java/Walls/Walls.json) e [Spin Bot](https://github.com/robocode-dev/tank-royale/blob/v1.4.0/sample-bots/java/SpinBot/SpinBot.json)
- [Licença upstream](https://github.com/robocode-dev/tank-royale/blob/v1.4.0/LICENSE)

[Instruções de reprodução no Windows](../../spikes/tank-royale/README.md) · [Tarefas Spec Kit](../../specs/002-tank-royale/tasks.md)
